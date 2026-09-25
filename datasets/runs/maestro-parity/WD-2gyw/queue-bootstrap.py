#!/usr/bin/env python3
"""Create the durable WD-2gyw feasible-subset video batch."""
from __future__ import annotations

import json
from pathlib import Path

from services.jobs.queue import JobQueue


def clip(index: int, family: str, preset: str, operation: str,
         seed: int) -> dict:
    return {
        "clip_index": index,
        "status": "pending",
        "log": None,
        "mp4": None,
        "qc_verdict": None,
        "kind": "video_generation",
        "family": family,
        "preset": preset,
        "operation": operation,
        "prompt": "WD-2gyw feasible-subset compass/crane evidence clip",
        "seed": seed,
        "video_length": 56,
    }


CLIPS = [
    clip(1, "minimax_h3", "standard", "create", 2931),
    clip(2, "minimax_h3", "h3_vdn_hybrid_attention", "create", 2932),
    clip(3, "minimax_h3", "kfi_frames_injection", "retake", 2933),
    clip(4, "minimax_h3", "h3_audio_refinement", "edit", 2934),
    clip(5, "hunyuan", "standard", "create", 2942),
]


def main() -> int:
    bundle = Path(__file__).resolve().parent
    database = bundle / "queue.db"
    if database.exists():
        raise SystemExit(f"refusing to replace existing queue: {database}")
    queue = JobQueue(database)
    try:
        job_id = queue.submit(plan_ref="WD-2gyw-feasible-video-subset", clips=CLIPS)
    finally:
        queue.close()
    record = {
        "queue_id": "wangp-JobQueue-WD-2gyw",
        "database": "queue.db",
        "job_id": job_id,
        "retry_id": "attempt-1",
        "admission_state": "admitted",
        "preflight": "doctor-preflight-after-download.json",
    }
    (bundle / "queue-record.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
