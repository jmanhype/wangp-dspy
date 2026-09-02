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
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.jobs.queue import JobQueue  # noqa: E402


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


# ── dependency admissibility ─────────────────────────────────────────

def is_admissible(job, done_jobs) -> bool:
    """True when the job has no unmet `needs` dependencies."""
    needs = job.clips[0].get("needs") if job.clips else None
    if not needs:
        needs = getattr(job, "needs", None)
    if not needs:
        return True
    return needs in done_jobs


def done_job_ids(queue) -> set:
    return set(queue.list_state("done"))


def next_admissible(queue):
    """Oldest pending job whose needs-target is done (or with no
    needs); a blocked job STAYS pending and later jobs are still
    considered (in-order among admissible ones)."""
    done = done_job_ids(queue)
    for jid in queue.list_state("pending"):
        if is_admissible(queue.get(jid), done):
            return jid
    return None


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
    # persist through the queue's clips JSON
    queue._db.execute(  # noqa: SLF001
        "UPDATE jobs SET clips=? WHERE job_id=?",
        (json.dumps(job.clips), job.job_id))
    queue._db.commit()  # noqa: SLF001


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

def build_executor(queue, host=None):
    """Wire JobExecutor with the production render seams (no dry-run
    guard on the jobs path — see module docstring)."""
    from services.jobs.executor import JobExecutor, RenderOutcome
    from services.jobs.preflight import run_preflight
    from host.wangp_adapter import WanGPAdapter

    adapter = WanGPAdapter(host=host) if host is not None else None

    def preflight(job):
        return run_preflight(
            host, models=[], min_free_gb=0.0,
            disk_path="/home/straughter/Wan2GP", qc_url="")

    def render(clip):
        if adapter is None:
            raise RuntimeError(
                "no host wired — run_jobs needs a host for real renders")
        res = adapter.render_for_job(clip)
        settings = getattr(res, "settings_path", "") or ""
        log = (str(Path(settings).parent) + "/render.log"
               if settings else "render.log")
        return RenderOutcome(
            mp4=getattr(res, "video_path", ""),
            log_text=_read_host_log(host, log),
            log_path=log)

    def ref2va_render(clip):
        return render(clip)

    return JobExecutor(queue=queue, preflight=preflight,
                       render=render, ref2va_render=ref2va_render,
                       qc=lambda clip: (True, f"qc/{clip['clip_index']}"
                                        ".json"))


def _read_host_log(host, log_path: str) -> str:
    rc, out, _err = host.run_probe(["cat", log_path], timeout=60)
    return out if rc == 0 else ""


# ── main driver ──────────────────────────────────────────────────────

def drain_once(queue, host=None, dry_run: bool = False, limit=None):
    """Run admissible jobs until none remain (or `limit` jobs, for
     --once callers). Returns list of handled job ids. --dry-run emits
    what would run WITHOUT host calls and WITHOUT mutating state."""
    handled = []
    while limit is None or len(handled) < limit:
        jid = next_admissible(queue)
        if jid is None:
            return handled
        job = queue.get(jid)
        if dry_run:
            print(f"[dry-run] would run {jid} "
                  f"(kinds={[c.get('kind') for c in job.clips]})")
            handled.append(jid)
            # advance WITHOUT mutating queue state: mark done locally
            # so next_admissible skips it in this process
            real_done = queue.list_state

            def _done_with_extra(state, _extra=jid, _real=real_done):
                ids = _real(state)
                return ids + ([_extra] if state == "done" else [])
            queue.list_state = _done_with_extra  # type: ignore
            continue
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


def main(argv=None):
    args = build_parser().parse_args(argv)
    queue = JobQueue(args.db)
    try:
        if args.dry_run:
            print(json.dumps(dry_run_report(queue), indent=2))
            return 0
        if args.once:
            # --once: exactly ONE admissible job
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
    return SshHost(target="3090",
                   wgp_root="/home/straughter/Wan2GP",
                   pull_root="datasets/runs/pull")


if __name__ == "__main__":
    raise SystemExit(main())
