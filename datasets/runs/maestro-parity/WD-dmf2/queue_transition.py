#!/usr/bin/env python3
"""Advance the real WD-dmf2 queue through its public state machine."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.jobs.queue import JobQueue


BUNDLE = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "state",
        choices=(
            "preflight", "rendering", "rendered_pending_qc", "qc", "done"
        ),
    )
    arguments = parser.parse_args()
    record = json.loads(
        (BUNDLE / "queue-record.json").read_text(encoding="utf-8")
    )
    queue = JobQueue(BUNDLE / "queue.db")
    try:
        queue.set_state(record["job_id"], arguments.state)
        state = queue.get(record["job_id"]).state
    finally:
        queue.close()
    payload = {"job_id": record["job_id"], "state": state}
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
