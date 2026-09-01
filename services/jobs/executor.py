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

import re
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from services.jobs.states import transition

# "20/20" / "8/8" Denoising — complete when the two numbers match
_DENOISE_COMPLETE_RE = re.compile(r"Denoising\s+(\d+)/\1\b")
_LOG_TAIL_CHARS = 800


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
                 max_failures: int = 3):
        self.queue = queue
        self.preflight = preflight
        self.render = render
        self.qc = qc
        self.max_failures = max_failures

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
            outcome = self.render(clip)
            # verify-before-trust (ruling 5)
            if not verify_render_log(outcome.log_text):
                self._fail(
                    job, "truncated_render_log",
                    f"render log verification failed for clip "
                    f"{clip['clip_index']} (no complete N/N Denoising "
                    f"line); log tail: {_tail(outcome.log_text)!r}; "
                    f"log={outcome.log_path}")
                return
            self.queue.update_clip(
                job.job_id, clip["clip_index"], status="rendered",
                log=outcome.log_path, mp4=outcome.mp4,
                qc_verdict=None)
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
        pending = self.queue.next_pending()
        if pending is not None:
            return self.queue.get(pending)
        parked = self.queue.list_state("rendered_pending_qc")
        if parked:
            return self.queue.get(parked[0])
        return None
