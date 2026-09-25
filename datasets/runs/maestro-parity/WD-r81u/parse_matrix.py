#!/usr/bin/env python3
"""Prove the five finishing rows and only reviewer-approved cell transitions."""
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
        match = re.match(
            r"^\| ([a-z_]+) \| (planned|unsupported|host_run_verified \([^|]+\)) \| "
            r"(planned|unsupported|host_run_verified \([^|]+\)) \| "
            r"(planned|unsupported|host_run_verified \([^|]+\)) \| "
            r"(planned|unsupported|host_run_verified \([^|]+\)) \|$", line)
        if match is None:
            continue
        result[match.group(1)] = [
            "host_run_verified" if match.group(index).startswith("host_run_verified ")
            else match.group(index)
            for index in range(2, 6)
        ]
    return result


APPROVED_TRANSITIONS = {
    ("ffmpeg", 0): "outputs/wd_r81u_ffmpeg_interpolation_x2.mp4",
    ("ffmpeg", 1): "outputs/wd_r81u_ffmpeg_spatial_x2.mp4",
    ("ffmpeg", 2): "outputs/wd_r81u_ffmpeg_film_grain.mp4",
    ("rife", 0): "outputs/wd_r81u_rife_interpolation_x2.mp4",
    ("real_esrgan", 1): "outputs/wd_r81u_real_esrgan_spatial_x2.mp4",
}


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
        "approved_transitions": [
            {"row": row, "cell_index": index, "evidence": evidence}
            for (row, index), evidence in APPROVED_TRANSITIONS.items()
        ],
        "off_diagonal_boundaries_unchanged": all(
            current[name][index] == "unsupported"
            for name in EXPECTED_ROWS
            for index, cell in enumerate(base[name])
            if cell == "unsupported"
        ),
        "planned_cells_flipped": len(APPROVED_TRANSITIONS),
        "reason": "reviewer_verdict is approved; only the five independently verified cells were promoted",
        "row_dispositions": evidence["row_dispositions"],
    }
    valid = (
        tuple(current) == EXPECTED_ROWS
        and all(len(cells) == 4 for cells in current.values())
        and all(
            current[row][index] == "host_run_verified"
            for row, index in APPROVED_TRANSITIONS
        )
        and {
            (row, index)
            for row, index, before, after in (
                (row, index, before, after)
                for row in EXPECTED_ROWS
                for index, (before, after) in enumerate(zip(base[row], current[row]))
            )
            if before != after
        } == set(APPROVED_TRANSITIONS)
    )
    (BUNDLE / "matrix-transition-check.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, sort_keys=True))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
