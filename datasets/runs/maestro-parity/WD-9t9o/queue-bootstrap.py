#!/usr/bin/env python3
"""Create the durable WD-9t9o H3 VDN operation batch."""
from __future__ import annotations

import json
from pathlib import Path

from services.jobs.queue import JobQueue


def clip(index: int, operation: str, seed: int, *, output: bool) -> dict:
    return {
        "clip_index": index,
        "status": "pending",
        "log": None,
        "mp4": None,
        "qc_verdict": None,
        "kind": "video_generation" if output else "host_boundary",
        "family": "minimax_h3",
        "preset": "h3_vdn_hybrid_attention",
        "operation": operation,
        "prompt": "WD-9t9o VDN operation-specific evidence",
        "seed": seed,
        "video_length": 120 if operation == "extend" else 56,
    }


CLIPS = [
    clip(1, "extend", 2961, output=False),
    clip(2, "retake", 2962, output=False),
    clip(3, "edit", 2963, output=True),
    clip(4, "repaint", 2964, output=True),
    clip(5, "upscale", 2968, output=True),
    clip(6, "blend", 2965, output=False),
    clip(7, "recast", 2966, output=False),
    clip(8, "outpaint", 2967, output=False),
]


def main() -> int:
    bundle = Path(__file__).resolve().parent
    database = bundle / "queue.db"
    if database.exists():
        raise SystemExit(f"refusing to replace existing queue: {database}")
    queue = JobQueue(database)
    try:
        job_id = queue.submit(plan_ref="WD-9t9o-h3-vdn-operations", clips=CLIPS)
    finally:
        queue.close()
    record = {
        "queue_id": "wangp-JobQueue-WD-9t9o",
        "database": "queue.db",
        "job_id": job_id,
        "retry_id": "attempt-1",
        "admission_state": "admitted",
        "preflight": "preflight-model-hash-summary.json",
    }
    (bundle / "queue-record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
