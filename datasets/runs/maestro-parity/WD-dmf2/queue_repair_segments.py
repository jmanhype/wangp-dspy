#!/usr/bin/env python3
"""Correct WD-dmf2 segment path width through the public queue seam."""
from __future__ import annotations

import json
from pathlib import Path

from services.jobs.queue import JobQueue


BUNDLE = Path(__file__).resolve().parent


def main() -> int:
    record = json.loads(
        (BUNDLE / "queue-record.json").read_text(encoding="utf-8")
    )
    queue = JobQueue(BUNDLE / "queue.db")
    try:
        job = queue.get(record["job_id"])
        clips = []
        for clip in job.clips:
            item = dict(clip)
            item["segment_outputs"] = [
                path.replace("clip01.mp4", "clip0001.mp4")
                   .replace("clip02.mp4", "clip0002.mp4")
                for path in item["segment_outputs"]
            ]
            missing = [
                path for path in item["segment_outputs"]
                if not (BUNDLE / path).is_file()
            ]
            if missing:
                raise SystemExit(f"missing corrected segment outputs: {missing}")
            clips.append(item)
        queue.update_clips(record["job_id"], clips)
        repaired = queue.get(record["job_id"]).clips
    finally:
        queue.close()
    payload = {
        "job_id": record["job_id"],
        "repaired_segments": [
            item["segment_outputs"] for item in repaired
        ],
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
