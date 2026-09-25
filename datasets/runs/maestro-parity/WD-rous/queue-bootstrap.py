#!/usr/bin/env python3
"""Create the durable WD-rous three-operation music batch."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from services.jobs.queue import JobQueue


CLIPS = [
    {
        "clip_index": 1,
        "status": "pending",
        "log": None,
        "mp4": None,
        "qc_verdict": None,
        "kind": "music_generation",
        "family": "ace_step",
        "operation": "generate",
        "prompt": "Bright analog chamber electro swing with crisp hand percussion, warm upright bass, and a clear 120 BPM 4/4 pulse",
        "seed": 1901,
        "video_length": 10,
    },
    {
        "clip_index": 2,
        "status": "pending",
        "log": None,
        "mp4": None,
        "qc_verdict": None,
        "kind": "music_generation",
        "family": "stable_audio",
        "operation": "generate",
        "prompt": "Soft neon synth jazz with mellow electric piano, brushed drums, warm bass, and gentle forward motion at 112 BPM",
        "seed": 2901,
        "video_length": 10,
    },
    {
        "clip_index": 3,
        "status": "pending",
        "log": None,
        "mp4": None,
        "qc_verdict": None,
        "kind": "music_generation",
        "family": "ace_step",
        "operation": "style_adaptation",
        "prompt": "Restyle the ACE source toward the Stable Audio reference while preserving source structure",
        "seed": 3901,
        "video_length": 10,
        "needs_ace_output": "clip 1",
        "needs_stable_output": "clip 2",
    },
]


def main() -> int:
    bundle = Path(__file__).resolve().parent
    database = bundle / "queue.db"
    if database.exists():
        raise SystemExit(f"refusing to replace existing queue: {database}")
    queue = JobQueue(database)
    try:
        job_id = queue.submit(plan_ref="WD-rous-music-batch-1", clips=CLIPS)
    finally:
        queue.close()
    record = {
        "queue_id": "wangp-JobQueue-WD-rous",
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
