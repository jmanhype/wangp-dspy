#!/usr/bin/env python3
"""Print the newest MP4 beneath a marathon output directory."""

from __future__ import annotations

import sys
from pathlib import Path


def latest_output(root: Path) -> Path | None:
    candidates = [path for path in root.glob("*.mp4") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: latest-output.py OUTPUT_DIRECTORY", file=sys.stderr)
        return 2
    output = latest_output(Path(sys.argv[1]))
    if output is None:
        print("no completed MP4 found", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
