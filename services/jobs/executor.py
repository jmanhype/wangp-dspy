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
import json
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional

from services.jobs.states import transition
from services.jobs.modes import (
    ModeError, ProductMode,
)
from services.jobs.spend_gate import SpendGateRecorder, write_live_row

# "20/20" / "8/8" Denoising — complete when the two numbers match
# LIVE FIX (2026-09-03, strict-chain V2): WanGP's H3 progress lines are
# tqdm-shaped ("H3 denoising: 100%|████| 20/20 [...]"), case-varying —
# the anchored `Denoising N/N` never matched and the executor failed
# healthy renders after the seam already accepted them. Same tolerant
# matcher as host.wangp_adapter.verify_denoise_steps.
_DENOISE_COMPLETE_RE = re.compile(
    r"(?i)denoising:?\s[^\r\n]{0,200}?(\d+)/(\d+)\b")
_LOG_TAIL_CHARS = 800
_DEFAULT_VISION_RETRIES = 2

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
    """Structural acceptance: a complete N/N denoise line exists
    (any N/M pair on a denoise line with N == M)."""
    for m in _DENOISE_COMPLETE_RE.finditer(log_text or ""):
        if m.group(1) == m.group(2):
            return True
    return False


def _tail(text: str) -> str:
    return (text or "")[-_LOG_TAIL_CHARS:]


def _unresolved_chain_ref(clip: dict) -> Optional[str]:
    """Return a still-unmaterialized chain reference, if any."""
    values = [clip.get("image_start")]
    refs = clip.get("image_refs")
    if isinstance(refs, (list, tuple)):
        values.extend(refs[:1])
    for value in values:
        if isinstance(value, str) and value.startswith("chain://"):
            return value
    return None


def _is_visual_gate_failure(exc: Exception) -> bool:
    """Return true only for a pixel-gate rejection.

    The Ref2VA QC stage wraps ``VisionJudgeError`` in
    ``Ref2VAQCStageError``.  Service failures (timeouts, malformed JSON,
    missing frames) use different messages and must remain terminal rather
    than being hidden by a seed retry.  Keep this predicate deliberately
    narrow so the retry policy applies to the probabilistic attribution
    failure the judge actually observed.
    """
    text = str(exc).casefold()
    return "visual gate failed:" in text or "vision gate failed:" in text


def _is_post_whisper_failure(exc: Exception) -> bool:
    """Return true only for a scored native-output transcript rejection."""
    evidence = getattr(exc, "whisper_evidence", None)
    if not isinstance(evidence, dict):
        return False
    post = evidence.get("post")
    return (isinstance(post, dict)
            and post.get("passed") is False
            and isinstance(post.get("transcript"), str)
            and isinstance(post.get("score"), (int, float)))


def _is_av_sync_failure(exc: Exception) -> bool:
    """Return true only for scored SyncNet rejection evidence."""
    evidence = getattr(exc, "av_sync_evidence", None)
    return (isinstance(evidence, dict)
            and evidence.get("passed") is False
            and isinstance(evidence.get("confidence"), (int, float)))


def _whisper_rejection_evidence(exc: Exception) -> dict:
    evidence = getattr(exc, "whisper_evidence", None)
    return dict(evidence) if isinstance(evidence, dict) else {}


def _seed_value(clip: dict):
    """Read a render seed without accepting an absent/invalid value."""
    value = clip.get("seed")
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def _vision_rejection_evidence(exc: Exception) -> dict:
    """Extract judge evidence carried by a visual-gate exception."""
    scores = (getattr(exc, "vision_scores", None)
              or getattr(exc, "scores", None) or {})
    raw = (getattr(exc, "vision_raw_response", None)
           if hasattr(exc, "vision_raw_response")
           else getattr(exc, "raw_response", None))
    mouth_raw = (getattr(exc, "vision_mouth_bbox_raw_response", None)
                 if hasattr(exc, "vision_mouth_bbox_raw_response")
                 else getattr(exc, "mouth_bbox_raw_response", None))
    return {
        "scores": dict(scores) if isinstance(scores, dict) else {},
        "raw_response": (str(raw) if raw is not None else None),
        "mouth_bbox_raw_response": (
            str(mouth_raw) if mouth_raw is not None else None),
    }


