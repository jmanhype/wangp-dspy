#!/usr/bin/env python3
"""Create fresh immutable plans from the corrected clone references."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


BUNDLE = Path(__file__).resolve().parent
ROOT = BUNDLE.parents[3]
NAMES = ("vibevoice-clone-one", "vibevoice-clone-two")


def main() -> int:
    request_dir = BUNDLE / "planning" / "rework-requests"
    database_dir = BUNDLE / "planning" / "rework-databases"
    cli_dir = BUNDLE / "planning" / "rework-cli"
    request_dir.mkdir(parents=True, exist_ok=True)
    database_dir.mkdir(parents=True, exist_ok=True)
    cli_dir.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        payload = json.loads((BUNDLE / "planning" / "requests" / f"{name}.json").read_text())
        payload["output_path_planned"] = str(
            BUNDLE / "outputs" / "rework-targets" / f"{name}.wav"
        )
        request = request_dir / f"{name}.json"
        database = database_dir / f"{name}.db"
        cli = cli_dir / f"{name}.json"
        reconstruct = cli_dir / f"{name}.reconstruct.json"
        if request.exists() or database.exists() or cli.exists() or reconstruct.exists():
            raise RuntimeError(f"rework plan namespace is not fresh: {name}")
        request.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        commands = [
            [
                str(ROOT / ".venv" / "bin" / "wgp"), "voice", "clone",
                "--request", str(request), "--models", str(BUNDLE / "planning" / "models.json"),
                "--db", str(database), "--json",
            ],
            [
                str(ROOT / ".venv" / "bin" / "wgp"), "voice", "plan",
                "--reconstruct", "--db", str(database), "--json",
            ],
        ]
        outputs = []
        for command in commands:
            result = subprocess.run(
                command, cwd=BUNDLE, text=True, capture_output=True, check=False
            )
            if result.returncode != 0:
                raise RuntimeError(f"{command} failed: {result.stdout}{result.stderr}")
            outputs.append(result.stdout)
        cli.write_text(outputs[0], encoding="utf-8")
        reconstruct.write_text(outputs[1], encoding="utf-8")
        print(json.dumps({
            "name": name,
            "request": str(request.relative_to(BUNDLE)),
            "database": str(database.relative_to(BUNDLE)),
            "reconstruct_all_match": json.loads(outputs[1])["all_match"],
            "hidden_mutation": json.loads(outputs[1])["hidden_mutation"],
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
