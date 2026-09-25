#!/usr/bin/env python3
"""Advance the real WD-r81u queue using its public state machine."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.jobs.queue import JobQueue


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("state", choices=("preflight", "rendering", "rendered_pending_qc", "qc", "done"))
    args = parser.parse_args()
    bundle = Path(__file__).resolve().parent
    record = json.loads((bundle / "queue-record.json").read_text(encoding="utf-8"))
    queue = JobQueue(bundle / "queue.db")
    try:
        queue.set_state(record["job_id"], args.state)
        state = queue.get(record["job_id"]).state
    finally:
        queue.close()
    print(json.dumps({"job_id": record["job_id"], "state": state}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
