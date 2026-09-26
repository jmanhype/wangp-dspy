#!/usr/bin/env python3
"""Bind WD-isg9 artifacts and captured boundaries to the durable queue."""
from __future__ import annotations

import json
from pathlib import Path

from services.jobs.queue import JobQueue


def main() -> int:
    bundle = Path(__file__).resolve().parent
    record = json.loads((bundle / "queue-record.json").read_text(encoding="utf-8"))
    artifacts = {
        1: ("host-logs/extend.render.log", "outputs/extend/wd_isg9_extend.mp4"),
        2: ("host-logs/retake.render.log", "outputs/retake/wd_isg9_retake.mp4"),
        3: ("host-logs/edit.render.log", "outputs/edit/wd_isg9_edit.mp4"),
        4: ("host-logs/repaint.render.log", "outputs/repaint/wd_isg9_repaint.mp4"),
        5: ("host-logs/upscale.render.log", "outputs/upscale/wd_isg9_upscale.mp4"),
        6: ("host-logs/blend-probe.render.log", None),
        7: ("host-logs/recast-probe.render.log", None),
        8: ("boundary-code-evidence.txt", None),
    }
    queue = JobQueue(bundle / record["database"])
    try:
        job = queue.get(record["job_id"])
        for clip in job.clips:
            log, output = artifacts[clip["clip_index"]]
            queue.update_clip(
                record["job_id"], clip["clip_index"],
                status="unsupported" if output is None else "done",
                log=log,
                mp4=output,
                qc_verdict={
                    "verdict": "UNSUPPORTED HOST BOUNDARY" if output is None else "NEEDS REVIEW",
                    "path": "objective-measurements.json" if output else log,
                },
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
