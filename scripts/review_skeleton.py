#!/usr/bin/env python3
"""WD-gq8y — pretty-print a round-1 skeleton for HUMAN review.

Renders the three sign-off questions explicitly (which lines cut /
which people merged / where the majors land) so the user can approve
or reject before any expensive stage runs.

Usage:
    python -m scripts.review_skeleton <skeleton.json>

Zero-model: reads a JSON file, prints. No LLM, no network.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from predict.skeleton import (  # noqa: E402
    Cut, Merge, PayoffPlacement, Signoff, Skeleton,
    render_skeleton_for_review, validate_skeleton,
)


def load_skeleton(path: str) -> Skeleton:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    so = d.get("signoff")
    return Skeleton(
        skeleton_id=d["skeleton_id"],
        cuts=[Cut(**c) for c in d["cuts"]],
        merges=[Merge(**m) for m in d["merges"]],
        payoff=PayoffPlacement(**d["payoff"]),
        cut_note=d["cut_note"],
        merge_note=d["merge_note"],
        signoff=Signoff(**so) if so else None,
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="print a round-1 skeleton for sign-off review")
    ap.add_argument("skeleton", help="path to skeleton.json")
    a = ap.parse_args()

    skel = load_skeleton(a.skeleton)
    viol = validate_skeleton(skel)
    if viol:
        print("VALIDATION VIOLATIONS (round-1 is invalid):", file=sys.stderr)
        for x in viol:
            print(f"  - {x}", file=sys.stderr)
    print(render_skeleton_for_review(skel))
    if viol:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
