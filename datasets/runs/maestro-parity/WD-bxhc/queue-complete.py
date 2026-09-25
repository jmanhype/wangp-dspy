#!/usr/bin/env python3
"""Bind measured WD-bxhc artifacts to the durable completion queue."""
from __future__ import annotations

import json
from pathlib import Path

from services.jobs.queue import JobQueue


LOGS = {
    1: "vibevoice-custom.attempt-11.native.log",
    2: "chatterbox-speech.attempt-4.native.log",
    3: "character-operations.attempt-2.log",
    4: "character-operations.attempt-2.log",
    5: "character-operations.attempt-2.log",
    6: "character-operations.attempt-2.log",
    7: "character-operations.attempt-2.log",
    8: "character-operations.attempt-2.log",
    9: "character-operations.attempt-2.log",
    10: "character-operations.attempt-2.log",
    11: "character-media-generation.log",
}


def main() -> int:
    bundle = Path(__file__).resolve().parent
    record = json.loads((bundle / "queue-record.json").read_text(encoding="utf-8"))
    queue = JobQueue(bundle / "queue.db")
    try:
        job = queue.get(record["job_id"])
        for clip in job.clips:
            index = clip["clip_index"]
            queue.update_clip(
                record["job_id"], index, status="done", log=LOGS[index],
                mp4=clip["artifact"],
                qc_verdict={"verdict": "NEEDS REVIEW", "path": "objective-gates.json"},
            )
        for state in ("preflight", "rendering", "rendered_pending_qc", "qc", "done"):
            queue.set_state(record["job_id"], state)
        final = queue.get(record["job_id"])
    finally:
        queue.close()
    print(json.dumps({"job_id": final.job_id, "state": final.state, "clips": final.clips}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
