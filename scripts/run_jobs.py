"""Production queue worker entrypoint (PR feat/production-render-seam).

Drives pending jobs through JobExecutor IN ORDER, honoring job.needs
dependencies (a job whose needs-target is not done stays pending).

    .venv/bin/python scripts/run_jobs.py --db jobs.db --once
    .venv/bin/python scripts/run_jobs.py --db jobs.db --loop 30
    .venv/bin/python scripts/run_jobs.py --db jobs.db --dry-run

Guard distinction (documented): scripts/run_cycle.py keeps its
ref2va "dry-run only" guard — it is a one-shot cycle driver whose
ref2va lane predates this seam. THIS entrypoint removes that guard:
the jobs path executes ref2va through the production render seam
(JobExecutor + adapter.render_for_job). Different entrypoints,
different contracts.

r2i -> fl2va dependency execution: when an r2i job (kind
r2i_pose_target) completes, its LAST FRAME is extracted on the host
(ffmpeg -sseof -0.1 -i <mp4> -frames:v 1 <png>) into the run dir and
recorded as the verified artifact the fl2va job (needs=<r2i job id>)
consumes. CONTINUATION jobs unwrap through
services.jobs.modes.unwrap_continuation using verified prior
last-frames.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# live smoke fix 3: the preflight QC healthz probe needs a REAL url —
# the "" placeholder made `curl -fsS -m N ""` fail on every job.
# Env-overridable via WANGP_QC_URL.
DEFAULT_QC_URL = "http://localhost:8000/health"

from services.jobs.queue import (  # noqa: E402,F401
    JobQueue, is_job_admissible as _is_admissible_impl,
    next_admissible as _next_admissible_impl,
)


def is_admissible(job, done_jobs) -> bool:
    """True when the job has no unmet `needs` dependencies.

    Thin re-export of the queue-module implementation so the executor
    path and the worker path share ONE admissibility definition."""
    return _is_admissible_impl(job, done_jobs)


def done_job_ids(queue) -> set:
    return set(queue.list_state("done"))


def _recover_stale_active(queue) -> list:
    """Requeue orphaned active jobs before applying dependency gating.

    ``JobExecutor._pick_job`` performs the same recovery, but the worker
    entrypoint must do it before its own ``next_admissible`` pre-pick.  A
    stale prerequisite otherwise remains in ``rendering`` and makes every
    dependent appear blocked forever at the entrypoint boundary.
    """
    recover = getattr(queue, "recover_stale_active", None)
    if recover is None:
        return []
    raw = os.environ.get("WANGP_STALENESS_S")
    if raw:
        return recover(staleness_s=float(raw))
    return recover()


def next_admissible(queue):
    """Oldest pending job whose needs-target is done (or with no
    needs). Delegates to services.jobs.queue.next_admissible — the
    SAME gating the executor's default picker uses."""
    return _next_admissible_impl(queue)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_jobs",
        description="Process pending jobs from the durable job queue.")
    p.add_argument("--db", required=True, help="path to the jobs.db")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--once", action="store_true",
                   help="process one admissible job then exit")
    g.add_argument("--loop", type=float, metavar="SECS",
                   help="poll forever, sleeping SECS between drains")
    p.add_argument("--dry-run", action="store_true",
                   help="emit what would run; NO host calls")
    return p


# ── r2i last-frame extraction (host seam, ffmpeg) ────────────────────

def extract_last_frame_argv(mp4: str, png: str) -> list:
    """The proven shape: last frame of mp4 -> png via -sseof -0.1."""
    return ["ffmpeg", "-y", "-sseof", "-0.1", "-i", mp4,
            "-frames:v", "1", png]


def extract_last_frame(host, mp4: str, png: str) -> None:
    """Extract the last frame ON THE HOST (ffmpeg via run_probe seam).
    Raises RuntimeError on nonzero rc — the artifact is only recorded
    when extraction verifiably succeeded."""
    rc, _out, err = host.run_probe(extract_last_frame_argv(mp4, png),
                                   timeout=300)
    if rc != 0:
        raise RuntimeError(
            f"r2i last-frame extraction failed (ffmpeg rc={rc}): "
            f"{(err or '')[:200]}")


