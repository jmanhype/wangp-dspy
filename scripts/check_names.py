#!/usr/bin/env python3
"""check_names.py — no-proper-nouns gate CLI.

Check a prompt (inline text or a file) against the SGFLIX entity
registry before submitting it to any image/video model. Deterministic
registry matching; NO LLM, NO network.

Usage:
  python scripts/check_names.py <file-or-text> [--registry PATH]

Exit codes: 0 = clean (or warnings), 1 = registry-name violations,
2 = usage/registry error. Default registry:
datasets/entity-registry.json (schema: docs/entity-registry.md).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from gates.no_names_gate import check_no_proper_nouns, load_registry

DEFAULT_REGISTRY = REPO / "datasets" / "entity-registry.json"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Reject prompts containing registry entity names "
                    "(no-names doctrine, docs/extraction/shuohao-skills/"
                    "no-names-doctrine.md)")
    ap.add_argument("target",
                    help="prompt text, or a path to a text/JSON file")
    ap.add_argument("--registry", default=str(DEFAULT_REGISTRY),
                    help=f"entity registry JSON (default: {DEFAULT_REGISTRY})")
    args = ap.parse_args(argv)

    try:
        registry = load_registry(args.registry)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"REGISTRY ERROR: {exc}", file=sys.stderr)
        return 2

    p = Path(args.target)
    if p.is_file():
        text = p.read_text(encoding="utf-8")
    else:
        text = args.target

    violations = check_no_proper_nouns(text, registry)
    if not violations:
        print("OK: no registry names found "
              f"({len(registry.get('entities', []))} entities checked)")
        return 0
    for v in violations:
        print(f"VIOLATION: {v} at char {v.span[0]}")
    print(f"\n{len(violations)} proper-noun violation(s) — describe the "
          "entity instead of naming it (no-names-doctrine.md).",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
