#!/usr/bin/env python3
"""check_common_actions.py — common-actions gate CLI.

Check action/shot text against the RISKY pattern registry before
submitting to the video model. Deterministic pattern matching; NO LLM,
NO network. Pattern: scripts/check_names.py.

Usage:
  python scripts/check_common_actions.py <file-or-text>

Exit codes: 0 = clean (only common actions), 1 = risky-action
violations, 2 = usage/input error (incl. empty-text loud skip).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from gates.common_actions import (  # noqa: E402
    ActionGateError, check_common_actions,
)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Reject action text containing patterns that "
                    "produce mush in video models (common-actions "
                    "doctrine, docs/extraction/shuohao-skills/"
                    "pass-methodology-outline.md section 4)")
    ap.add_argument("target",
                    help="action text, or a path to a text file")
    args = ap.parse_args(argv)

    p = Path(args.target)
    if p.is_file():
        text = p.read_text(encoding="utf-8")
    else:
        text = args.target

    try:
        violations = check_common_actions(text)
    except ActionGateError as exc:
        print(f"SKIP (loud): {exc}", file=sys.stderr)
        return 2

    if not violations:
        print("OK: no risky action patterns — text uses actions the "
              "model has seen millions of times")
        return 0
    for v in violations:
        print(f"VIOLATION: [{v.category}] {v.matched_text!r} "
              f"(pattern {v.id}) at char {v.span[0]} — {v.id}")
    print(f"\n{len(violations)} risky-action pattern(s) — the judgment "
          "test is 'is this action common in real-life video?' "
          "(docs/common-actions.md).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
