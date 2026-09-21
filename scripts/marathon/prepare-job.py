#!/usr/bin/env python3
"""Apply one marathon job to the configured render settings file."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def prepare_job(job_path: Path, settings_path: Path) -> None:
    job: dict[str, Any] = json.loads(job_path.read_text(encoding="utf-8"))
    settings: dict[str, Any] = json.loads(
        settings_path.read_text(encoding="utf-8")
    )
    settings.update(job)
    settings_path.write_text(
        json.dumps(settings, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: prepare-job.py NEXT_JOB SETTINGS", file=sys.stderr)
        return 2
    prepare_job(Path(sys.argv[1]), Path(sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
