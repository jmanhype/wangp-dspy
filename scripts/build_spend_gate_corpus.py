#!/usr/bin/env python3
"""Build, verify, and replay the committed spend-gate corpus."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from training.spend_gate import build_corpus, verify_artifact, write_corpus
from training.spend_gate_replay import replay_baselines


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__, epilog=(
        "Fresh-checkout replay: python scripts/build_spend_gate_corpus.py "
        "--repository-root . --evidence-mode tracked --output-dir "
        "datasets/spend-gate/v1 --replay --verify-artifact"))
    result.add_argument("--repository-root", type=Path, default=Path(".")); result.add_argument("--evidence-mode", choices=("tracked", "all-local"), default="tracked")
    result.add_argument("--output-dir", type=Path, required=True)
    result.add_argument("--replay", action="store_true"); result.add_argument("--verify-artifact", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root, output = args.repository_root.resolve(), args.output_dir.resolve()
    existing = output / "corpus.jsonl"
    if not (args.verify_artifact and args.evidence_mode == "tracked" and existing.exists()):
        corpus = build_corpus(root, evidence_mode=args.evidence_mode)
        write_corpus(corpus, output)
    manifest = verify_artifact(output)
    if args.replay:
        metrics, report = replay_baselines(output / "corpus.jsonl").write(output); print(f"replay={metrics} report={report}")
    print(f"manifest={output / 'manifest.json'} rows={manifest['row_count']} mode={manifest['evidence_mode']}"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
