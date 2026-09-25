#!/usr/bin/env python3
"""Bind measured artifacts to completed WD-2gyw queue clips."""
from __future__ import annotations

import json
from pathlib import Path

from services.jobs.queue import JobQueue


def main() -> int:
    bundle = Path(__file__).resolve().parent
    record = json.loads((bundle / "queue-record.json").read_text(encoding="utf-8"))
    artifacts = {
        1: ("h3-standard.render.log", "outputs/wd_2gyw_h3_standard.mp4"),
        2: ("h3-specialized.render.log", "outputs/wd_2gyw_h3_vdn_hybrid_attention.mp4"),
        3: ("h3-kfi-retry.render.log", "outputs/wd_2gyw_h3_kfi_frames_injection.mp4"),
        4: ("h3-specialized.render.log", "outputs/wd_2gyw_h3_audio_refinement.mp4"),
        5: ("hunyuan.render.log", "outputs/wd_2gyw_hunyuan.mp4"),
    }
    queue = JobQueue(bundle / "queue.db")
    try:
        job = queue.get(record["job_id"])
        for clip in job.clips:
            log, output = artifacts[clip["clip_index"]]
            queue.update_clip(
                record["job_id"], clip["clip_index"], status="done", log=log,
                mp4=output,
                qc_verdict={"verdict": "NEEDS REVIEW", "path": "objective-gates.json"},
            )
        for state in ("preflight", "rendering", "rendered_pending_qc", "qc", "done"):
            queue.set_state(record["job_id"], state)
        final = queue.get(record["job_id"])
    finally:
        queue.close()
    print(json.dumps({
        "job_id": final.job_id,
        "state": final.state,
        "clips": final.clips,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
