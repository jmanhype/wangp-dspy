#!/usr/bin/env python3
"""check_job_config.py — WanGPJobConfig validator CLI.

Validate a flat WanGP job settings JSON against the five absorbed
rules (force_fps str typing, 96f floor, 5+17k snap, flat JSON,
line-anchored separator). Deterministic; NO LLM, NO network.

Usage:
  python scripts/check_job_config.py <job.json>

Exit codes: 0 = valid, 1 = validation violations, 2 = usage/input
error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from predict.job_config import (  # noqa: E402
    WanGPJobConfig, JobConfigError, validate_job_config,
)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Validate a WanGP job settings JSON "
                    "(WD-l5bx single authority)")
    ap.add_argument("job", help="path to job settings JSON")
    args = ap.parse_args(argv)

    try:
        doc = json.loads(Path(args.job).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 2
    if not isinstance(doc, dict):
        print("INPUT ERROR: job settings must be a JSON object",
              file=sys.stderr)
        return 2

    try:
        cfg = WanGPJobConfig(**doc)
    except TypeError as exc:
        print(f"INPUT ERROR: unknown/missing fields: {exc}",
              file=sys.stderr)
        return 2
    except JobConfigError as exc:
        print(f"VIOLATION: {exc}", file=sys.stderr)
        return 1

    violations = validate_job_config(cfg)
    if violations:
        for v in violations:
            print(f"VIOLATION: {v}", file=sys.stderr)
        return 1
    print(f"OK: valid WanGP job config "
          f"({cfg.frames_per_shot}f @ {cfg.force_fps}fps, "
          f"effective {__import__('predict.job_config', fromlist=['normalize_frame_count']).normalize_frame_count(cfg.frames_per_shot)}f on the H3 grid)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
