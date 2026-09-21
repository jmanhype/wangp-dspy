#!/usr/bin/env python3
"""Gzip all but the newest marathon output files."""

from __future__ import annotations

import gzip
import shutil
import sys
from pathlib import Path


def triage_outputs(root: Path, keep: int) -> list[Path]:
    outputs = sorted(
        (path for path in root.glob("*.mp4") if path.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    compressed: list[Path] = []
    for output in outputs[keep:]:
        destination = output.with_suffix(".mp4.gz")
        with output.open("rb") as source, gzip.open(
            destination, "wb", compresslevel=9
        ) as target:
            shutil.copyfileobj(source, target)
        output.unlink()
        compressed.append(destination)
    return compressed


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: triage-outputs.py OUTPUT_DIRECTORY KEEP", file=sys.stderr)
        return 2
    for destination in triage_outputs(Path(sys.argv[1]), int(sys.argv[2])):
        print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
