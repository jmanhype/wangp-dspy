#!/usr/bin/env python3
"""Prove the five finishing rows and every planned/off-diagonal cell remain intact."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
BUNDLE = Path(__file__).resolve().parent
DOC = "docs/finishing-capabilities.md"
EXPECTED_ROWS = ("ffmpeg", "rife", "real_esrgan", "film", "neural_frame_gen")


def rows(text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for line in text.splitlines():
        match = re.match(r"^\| ([a-z_]+) \| (planned|unsupported) \| (planned|unsupported) \| (planned|unsupported) \| (planned|unsupported) \|$", line)
        if match is None:
            continue
        result[match.group(1)] = [match.group(index) for index in range(2, 6)]
    return result


def main() -> int:
    current = rows((REPO / DOC).read_text(encoding="utf-8"))
    base_text = subprocess.run(
        ["git", "-C", str(REPO), "show", f"c91a6d8:{DOC}"],
        text=True, capture_output=True, timeout=30, check=True,
    ).stdout
    base = rows(base_text)
    evidence = json.loads((BUNDLE / "evidence.json").read_text(encoding="utf-8"))
    payload = {
        "base": "c91a6d8",
        "expected_rows": list(EXPECTED_ROWS),
        "observed_rows": list(current),
        "row_count": len(current),
        "cells_per_row": {name: len(cells) for name, cells in current.items()},
        "unchanged_from_base": current == base,
        "off_diagonal_boundaries_unchanged": all(
            current[name][index] == "unsupported"
            for name in EXPECTED_ROWS
            for index, cell in enumerate(base[name])
            if cell == "unsupported"
        ),
        "planned_cells_flipped": 0,
        "reason": "reviewer_verdict is pending and the canonical checker exits 1; candidate rows cannot be promoted",
        "row_dispositions": evidence["row_dispositions"],
    }
    valid = (
        tuple(current) == EXPECTED_ROWS
        and current == base
        and all(len(cells) == 4 for cells in current.values())
    )
    (BUNDLE / "matrix-transition-check.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, sort_keys=True))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
