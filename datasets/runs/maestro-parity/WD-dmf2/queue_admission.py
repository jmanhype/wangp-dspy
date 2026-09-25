#!/usr/bin/env python3
"""Prove the real WD-dmf2 composition job is admitted by the selector."""
from __future__ import annotations

import json
from pathlib import Path

from services.jobs.queue import JobQueue, next_admissible


BUNDLE = Path(__file__).resolve().parent


def main() -> int:
    record = json.loads(
        (BUNDLE / "queue-record.json").read_text(encoding="utf-8")
    )
    queue = JobQueue(BUNDLE / "queue.db")
    try:
        selected = next_admissible(queue)
        payload = {
            "job_id": record["job_id"],
            "selected_job": selected,
            "admission_state": (
                "admitted" if selected == record["job_id"] else "not_admitted"
            ),
            "selector": "services.jobs.queue.JobQueue.next_admissible",
        }
    finally:
        queue.close()
    (BUNDLE / "queue-admission.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["admission_state"] == "admitted" else 2


if __name__ == "__main__":
    raise SystemExit(main())
