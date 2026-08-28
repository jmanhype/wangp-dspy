#!/usr/bin/env python3
"""check_provenance.py — provenance-tier gate CLI (WD-oyti).

Check an identity claim (inline text or a file) against the
inferred-marker convention: every claim carries either a canon
citation OR exactly one `(inferred)` marker; no unmarked middle
ground, no double-marking. Also checks rendered prompts are
marker-free (the brief_to_prompt seam contract). Deterministic string
checks; NO LLM, NO network.

Usage:
  python scripts/check_provenance.py <file-or-text> [--cited]
      --claim    check an identity claim (default mode)
      --prompt   check a rendered prompt is marker-free
      --cited    the claim carries a canon citation (then any marker
                 is a redundant double-tier violation)

Exit codes: 0 = clean, 1 = provenance violations, 2 = usage error.
Design source: docs/extraction/shuohao-skills/inferred-marker-convention.md
(schema + wiring: docs/entity-registry.md "Decision provenance" section).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from gates.provenance_gate import (  # noqa: E402
    check_prompt_fields, check_provenance_tier, ProvenanceGateError)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Reject identity claims without a provenance tier "
                    "(canon citation OR exactly one (inferred) marker) "
                    "and prompts carrying markers "
                    "(inferred-marker-convention.md)")
    ap.add_argument("target", help="identity claim / prompt text, or a path")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--claim", action="store_true",
                      help="target is an identity claim (default)")
    mode.add_argument("--prompt", action="store_true",
                      help="target is a rendered prompt (must be marker-free)")
    ap.add_argument("--cited", action="store_true",
                    help="claim carries a canon citation (markers then "
                         "violate as double-tier)")
    args = ap.parse_args(argv)

    p = Path(args.target)
    if p.is_file():
        text = p.read_text(encoding="utf-8")
    else:
        text = args.target

    if args.prompt:
        violations = check_prompt_fields(text)
    else:
        try:
            violations = check_provenance_tier(
                text, field="identity", has_canon_citation=args.cited)
        except ProvenanceGateError as exc:
            print(f"GATE ERROR: {exc}", file=sys.stderr)
            return 2

    if not violations:
        print("OK: provenance tiers consistent "
              "(inferred-marker-convention.md)")
        return 0
    for v in violations:
        print(f"VIOLATION [{v.field}]: {v.reason}")
    print(f"\n{len(violations)} provenance violation(s) — cite the canon "
          "or add exactly one (inferred) marker per item.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
