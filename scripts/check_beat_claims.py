#!/usr/bin/env python3
"""check_beat_claims.py — beat-grid/lyric-boundary claim gate CLI.

Replay a cut list's CLAIM fields against the audio beat grid before
render: every cut must land on its claimed lyric-phrase boundary
within tolerance. Deterministic replay; NO LLM, NO network.

Pattern: scripts/check_names.py.

Usage:
  python scripts/check_beat_claims.py <grid.json> <cuts.json>
  python scripts/check_beat_claims.py <grid.json> -   # cuts on stdin

JSON shapes (docs/beat-claims.md):
  grid: {"phrases": [{"id","text","start","end"}, ...]}
  cuts: {"cuts": [{"cut_id","time","claim":{"phrase_id","offset"
          [,"tolerance"]}}, ...]}

Exit codes: 0 = all cuts PASS, 1 = violations (per-cut FAIL report),
2 = usage/input error (incl. empty grid / empty cuts — loud skip).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from gates.beat_claims import (  # noqa: E402
    BeatClaimValidationError, load_cuts_json, load_grid_json,
    validate_beat_claims,
)

DEFAULT_TOLERANCE = 0.05


def _read(path: str) -> dict:
    if path == "-":
        return json.loads(sys.stdin.read())
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Replay cut CLAIM fields against the beat grid "
                    "(hookBeat doctrine, "
                    "docs/extraction/shuohao-skills/"
                    "changelog-design-rationale.md section C)")
    ap.add_argument("grid", help="beat-grid JSON file")
    ap.add_argument("cuts", help="cut-list JSON file, or '-' for stdin")
    ap.add_argument("--tolerance", type=float,
                    default=DEFAULT_TOLERANCE,
                    help=f"default per-cut tolerance in seconds "
                         f"(default {DEFAULT_TOLERANCE})")
    args = ap.parse_args(argv)

    try:
        grid = load_grid_json(_read(args.grid))
        cuts = load_cuts_json(_read(args.cuts))
    except (FileNotFoundError, json.JSONDecodeError, KeyError,
            TypeError, ValueError) as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        violations = validate_beat_claims(
            grid, cuts, default_tolerance=args.tolerance)
    except BeatClaimValidationError as exc:
        print(f"SKIP (loud): {exc}", file=sys.stderr)
        return 2

    bad = {x.split("'")[1] for x in violations if "'" in x}
    for c in cuts:
        status = "FAIL" if c.cut_id in bad else "PASS"
        claim = (f"{c.claim.phrase_id}+{c.claim.offset}s"
                 if c.claim else "NO CLAIM")
        print(f"{status}  {c.cut_id}  t={c.time}s  claim={claim}")
    for x in violations:
        print(f"\nVIOLATION: {x}", file=sys.stderr)
    if violations:
        print(f"\n{len(violations)} beat-claim violation(s) — cuts "
              "must land on their claimed lyric boundaries "
              "(docs/beat-claims.md).", file=sys.stderr)
        return 1
    print("OK: all cuts land on their claimed phrase boundaries "
          f"({len(cuts)} cuts, tolerance {args.tolerance}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
