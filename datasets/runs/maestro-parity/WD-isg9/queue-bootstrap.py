#!/usr/bin/env python3
"""Create the durable WD-isg9 H3-standard operation batch."""
from __future__ import annotations

import json
from pathlib import Path

from services.jobs.queue import JobQueue


def clip(index: int, operation: str, seed: int, *, boundary: bool = False) -> dict:
    return {
        "clip_index": index,
        "status": "pending",
        "log": None,
        "mp4": None,
        "qc_verdict": None,
        "kind": "host_boundary" if boundary else "video_generation",
        "family": "minimax_h3",
        "preset": "standard",
        "operation": operation,
        "prompt": "WD-isg9 H3-standard operation-specific evidence",
        "seed": seed,
        "video_length": 120 if operation == "extend" else 56,
    }


CLIPS = [
    clip(1, "extend", 2945),
    clip(2, "retake", 2946),
    clip(3, "edit", 2947),
    clip(4, "repaint", 2948),
    clip(5, "upscale", 2949),
    clip(6, "blend", 2950, boundary=True),
    clip(7, "recast", 2951, boundary=True),
    clip(8, "outpaint", 2952, boundary=True),
]


def main() -> int:
    bundle = Path(__file__).resolve().parent
    database = bundle / "queue.db"
    if database.exists():
        raise SystemExit(f"refusing to replace existing queue: {database}")
    queue = JobQueue(database)
    try:
        job_id = queue.submit(plan_ref="WD-isg9-h3-standard-operations", clips=CLIPS)
    finally:
        queue.close()
    record = {
        "queue_id": "wangp-JobQueue-WD-isg9",
        "database": "queue.db",
        "job_id": job_id,
        "retry_id": "attempt-2",
        "admission_state": "admitted",
        "preflight": "preflight.json",
        "attempt_note": "Attempt 1 was dispatcher-stopped before denoising because host snapshot paths were malformed; its files were quarantined on the host and are not evidence.",
    }
    (bundle / "queue-record.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
