#!/usr/bin/env python3
"""check_diarization.py — S2 diarization timeline CLI (WD-j9nx/S2).

Thin wrapper over predict.diarization: validates an out-of-repo
diarization JSON timeline and optionally renders the <d>Name</d>
attribution blocks. No new logic lives here.

Usage:
    python scripts/check_diarization.py FILE [--convert]

Exit codes:
    0  valid timeline; summary on stdout (n speakers, n segments, duration)
    1  invalid timeline (typed rule error on stderr) / missing file / bad JSON
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from predict.diarization import (  # noqa: E402
    DiarizationError, diarization_to_speaker_blocks, render_attribution,
    validate_diarization,
)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Validate a diarization timeline")
    ap.add_argument("file", help="path to the diarization JSON file")
    ap.add_argument("--convert", action="store_true",
                    help="also print rendered <d>Name</d> attribution lines")
    args = ap.parse_args(argv)

    path = Path(args.file)
    if not path.is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON in {path}: {e}", file=sys.stderr)
        return 1

    try:
        validate_diarization(doc)
    except DiarizationError as e:
        print(str(e), file=sys.stderr)
        return 1

    print(f"OK: {len(doc['speakers'])} speakers, "
          f"{len(doc['segments'])} segments, {doc['duration_sec']}s")
    if args.convert:
        blocks = diarization_to_speaker_blocks(doc)
        print(render_attribution(blocks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