def record_last_frame(queue, job, png: str) -> None:
    """Record the extracted frame as the verified artifact dependents
    consume (clip-level `last_frame` + job-level done bookkeeping)."""
    for c in job.clips:
        if c.get("kind") == "r2i_pose_target":
            c["last_frame"] = png
    # persist through the queue's PUBLIC clips write (no _db poking)
    queue.update_clips(job.job_id, job.clips)


def r2i_last_frame_png(run_dir: str, job) -> str:
    """Convention (matches emit_fl2va_job's image_end path):
    <run_dir>/<r2i job id>_last_frame.png under render/clipNNNN."""
    clip = job.clips[0] if job.clips else {}
    idx = clip.get("clip_index", 0)
    return f"{run_dir}/render/clip{int(idx):04d}/" \
           f"{job.job_id}_last_frame.png"


# ── dry-run emission ─────────────────────────────────────────────────

def dry_run_report(queue) -> dict:
    jobs = []
    done = done_job_ids(queue)
    for jid in queue.list_state("pending"):
        job = queue.get(jid)
        blocked = not is_admissible(job, done)
        jobs.append({
            "job_id": jid, "state": job.state,
            "plan_ref": job.plan_ref,
            "kinds": [c.get("kind") for c in job.clips],
            "blocked_by": (job.clips[0].get("needs")
                           if job.clips and blocked else None),
        })
    return {"would_run": jobs}


# ── executor wiring ──────────────────────────────────────────────────

def build_executor(queue, host=None, pre_render=None,
                   whisper_transcriber=None, vision_judge=None):
    """Wire JobExecutor with the production render seams (no dry-run
    guard on the jobs path — see module docstring)."""
    from services.jobs.executor import JobExecutor, RenderOutcome
    from services.jobs.preflight import run_preflight
    from host.wangp_adapter import WanGPAdapter
    from qc.audio_critic.whisper_cli import host_whisper_transcriber

    adapter = WanGPAdapter(host=host) if host is not None else None
    # The production seam is deliberately structural: a jobs executor may
    # only receive a typed per-job renderer.  Fail during wiring when an
    # adapter implementation does not expose it rather than discovering the
    # gap after claiming a GPU job (or silently falling back to render()).
    render_for_job = (getattr(adapter, "render_for_job", None)
                      if adapter is not None else None)
    if adapter is not None and not callable(render_for_job):
        raise TypeError(
            "WanGPAdapter must expose callable render_for_job(job); "
            "legacy render() is not a production jobs seam")
    if whisper_transcriber is None and host is not None:
        # Production jobs get a real Whisper runner from the existing host
        # seam. Tests and custom operators may still inject a deterministic
        # transcriber explicitly.
        whisper_transcriber = host_whisper_transcriber(host)

    # live smoke fix 3: qc_url="" made the preflight curl probe an
    # EMPTY URL — wire a real default (env-overridable).
    qc_url = (os.environ.get("WANGP_QC_URL")
              or DEFAULT_QC_URL)

    def preflight(job):
        return run_preflight(
            host, models=[], min_free_gb=0.0,
            disk_path="/home/straughter/Wan2GP", qc_url=qc_url)

    def render(clip):
        if adapter is None:
            raise RuntimeError(
                "no host wired — run_jobs needs a host for real renders")
        # NIGHT TWO fix 3: render-leg phased VRAM — on the localhost
        # lane, llama-server (the QC stack preflight needed) is killed
        # BEFORE the wgp render so it gets the VRAM.
        if _is_localhost():
            free_vram_for_render(host)
        # Never call adapter.render() here.  That legacy API accepts a
        # brief/settings shape and cannot carry ContinuationExtras.
        res = render_for_job(clip)
        settings = getattr(res, "settings_path", "") or ""
        log = (str(Path(settings).parent) + "/render.log"
               if settings else "render.log")
        return RenderOutcome(
            mp4=getattr(res, "video_path", ""),
            log_text=_read_host_log(host, log),
            log_path=log)

    def ref2va_render(clip):
        return render(clip)

    def qc(clip):
        # Legacy FL2VA jobs retain their existing QC callback.  Ref2VA
        # continuation jobs must pass the repo-owned audio stage: both
        # pre/post Whisper gates are required, and optional visual judging is
        # bound to the same cut artifact.
        if clip.get("kind") != "ref2va_render":
            return True, f"qc/{clip['clip_index']}.json"
        from qc.audio_critic.ref2va_stage import run_ref2va_qc_stage
        evidence_path = clip.get("qc_evidence_path")
        qc_result = run_ref2va_qc_stage(
            dict(clip), judge=None,
            pre_audio_path=clip.get("audio_guide"),
            post_audio_path=clip.get("mp4"),
            intended_text=clip.get("dialogue_text") or clip.get("prompt"),
            whisper_transcriber=whisper_transcriber,
            evidence_path=evidence_path,
            video_path=(clip.get("mp4") if vision_judge is not None else None),
            expected_speaker=(clip.get("speaker_sn") if vision_judge is not None else None),
            expected_action=(clip.get("action") or clip.get("motion")
                             if vision_judge is not None else None),
            vision_judge=vision_judge)
        return True, qc_result.to_dict()

    return JobExecutor(queue=queue, preflight=preflight,
                       render=render, ref2va_render=ref2va_render,
                       pre_render=pre_render,
                       qc=qc)


