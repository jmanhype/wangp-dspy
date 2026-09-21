#!/usr/bin/env python3
"""Print a marathon job premise for logging."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def job_premise(path: Path) -> str:
    job = json.loads(path.read_text(encoding="utf-8"))
    return str(job.get("premise", "?"))


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: job-premise.py NEXT_JOB", file=sys.stderr)
        return 2
    print(job_premise(Path(sys.argv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
