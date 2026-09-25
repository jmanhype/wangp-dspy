#!/usr/bin/env python3
"""Bind completed WD-dmf2 outputs and pending review evidence in the queue."""
from __future__ import annotations

import json
from pathlib import Path

from services.jobs.queue import JobQueue


BUNDLE = Path(__file__).resolve().parent
MODES = ("prompt", "audio", "music_video", "screenplay")


def main() -> int:
    record = json.loads(
        (BUNDLE / "queue-record.json").read_text(encoding="utf-8")
    )
    queue = JobQueue(BUNDLE / "queue.db")
    try:
        for index, mode in enumerate(MODES, start=1):
            queue.update_clip(
                record["job_id"],
                index,
                status="done",
                log=f"wd-dmf2-{mode}.native.log",
                mp4=f"outputs/wd_dmf2_{mode}_composition.mp4",
                qc_verdict={
                    "verdict": "NEEDS REVIEW",
                    "path": "objective-gates.json",
                    "reviewer_decision": "pending",
                },
                lane="director_composition",
            )
        queue.set_state(record["job_id"], "done")
        job = queue.get(record["job_id"])
        payload = {
            "job_id": job.job_id,
            "state": job.state,
            "clips": [
                {
                    "clip_index": clip["clip_index"],
                    "status": clip["status"],
                    "mp4": clip["mp4"],
                    "reviewer_decision": clip["qc_verdict"]["reviewer_decision"],
                }
                for clip in job.clips
            ],
        }
    finally:
        queue.close()
    (BUNDLE / "queue-final-state.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