def _read_host_log(host, log_path: str) -> str:
    rc, out, _err = host.run_probe(["cat", log_path], timeout=60)
    return out if rc == 0 else ""


# ── main driver ──────────────────────────────────────────────────────

def dry_run_plan(queue, limit=None) -> list:
    """Read-only view of the jobs a real drain would run, in order.

    Same gating as execution (needs-aware), but computed against a
    LOCAL done-set: no queue state is mutated and no shared object is
    monkeypatched. A job whose need is itself only 'would-run' here is
    still shown downstream (it WOULD be done by the time the drain
    reaches its dependent), matching drain semantics."""
    done = done_job_ids(queue)
    planned = []
    for jid in queue.list_state("pending"):
        if limit is not None and len(planned) >= limit:
            break
        if not is_admissible(queue.get(jid), done):
            continue
        planned.append(jid)
        done.add(jid)  # local view only — the queue is untouched
    return planned


def drain_once(queue, host=None, dry_run: bool = False, limit=None):
    """Run admissible jobs until none remain (or `limit` jobs, for
     --once callers). Returns list of handled job ids. --dry-run emits
     what would run WITHOUT host calls and WITHOUT mutating state."""
    if dry_run:
        handled = dry_run_plan(queue, limit=limit)
        for jid in handled:
            job = queue.get(jid)
            print(f"[dry-run] would run {jid} "
                  f"(kinds={[c.get('kind') for c in job.clips]})")
        return handled
    handled = []
    while limit is None or len(handled) < limit:
        _recover_stale_active(queue)
        jid = next_admissible(queue)
        if jid is None:
            return handled
        job = queue.get(jid)
        ex = build_executor(queue, host=host)
        ex.run_once()
        handled.append(jid)
        # r2i -> fl2va dependency: extract + record the last frame
        fresh = queue.get(jid)
        if fresh.state == "done" and any(
                c.get("kind") == "r2i_pose_target"
                for c in fresh.clips) and host is not None:
            mp4 = next((c.get("mp4") for c in fresh.clips if c.get("mp4")),
                       None)
            if mp4:
                png = r2i_last_frame_png(
                    str(Path(queue.db_path).parent), fresh)
                extract_last_frame(host, mp4, png)
                record_last_frame(queue, fresh, png)
        # LIVE FIX 6 (2026-09-03): chain AUTO-ADVANCE — when a chain job
        # (kind ref2va_render with chain metadata) completes, the
        # dependent job's image_refs[0] chain://clipNNNN/last_frame
        # placeholder is materialized from the completed job's mp4
        # (the same proven ffmpeg -sseof -0.1 extraction the r2i path
        # uses) BEFORE the next pick, so the dependent becomes
        # admissible with real refs.
        if fresh.state == "done" and host is not None:
            from services.director.wiring import advance_chain
            advance_chain(queue, host, jid)
    return handled


def main(argv=None):
    args = build_parser().parse_args(argv)
    queue = JobQueue(args.db)
    try:
        if args.dry_run:
            print(json.dumps(dry_run_report(queue), indent=2))
            return 0
        if args.once:
            # --once: exactly ONE admissible job
            _recover_stale_active(queue)
            jid = next_admissible(queue)
            if jid is None:
                print("no admissible pending jobs")
                return 0
            from services.jobs.executor import JobExecutor
            ex = build_executor(queue, host=_default_host())
            ex.run_once()
            print(f"ran {jid}: state={queue.get(jid).state}")
            return 0
        if args.loop:
            while True:
                drain_once(queue, host=_default_host())
                time.sleep(args.loop)
        # default: drain all admissible jobs once
        handled = drain_once(queue, host=_default_host()) or []
        print(f"handled {len(handled)} job(s)")
        return 0
    finally:
        queue.close()


