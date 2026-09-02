"""Job executor — SSH/render/retry/QC orchestration (operator ruling 2).

Planning stays pure: DSPy planner/chain controllers emit plans
(services/chain emit_render_manifest); THIS module executes them.
The queue/preflight/render/QC collaborators are injected — unit
tests stub them; the real run wires host/render_host.SshHost +
host/wangp_adapter.WanGPAdapter (existing seams, not duplicated).

Verify-before-trust (ruling 5): a rendered mp4 is accepted only
after log step-count verification — the log must contain a complete
"N/N" Denoising line. A truncated log fails the clip with the log
tail captured as the failure artifact.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from services.jobs.states import transition
from services.jobs.modes import (
    ModeError, ProductMode,
)

# "20/20" / "8/8" Denoising — complete when the two numbers match
_DENOISE_COMPLETE_RE = re.compile(r"Denoising\s+(\d+)/\1\b")
_LOG_TAIL_CHARS = 800

# ── per-job-kind render-lane dispatch table (PR feat/ref2va-jobs-routing)
# kind -> lane. Semantic product modes (PR #62 amendment): the four
# MODEL modes route by mode; "ref2va_render" stays a valid legacy kind
# for backward compat; unknown/None kinds stay on the fl2va path
# (legacy jobs carry no kind and must render exactly as before).
# CONTINUATION is orchestration, NOT a model mode — it must be
# unwrapped (modes.unwrap_continuation) BEFORE dispatch; it raises
# here instead of silently riding fl2va.
_REF2VA_KINDS = frozenset(
    {"ref2va_render", ProductMode.REF2VA_IDENTITY_AUDIO.value})


def render_lane_for(kind) -> str:
    """Map a job/clip kind (or product mode) to its render lane."""
    if kind == ProductMode.CONTINUATION.value:
        raise ModeError(
            "CONTINUATION is orchestration, not a model mode — unwrap "
            "it to the underlying job + temporal_strategy before "
            "dispatch (services.jobs.modes.unwrap_continuation)")
    return "ref2va" if kind in _REF2VA_KINDS else "fl2va"


@dataclass(frozen=True)
class RenderOutcome:
    mp4: str
    log_text: str
    log_path: str


def verify_render_log(log_text: str) -> bool:
    """Structural acceptance: a complete N/N Denoising line exists."""
    return bool(_DENOISE_COMPLETE_RE.search(log_text or ""))


def _tail(text: str) -> str:
    return (text or "")[-_LOG_TAIL_CHARS:]


class JobExecutor:
    """One trusted 3090; single-job step machine driver.

    run_once(): take the oldest admissible job, drive it one phase.
    Returns the job id handled, or None when there is nothing to do.
    """

    def __init__(self, *, queue, preflight: Callable,
                 render: Callable[[dict], RenderOutcome],
                 qc: Callable[[dict], tuple],
                 ref2va_render: Optional[Callable[[dict], RenderOutcome]] = None,
                 max_failures: int = 3,
                 staleness_s: float = 600.0):
        self.queue = queue
        self.preflight = preflight
        self.render = render
        # ref2va lane renderer (per-job-kind routing); when None the
        # ref2va lane FAILS CLOSED — never silently rendered on fl2va.
        self.ref2va_render = ref2va_render
        self.qc = qc
        self.max_failures = max_failures
        # stale-active heartbeat timeout (reviewer B2): an active-state
        # job whose owner is dead AND heartbeat older than this is
        # requeued. Configurable via WANGP_STALENESS_S.
        env = os.environ.get("WANGP_STALENESS_S")
        self.staleness_s = (float(env) if env else staleness_s)

    # -- helpers ----------------------------------------------------
    def _fail(self, job, failure_class: str, detail: str) -> None:
        jid = job.job_id
        self.queue.record_failure(jid, failure_class=failure_class)
        self.queue.set_failure_detail(jid, detail)
        if self.queue.dead_letter_due(jid, max_failures=self.max_failures):
            state = self.queue.get(jid).state
            if state != "failed":
                self.queue.set_state(jid, "failed")
            self.queue.set_state(jid, "dead_letter")
        else:
            state = self.queue.get(jid).state
            if state not in ("failed", "dead_letter"):
                self.queue.set_state(jid, "failed")

    def _render_clips(self, job) -> None:
        for clip in job.clips:
            if clip.get("status") == "done":
                continue  # checkpoint resume: skip done clips
            lane = render_lane_for(clip.get("kind"))
            render_fn = self.render
            if lane == "ref2va":
                if self.ref2va_render is None:
                    self._fail(
                        job, "ref2va_lane_unavailable",
                        f"clip {clip['clip_index']} is a ref2va_render "
                        "job but no ref2va renderer was wired into the "
                        "executor — refusing to fall back to fl2va")
                    return
                render_fn = self.ref2va_render
            outcome = render_fn(clip)
            # verify-before-trust (ruling 5)
            if not verify_render_log(outcome.log_text):
                self._fail(
                    job, "truncated_render_log",
                    f"[lane={lane}] render log verification failed for "
                    f"clip {clip['clip_index']} (no complete N/N Denoising "
                    f"line); log tail: {_tail(outcome.log_text)!r}; "
                    f"log={outcome.log_path}")
                return
            self.queue.update_clip(
                job.job_id, clip["clip_index"], status="rendered",
                log=outcome.log_path, mp4=outcome.mp4,
                qc_verdict=None, lane=lane)
        self.queue.set_state(job.job_id, "rendered_pending_qc")

    def _qc_clips(self, job) -> None:
        for clip in job.clips:
            if clip.get("status") == "done":
                continue
            try:
                ok, qc_path = self.qc(clip)
            except Exception as e:
                # QC unavailable mid-job: park, do NOT fail
                self.queue.set_state(job.job_id,
                                     "rendered_pending_qc")
                return
            if not ok:
                self._fail(job, "qc_reject",
                           f"QC rejected clip {clip['clip_index']}: "
                           f"verdict={qc_path}")
                return
            self.queue.update_clip(
                job.job_id, clip["clip_index"], status="done",
                log=clip["log"], mp4=clip["mp4"],
                qc_verdict={"verdict": "KEEP", "path": qc_path})
        self.queue.set_state(job.job_id, "done")

    # -- main driver -------------------------------------------------
    def run_once(self) -> Optional[str]:
        job = self._pick_job()
        if job is None:
            return None
        jid = job.job_id
        claim = getattr(self.queue, "claim_active", None)
        if claim:
            claim(jid, owner_pid=os.getpid())

        try:
            return self._drive(job, jid)
        finally:
            # release ownership (job may have moved to a parked/terminal
            # state; the WHERE is harmless either way)
            try:
                self._db_clear_ownership(jid)
            except Exception:
                pass

    def _db_clear_ownership(self, jid: str) -> None:
        clear = getattr(self.queue, "clear_ownership", None)
        if clear:
            clear(jid)

    def _drive(self, job, jid: str) -> str:
        if job.state == "pending":
            self.queue.set_state(jid, "preflight")
            report = self.preflight(job)
            if not report.passed:
                self._fail(jid := self.queue.get(jid), "preflight",
                           f"preflight failed: {report.detail}")
                return jid
            job = self.queue.get(jid)

        if job.state == "preflight":
            self.queue.set_state(jid, "rendering")
            job = self.queue.get(jid)

        if job.state == "rendering":
            self._render_clips(job)
            job = self.queue.get(jid)

        if job.state == "rendered_pending_qc":
            self.queue.set_state(jid, "qc")
            job = self.queue.get(jid)

        if job.state == "qc":
            self._qc_clips(job)

        return jid

    def _pick_job(self):
        # stale-active recovery first (reviewer B2): orphaned
        # 'rendering'/'preflight'/'qc' jobs (dead owner pid / stale
        # heartbeat) go back to pending and are picked up here.
        recover = getattr(self.queue, "recover_stale_active", None)
        if recover is not None:
            recover(staleness_s=self.staleness_s)
        pending = self.queue.next_pending()
        if pending is not None:
            return self.queue.get(pending)
        parked = self.queue.list_state("rendered_pending_qc")
        if parked:
            return self.queue.get(parked[0])
        return None
