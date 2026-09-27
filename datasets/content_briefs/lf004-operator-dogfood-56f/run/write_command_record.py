#!/usr/bin/env python3
"""Write the deterministic command record for an LF004 recovery launcher run."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def build_payload(root: Path) -> dict[str, Any]:
    """Build the same launcher command record previously embedded in Bash."""
    base = root / "datasets/content_briefs/lf004-operator-dogfood-56f"
    source = root / "datasets/content_briefs/lf004-operator-dogfood"
    command = [str(base / "run/recover_once.py"), "run-film"]
    expanded = {
        "script": str(base / "run/script.txt"),
        "plates": str(source / "plates"),
        "characters": "Tess:S1:... Rho:S2:...",
        "db": "datasets/lf004-operator-dogfood-56f-recovery-20260921.jobs.db",
        "run_ledger": "datasets/lf004-operator-dogfood-56f-recovery-20260921.run_ledger.json",
        "duration_s": [2.3333333333333335] * 4,
        "audio": [
            str(root / "datasets/runs/provenance/lf003-vibevoice-audition-20260917/audio/tess.prepared.wav"),
            str(root / "datasets/runs/provenance/lf003-vibevoice-rho-strong-20260918/audio/rho.prepared.wav"),
            str(root / "datasets/runs/provenance/lf003-four-cut-fullgate-20260919/audio/tess-cut3.prepared.wav"),
            str(root / "datasets/runs/provenance/lf003-four-cut-fullgate-20260919/audio/rho-cut4.prepared.wav"),
        ],
    }
    verification_path = root / "datasets/runs/provenance/lf004-operator-dogfood-56f-recovery-20260921/input-verification.json"
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    return {
        "schema_version": 1,
        "execution_count": 1,
        "command": command,
        "expanded_run_film_inputs": expanded,
        "input_verification": verification,
        "environment": {
            key: value for key, value in os.environ.items() if key.startswith("WANGP_")
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    payload = build_payload(args.root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
