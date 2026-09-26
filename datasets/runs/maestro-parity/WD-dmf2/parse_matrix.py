#!/usr/bin/env python3
"""Check the director matrix identities and WD-dmf2 no-flip dispositions."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
DOC = ROOT / "docs/director-capabilities.md"
BUNDLE = Path(__file__).resolve().parent
EXPECTED = (
    "Deterministic ordered multi-clip plan",
    "Per-clip prompt and six-frame overlap",
    "Explicit continuity state and transitions",
    "Beat-aware measured window mapping",
    "Exact/window pacing preservation",
    "Auto/manual review checkpoints",
    "Immutable non-executable queue records",
    "Authorized prompt-only enhancement",
    "Seed-based hash reconstruction",
    "Generated clip, audio, or finished film",
)


def main() -> int:
    lines = DOC.read_text(encoding="utf-8").splitlines()
    rows = {}
    for line in lines:
        match = re.match(r"^\| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$", line)
        if not match:
            continue
        capability = match.group(1).strip()
        if capability in EXPECTED:
            rows[capability] = tuple(match.group(index).strip() for index in range(2, 6))
    dispositions = json.loads(
        (BUNDLE / "row-dispositions.json").read_text(encoding="utf-8")
    )
    planned_first_nine = all(
        all(value in {"planned", "not applicable"}
            for value in item["cells"].values())
        and "planned" in item["cells"].values()
        for item in dispositions["rows"]
    )
    payload = {
        "schema_version": "wangp-dspy.director-matrix-transition-check/v1",
        "document": str(DOC.relative_to(ROOT)),
        "row_count": len(rows),
        "expected_row_count": len(EXPECTED),
        "row_identities_match": tuple(rows) == EXPECTED,
        "first_nine_all_unchanged_planned": planned_first_nine,
        "generated_media_row_unchanged": (
            dispositions["generated_media_row"]["disposition"]
            == "unchanged_unsupported_in_this_lane"
        ),
        "rows": [
            {"capability": capability, "cells": values}
            for capability, values in rows.items()
        ],
        "passed": (
            len(rows) == len(EXPECTED)
            and tuple(rows) == EXPECTED
            and planned_first_nine
            and dispositions["generated_media_row"]["disposition"]
            == "unchanged_unsupported_in_this_lane"
        ),
    }
    destination = BUNDLE / "matrix-transition-check.json"
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
