#!/usr/bin/env python3
"""check_qc_triage.py — VLM QC failure triage CLI (WD-rty2).

Classify a recorded QC failure event (JSON file) into exactly one
of {gate_false_positive, rule_violation, example_gap} using the
deterministic zero-model classifier (gates/qc_triage.py), or append
a classified record to the triage ledger. Three-tier ladder: gate /
rule / example ("误拦的门比没有门更糟——门的信用比数量重要").

Usage:
  python scripts/check_qc_triage.py <event.json>            classify
  python scripts/check_qc_triage.py <event.json> --record \
      --action gate-fixed [--story WD-xxx] [--ledger PATH]   classify + append
  python scripts/check_qc_triage.py --stats [PATH]          stats view

Exit codes: 0 = classified clean, 1 = typed rejection /
unclassifiable, 2 = usage error. Matches check_provenance.py.
Design source: docs/extraction/shuohao-skills/changelog-design-
rationale.md sections B + G; docs/qc-triage.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from gates.qc_triage import (  # noqa: E402
    ACTIONS, QCTriageError, classify_qc_failure, stats, write_record)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Deterministic QC-failure triage: gate false "
                    "positive / rule violation / example gap "
                    "(three-tier ladder, zero-model)")
    ap.add_argument("target", nargs="?",
                    help="path to a JSON event file")
    ap.add_argument("--record", action="store_true",
                    help="append the classified record to the ledger")
    ap.add_argument("--action", choices=ACTIONS,
                    help="the human decision taken (required with "
                         "--record)")
    ap.add_argument("--story", default="",
                    help="follow-up story id (with --record)")
    ap.add_argument("--ledger", default=str(
        REPO / "datasets" / "qc-triage-ledger.jsonl"),
        help="ledger path (default datasets/qc-triage-ledger.jsonl)")
    ap.add_argument("--stats", nargs="?", const="__known__",
                    default=None, metavar="PATH",
                    help="print the stats view instead of classifying")
    args = ap.parse_args(argv)

    if args.stats is not None:
        p = args.ledger if args.stats == "__known__" else args.stats
        s = stats(p, known_gates=(
            "render_qc_threshold", "language_gate", "provenance_gate"))
        print(json.dumps(s, indent=2, ensure_ascii=False))
        return 0

    if not args.target:
        ap.error("event file required (or use --stats)")
    p = Path(args.target)
    if not p.is_file():
        print(f"USAGE ERROR: no such file: {args.target}", file=sys.stderr)
        return 2
    try:
        event = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"USAGE ERROR: {args.target} is not valid JSON: {exc}",
              file=sys.stderr)
        return 2

    try:
        res = classify_qc_failure(event)
    except QCTriageError as exc:
        print(f"TRIAGE REJECTED [{exc.kind}]: {exc}", file=sys.stderr)
        return 1

    if args.record:
        if not args.action:
            print("USAGE ERROR: --record requires --action "
                  f"{ACTIONS}", file=sys.stderr)
            return 2
        rec = write_record(args.ledger, event,
                           action_taken=args.action,
                           follow_up_story=args.story)
        print(f"LEDGER APPENDED: {rec['classification']} "
              f"-> {args.ledger}")
    print(f"CLASSIFIED: {res.classification} "
          f"(confidence={res.confidence})")
    print(f"  reason: {res.reason}")
    print(f"  evidence: {res.evidence[:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