def _default_host():
    from host.render_host import SshHost
    # LIVE FIX 7 (2026-09-03): WANGP_SSH_TARGET env override for
    # on-host execution (e.g. WANGP_SSH_TARGET=localhost on the 3090
    # itself); default unchanged.
    target = os.environ.get("WANGP_SSH_TARGET") or "3090"
    return SshHost(target=target,
                   wgp_root="/home/straughter/Wan2GP",
                   pull_root="datasets/runs/pull")


def _is_localhost() -> bool:
    return os.environ.get("WANGP_SSH_TARGET", "") == "localhost"


# NIGHT TWO (2026-09-03, live-verified shape on the 3090): the direct
# llama-server launch fallback when the systemd unit is absent.
LLAMA_SERVER_LOG = "/tmp/llama-server.log"
_LLAMA_HEALTH_RETRIES = 60
_LLAMA_HEALTH_INTERVAL_S = 2.0


def llama_server_argv(log_path: str = LLAMA_SERVER_LOG) -> list:
    """The DIRECT llama-server launch (systemd fallback): detached,
    logged to /tmp/llama-server.log — the live box shape."""
    return ["setsid", "nohup", "llama-server", "--port", "8000",
            f"> {log_path} 2>&1 &"]


def free_vram_for_render(host) -> None:
    """RENDER-LEG phased VRAM: kill llama-server so the wgp render gets
    the VRAM (NIGHT TWO — the kill lives in the render leg, NOT in the
    pre-preflight phase; preflight still needs the QC stack up).
    """
    host.run_probe(["pkill", "-f", "llama-server"], timeout=30)
    host.run_probe(["sleep", "3"], timeout=30)


def localhost_pre_render(clip) -> None:
    """The phased VRAM dance the box scripts ran on night one/two
    (2026-09-03), as an injectable pre_render hook fired BEFORE
    preflight: bring the QC stack up (systemd attempt, then a DIRECT
    llama-server launch fallback), health-wait until it answers, and
    LEAVE IT RUNNING — the kill moved to the render leg
    (free_vram_for_render, wired into build_executor's render()).

    Default-ON in run_film when WANGP_SSH_TARGET=localhost; a no-op
    elsewhere unless wired explicitly.
    """
    import subprocess

    def _best_effort(argv, timeout=60):
        try:
            return subprocess.run(argv, capture_output=True,
                                  timeout=timeout)
        except Exception:
            return None  # ops config: phased dance, never fatal

    # 1) systemd attempt (the unit exists on some boxes)
    if _best_effort(["systemctl", "--user", "start", "qc-stack"]) \
            is not None:
        # 2) health-wait loop: the probe decides who serves healthz
        if _qc_health_wait(_best_effort):
            return
    # 3) DIRECT llama-server fallback (the live box shape)
    _best_effort(["bash", "-lc", " ".join(llama_server_argv())])
    _qc_health_wait(_best_effort)
    # NOTE: NO kill here — preflight still needs the QC stack; the
    # llama-server kill is free_vram_for_render's job in the render
    # leg.


def _qc_health_wait(run_fn, *, url=None,
                    retries: int = _LLAMA_HEALTH_RETRIES,
                    interval_s: float = _LLAMA_HEALTH_INTERVAL_S) -> bool:
    """Wait until the QC healthz endpoint answers (curl -fsS). Uses
    the same env-overridable URL as the preflight probe."""
    url = url or (os.environ.get("WANGP_QC_URL") or DEFAULT_QC_URL)
    argv = ["curl", "-fsS", "-m", "2", url]
    for _ in range(max(1, retries)):
        proc = run_fn(argv, timeout=5)
        if proc is not None and proc.returncode == 0:
            return True
        time.sleep(max(0.05, interval_s))
    return False


def _pre_render_default(host):
    """Default-on phased QC/kill hook ONLY for localhost execution."""
    target = os.environ.get("WANGP_SSH_TARGET", "")
    if target == "localhost":
        return localhost_pre_render
    return None


if __name__ == "__main__":
    raise SystemExit(main())
