#!/usr/bin/env python3
"""Create the durable WD-cpow three-operation audio-post batch."""
from __future__ import annotations

import json
from pathlib import Path

from services.jobs.queue import JobQueue


CLIPS = [
    {
        "clip_index": 1,
        "status": "pending",
        "log": None,
        "mp4": None,
        "qc_verdict": None,
        "kind": "audio_post_generation",
        "family": "stable_audio",
        "operation": "sfx",
        "prompt": "dry metal gate latch clack followed by a small chain sway in a close room",
        "seed": 9101,
        "video_length": 54,
    },
    {
        "clip_index": 2,
        "status": "pending",
        "log": None,
        "mp4": None,
        "qc_verdict": None,
        "kind": "audio_post_generation",
        "family": "vibevoice",
        "operation": "revoice",
        "prompt": "This is the last rain we have.",
        "seed": 9201,
        "video_length": 56,
    },
    {
        "clip_index": 3,
        "status": "pending",
        "log": None,
        "mp4": None,
        "qc_verdict": None,
        "kind": "audio_post_generation",
        "family": "deepfilternet",
        "operation": "refine",
        "prompt": "denoise_and_loudness noise_reduction_db=6 target_lufs=-18",
        "seed": 9301,
        "video_length": 56,
    },
]


def main() -> int:
    bundle = Path(__file__).resolve().parent
    database = bundle / "queue.db"
    if database.exists():
        raise SystemExit(f"refusing to replace existing queue: {database}")
    queue = JobQueue(database)
    try:
        job_id = queue.submit(plan_ref="WD-cpow-audio-post-batch-1", clips=CLIPS)
    finally:
        queue.close()
    record = {
        "queue_id": "wangp-JobQueue-WD-cpow",
        "database": "queue.db",
        "job_id": job_id,
        "retry_id": "attempt-1",
        "admission_state": "admitted",
        "preflight": "selected-doctor-preflight-after-download.json",
    }
    (bundle / "queue-record.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
