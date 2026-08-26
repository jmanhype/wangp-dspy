#!/usr/bin/env python3
"""run_baseline.py — WD-oa4i STEP 2 baseline evaluator.

Loads the bank via metrics.qc_feedback.load_examples, evaluates the
validation split with qc_feedback_metric, and writes
metrics/baseline_score.json: {score, n_val, timestamp_utc, git_head,
story}. Zero optimizer imports — plain dspy-free scoring path (the
metric itself needs dspy only for its Prediction type; the program
level used here returns a plain float).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from metrics.qc_feedback import load_examples, qc_feedback_metric  # noqa: E402


def _predict(example):
    """Baseline predictor. Default: a degenerate predictor that emits
    empty brief sections (floor baseline — the number the optimizer
    must beat).
    Tests may monkeypatch this with a real program."""
    class _Empty:
        subject = motion = camera = style = ""
        audio_direction = negatives = identity_lock = ""
    return _Empty()


def _git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
            text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def run_baseline(runs_dir: Path, out_path: Path,
                 split: float = 0.7) -> float:
    _, val = load_examples(runs_dir=str(runs_dir), split=split)
    if not val:
        raise ValueError(f"empty validation split from {runs_dir}")
    scores = [qc_feedback_metric(ex, _predict(ex))
              for ex in val]
    score = sum(scores) / len(scores)
    payload = {
        "score": score,
        "n_val": len(val),
        "timestamp_utc": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "git_head": _git_head(),
        "story": "WD-oa4i",
    }
    Path(out_path).write_text(json.dumps(payload, indent=2) + "\n")
    return score


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs-dir", default=str(REPO / "datasets" / "runs"))
    ap.add_argument("--out",
                    default=str(REPO / "metrics" / "baseline_score.json"))
    ap.add_argument("--dry-run", action="store_true",
                    help="evaluate and print, do not write the output file")
    args = ap.parse_args(argv)

    out = Path("/dev/null") if args.dry_run else Path(args.out)
    score = run_baseline(Path(args.runs_dir), out)
    print(f"baseline score: {score:.4f}")
    if not args.dry_run:
        print(Path(args.out).read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