def _has_vision_rejection_evidence(exc: Exception) -> bool:
    """Whether a terminal vision-contract failure carries durable evidence."""
    evidence = _vision_rejection_evidence(exc)
    return (bool(evidence["scores"])
            or evidence["raw_response"] is not None
            or evidence["mouth_bbox_raw_response"] is not None)


def _av_sync_rejection_evidence(exc: Exception) -> dict:
    evidence = getattr(exc, "av_sync_evidence", None)
    return dict(evidence) if isinstance(evidence, dict) else {}


class JobExecutor:
    """One trusted 3090; single-job step machine driver.

    run_once(): take the oldest admissible job, drive it one phase.
    Returns the job id handled, or None when there is nothing to do.
    """

    def __init__(self, *, queue, preflight: Callable,
                 render: Callable[[dict], RenderOutcome],
                 qc: Callable[[dict], tuple],
                 ref2va_render: Optional[Callable[[dict], RenderOutcome]] = None,
                 pre_render: Optional[Callable[[dict], None]] = None,
                 max_failures: int = 3,
                 staleness_s: float = 600.0,
                 picker: Optional[Callable[[], Optional[str]]] = None,
                 spend_gate_recorder: Optional[SpendGateRecorder] = None):
        self.queue = queue
        self.preflight = preflight
        self.render = render
        # pre_render hook: optional phase before each clip's render leg
        # (phased QC kill/restart — ops config wires it; default no-op).
        self.pre_render = pre_render
        # ref2va lane renderer (per-job-kind routing); when None the
        # ref2va lane FAILS CLOSED — never silently rendered on fl2va.
        self.ref2va_render = ref2va_render
        self.qc = qc
        self.max_failures = max_failures
        raw_retries = os.environ.get("WANGP_VISION_RETRIES")
        try:
            self.vision_retries = (int(raw_retries)
                                   if raw_retries is not None
                                   else _DEFAULT_VISION_RETRIES)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "WANGP_VISION_RETRIES must be a non-negative integer") from exc
        if self.vision_retries < 0:
            raise ValueError("WANGP_VISION_RETRIES must be non-negative")
        raw_whisper_retries = os.environ.get("WANGP_WHISPER_RETRIES")
        try:
            self.whisper_retries = (
                int(raw_whisper_retries)
                if raw_whisper_retries is not None
                else _DEFAULT_VISION_RETRIES)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "WANGP_WHISPER_RETRIES must be a non-negative integer"
            ) from exc
        if self.whisper_retries < 0:
            raise ValueError("WANGP_WHISPER_RETRIES must be non-negative")
        # Job picker: given the queue, return the next pending job id
        # to execute (or None). PRODUCTION DEFAULT is needs-aware —
        # a job whose `needs` dependency is not done can NEVER be
        # picked (reviewer blocker: gating must live on the actual
        # execution path, not just in the worker entrypoint). An
        # explicit `picker` overrides it (tests, alternate policies).
        self.picker = picker
        # Observability seam: enabled by default at the production executor
        # boundary, but strictly fail-open (see SpendGateRecorder.record).
        self.spend_gate_recorder = spend_gate_recorder or SpendGateRecorder(
            write_row=write_live_row,
            repository_root=Path(__file__).resolve().parents[2],
        )
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
        # Append immutable attempt evidence when the durable queue supports
        # the Finding #21 retry seam.  A repeated signature on the attempt
        # immediately following a requeue disables any further retries;
        # the current failure still becomes terminal ``failed`` evidence.
        record_attempt = getattr(self.queue, "record_attempt_failure", None)
        repeated_retry = False
        if callable(record_attempt):
            repeated_retry = bool(record_attempt(
                jid, failure_class=failure_class,
                failure_detail=detail))
        if repeated_retry:
            state = self.queue.get(jid).state
            if state not in ("failed", "dead_letter"):
                self.queue.set_state(jid, "failed")
            return
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
            if clip.get("status") in ("done", "rendered"):
                # checkpoint/adoption resume: a rendered clip already has
                # its log+mp4 evidence; re-gate it instead of burning a
                # second GPU render.  ``done`` also remains untouched.
                continue
            unresolved = _unresolved_chain_ref(clip)
            if unresolved:
                # Never spend a render attempt handing a chain URI to
                # WanGP/ffmpeg; the predecessor frame must be materialized
                # before render admission.
                self._fail(
                    job, "unresolved_chain_ref",
                    f"clip {clip['clip_index']} still references "
                    f"{unresolved!r} at render admission; advance_chain "
                    "must materialize the predecessor frame first")
                return
            # pre_render hook (phased QC kill/restart seam): injectable,
            # default no-op. Runs immediately before the render leg.
            if self.pre_render is not None:
                self.pre_render(clip)
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
            mark_attempt = getattr(
                self.queue, "mark_clip_render_attempt", None)
            if callable(mark_attempt):
                try:
                    mark_attempt(job.job_id, clip["clip_index"])
                except Exception as exc:
                    self._fail(
                        job, "queue_admission_error",
                        f"[lane={lane}] failed to persist render-admission "
                        f"marker for clip {clip['clip_index']}: "
                        f"{type(exc).__name__}: {exc}")
                    return
            # Keep the in-memory record aligned with the durable attempt flag
            # even when a fake queue does not implement the mutation seam.
            clip["render_attempted"] = True
            try:
                outcome = render_fn(clip)
            except Exception as e:
                # A renderer failure must become durable queue evidence.
                # Letting it escape leaves the claimed job in ``rendering``
                # with no failure class/detail; stale recovery can then
                # requeue the same deterministic error indefinitely.
                self._fail(
                    job, "render_error",
                    f"[lane={lane}] render failed for clip "
                    f"{clip['clip_index']}: {type(e).__name__}: {e}")
                return
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
                # Typed evidence-gate violations are terminal for this
                # attempt: repeatedly parking a Ref2VA job whose Whisper /
                # vision inputs are absent would make the film drain spin
                # forever.  Generic service outages retain the historical
                # park-and-retry behavior.
                if e.__class__.__name__ in {
                        "Ref2VAQCStageError", "WhisperGateError",
                        "VisionJudgeError"}:
                    detail = str(e)
                    if _is_visual_gate_failure(e):
                        evidence = _vision_rejection_evidence(e)
                        self._persist_visual_rejection(
                            job, clip, evidence, detail)
                        if (evidence["scores"] or evidence["raw_response"]
                                or evidence["mouth_bbox_raw_response"]):
                            detail = (f"{detail}; vision_evidence="
                                      f"{json.dumps(evidence, sort_keys=True)}")
                        if self._retry_visual_gate(job, clip, detail):
                            return
                        # Include the seed on the terminal/exhausted
                        # attempt too, so the durable failure signature and
                        # operator report identify every render tried.
                        seed = _seed_value(clip)
                        if seed is not None:
                            detail = f"{detail}; seed={seed}"
                    elif _has_vision_rejection_evidence(e):
                        evidence = _vision_rejection_evidence(e)
                        self._persist_visual_rejection(
                            job, clip, evidence, detail)
                        if (evidence["scores"] or evidence["raw_response"]
                                or evidence["mouth_bbox_raw_response"]):
                            detail = (f"{detail}; vision_evidence="
                                      f"{json.dumps(evidence, sort_keys=True)}")
                        self._fail(job, "qc_gate", detail)
                        return
                    elif _is_post_whisper_failure(e):
                        evidence = _whisper_rejection_evidence(e)
                        self._persist_whisper_rejection(
                            job, clip, evidence, detail)
                        if evidence:
                            detail = (
                                f"{detail}; whisper_evidence="
                                f"{json.dumps(evidence, sort_keys=True)}")
                        if self._retry_whisper_gate(job, clip, detail):
                            return
                        seed = _seed_value(clip)
                        if seed is not None:
                            detail = f"{detail}; seed={seed}"
                    elif _is_av_sync_failure(e):
                        evidence = _av_sync_rejection_evidence(e)
                        history = clip.get("av_sync_rejections")
                        if not isinstance(history, list):
                            history = []
                        clip["av_sync_rejections"] = [*history, {
                            "attempt": len(history) + 1,
                            "seed": _seed_value(clip),
                            "mp4": clip.get("mp4"),
                            "log": clip.get("log"),
                            "evidence": evidence,
                            "failure_detail": detail,
                        }]
                        update_clips = getattr(self.queue, "update_clips", None)
                        if callable(update_clips):
                            update_clips(job.job_id, job.clips)
                        if evidence:
                            detail = (
                                f"{detail}; av_sync_evidence="
                                f"{json.dumps(evidence, sort_keys=True)}")
                        if self._retry_scored_gate(
                                job, clip, detail, gate_name="av_sync",
                                retries=self.vision_retries):
                            return
                        seed = _seed_value(clip)
                        if seed is not None:
                            detail = f"{detail}; seed={seed}"
                    self._fail(job, "qc_gate", detail)
                    return
                # QC unavailable mid-job: park, do NOT fail
                self.queue.set_state(job.job_id,
                                     "rendered_pending_qc")
                return
            if not ok:
                self._fail(job, "qc_reject",
                           f"QC rejected clip {clip['clip_index']}: "
                           f"verdict={qc_path}")
                return
            self.spend_gate_recorder.record(
                Path(qc_path), job_id=job.job_id,
                clip_index=clip.get("clip_index"))
            self.queue.update_clip(
                job.job_id, clip["clip_index"], status="done",
                log=clip["log"], mp4=clip["mp4"],
                qc_verdict={"verdict": (
                    "NEEDS REVIEW" if render_lane_for(clip.get("kind")) == "ref2va"
                    else "KEEP"), "path": qc_path})
        self.queue.set_state(job.job_id, "done")

    def _persist_visual_rejection(self, job, clip: dict,
                                  evidence: dict, detail: str) -> None:
        """Persist scores/raw judge text before any reseed/reset occurs."""
        history = clip.get("vision_rejections")
        if not isinstance(history, list):
            history = []
        entry = {
            "attempt": len(history) + 1,
            "seed": _seed_value(clip),
            "scores": dict(evidence.get("scores") or {}),
            "raw_response": evidence.get("raw_response"),
            "mouth_bbox_raw_response": evidence.get(
                "mouth_bbox_raw_response"),
            "failure_detail": detail,
        }
        clip["vision_rejections"] = [*history, entry]
        update_clips = getattr(self.queue, "update_clips", None)
        if callable(update_clips):
            update_clips(job.job_id, job.clips)

    def _persist_whisper_rejection(self, job, clip: dict,
                                   evidence: dict, detail: str) -> None:
        """Persist native pre/post transcript evidence before any retry."""
        history = clip.get("whisper_rejections")
        if not isinstance(history, list):
            history = []
        entry = {
            "attempt": len(history) + 1,
            "seed": _seed_value(clip),
            "mp4": clip.get("mp4"),
            "log": clip.get("log"),
            "evidence": dict(evidence or {}),
            "failure_detail": detail,
        }
        clip["whisper_rejections"] = [*history, entry]
        update_clips = getattr(self.queue, "update_clips", None)
        if callable(update_clips):
            update_clips(job.job_id, job.clips)

    def _retry_visual_gate(self, job, clip: dict, detail: str) -> bool:
        return self._retry_scored_gate(
            job, clip, detail, gate_name="vision",
            retries=self.vision_retries)

    def _retry_whisper_gate(self, job, clip: dict, detail: str) -> bool:
        return self._retry_scored_gate(
            job, clip, detail, gate_name="whisper",
            retries=self.whisper_retries)

    def _retry_scored_gate(self, job, clip: dict, detail: str, *,
                           gate_name: str, retries: int) -> bool:
        """Requeue a scored probabilistic gate rejection with a new seed.

        Visual attribution misses and native post-Whisper drift are both
        stochastic. Golden replay controls remain deterministic comparisons
        and are not reseeded. Every attempt remains append-only in the
        durable queue and retains prior render/log evidence. Missing/invalid
        seeds,
        an exhausted budget, and queue implementations without the audited
        retry seam all fail closed as ordinary QC failures.
        """
        # A golden replay is a controlled comparison, not a seed search.
        # A production bundle may reuse the golden_v3 recipe while explicitly
        # declining byte-exact replay status; such clips opt into retries.
        if clip.get("golden_replay", clip.get("recipe_name") == "golden_v3"):
            return False
        count_field = f"{gate_name}_retry_count"
        history_field = f"{gate_name}_retry_history"
        count_raw = clip.get(count_field, 0)
        try:
            count = int(count_raw)
        except (TypeError, ValueError):
            return False
        if count < 0 or count >= retries:
            return False
        seed = _seed_value(clip)
        if seed is None:
            return False
        requeue = getattr(self.queue, "requeue_failed", None)
        update_clips = getattr(self.queue, "update_clips", None)
        if not callable(requeue) or not callable(update_clips):
            return False

        # Include the seed in the failure signature.  Two different seeds
        # are distinct probabilistic attempts; the queue's same-signature
        # loop guard must still stop a deterministic repeat when a seed was
        # accidentally not changed.
        failure_detail = f"{detail}; seed={seed}"
        self._fail(job, "qc_gate", failure_detail)
        current = self.queue.get(job.job_id)
        if current.state != "failed":
            # _fail may exhaust the shared qc_gate budget and move the job
            # directly to dead_letter. That failure is already durable;
            # reporting it unhandled would make _qc_clips call _fail again
            # from a terminal state.
            return True

        next_seed = seed + 1
        history = clip.get(history_field)
        if not isinstance(history, list):
            history = []
        history = list(history)
        history.append({
            "attempt": count + 1,
            "seed": seed,
            "mp4": clip.get("mp4"),
            "log": clip.get("log"),
            "qc_evidence_path": clip.get("qc_evidence_path"),
            "failure_class": "qc_gate",
            "failure_detail": failure_detail,
        })
        # Reset only this clip's render/QC claims.  Chain metadata and all
        # completed predecessor clips remain intact for the next attempt.
        original = dict(clip)
        clip[count_field] = count + 1
        clip[history_field] = history
        clip["seed"] = next_seed
        clip["status"] = "pending"
        clip["log"] = None
        clip["mp4"] = None
        clip["qc_verdict"] = None
        # Each new render occupies a new artifact directory. Do not point its
        # QC stage at (and overwrite) the previous attempt's evidence file.
        clip["qc_evidence_path"] = None
        mutate_inputs = getattr(
            self.queue, "update_render_inputs", update_clips)
        mutate_inputs(job.job_id, job.clips)
        reason = (f"{gate_name} gate retry {count + 1}/{retries}; "
                  f"seed {seed} -> {next_seed}")
        try:
            requeue(job.job_id, reason=reason)
        except Exception:
            # The failed attempt and its clip history are durable even when
            # a concurrent worker/state race prevents requeueing. Restore
            # the artifact claim because the job remains terminal failed.
            clip.clear()
            clip.update(original)
            update_clips(job.job_id, job.clips)
            return True
        return True

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
            # Release ownership (the job may have moved to a parked/terminal
            # state). Stale-active recovery remains the durable cleanup path.
            with suppress(Exception):
                self._db_clear_ownership(jid)

    def _db_clear_ownership(self, jid: str) -> None:
        clear = getattr(self.queue, "clear_ownership", None)
        if clear:
            clear(jid)

    def _drive(self, job, jid) -> str:
        if job.state == "pending":
            # NIGHT TWO sequencing fix: the pre_render hook (localhost
            # qc-stack bring-up / llama-server launch) fires BEFORE the
            # preflight probe — preflight's healthz needs the QC stack
            # the hook just started, not one started mid-render leg.
            if self.pre_render is not None:
                for clip in job.clips:
                    self.pre_render(clip)
            self.queue.set_state(jid, "preflight")
            report = self.preflight(job)
            if not report.passed:
                self._fail(self.queue.get(jid), "preflight",
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
        pending = self._next_pending_id()
        if pending is not None:
            return self.queue.get(pending)
        parked = self.queue.list_state("rendered_pending_qc")
        if parked:
            return self.queue.get(parked[0])
        return None

    def _next_pending_id(self) -> Optional[str]:
        """Pick the next pending job id through the configured picker.

        Default (production) is needs-aware: queue.next_admissible()
        when the queue provides it, falling back to the shared
        next_admissible(queue) helper (test fakes), so a blocked
        dependent can never be picked on the execution path. An
        explicit `picker` override wins outright.
        """
        if self.picker is not None:
            return self.picker()
        if hasattr(self.queue, "next_admissible"):
            return self.queue.next_admissible()
        from services.jobs.queue import next_admissible as _next_adm
        return _next_adm(self.queue)
