#!/usr/bin/env python3
"""Download only the operator-approved WD-2gyw feasible-subset assets."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path("/home/straughter/Wan2GP")
MANIFEST = ROOT / "wd_2gyw_model_assets.json"
INPUT = ROOT / "wd_2gyw_download_input.txt"
REPORT = ROOT / "outputs/wd-2gyw/download-report.json"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    assets = json.loads(MANIFEST.read_text(encoding="utf-8"))["assets"]
    lines: list[str] = []
    for asset in assets:
        destination = Path(asset["destination"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        lines.extend((
            asset["source_url"],
            f"  dir={destination.parent}",
            f"  out={destination.name}",
            f"  checksum=sha-256={asset['sha256']}",
        ))
    INPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    command = [
        "aria2c",
        "--input-file=" + str(INPUT),
        "--continue=true",
        "--allow-overwrite=true",
        "--auto-file-renaming=false",
        "--check-integrity=true",
        "--max-connection-per-server=8",
        "--split=8",
        "--min-split-size=64M",
        "--concurrent-downloads=3",
        "--summary-interval=30",
        "--console-log-level=warn",
    ]
    completed = subprocess.run(command, check=False)
    entries = []
    for asset in assets:
        destination = Path(asset["destination"])
        observed_size = destination.stat().st_size if destination.is_file() else None
        observed_hash = file_sha256(destination) if destination.is_file() else None
        entries.append({
            **asset,
            "observed_size_bytes": observed_size,
            "observed_sha256": observed_hash,
            "verified": (
                observed_size == asset["size_bytes"]
                and observed_hash == asset["sha256"]
            ),
        })
    payload = {
        "schema_version": "wangp-dspy.model-assets-download-report/v1",
        "command": command,
        "exit_status": "succeeded" if completed.returncode == 0 and all(
            entry["verified"] for entry in entries
        ) else "failed",
        "aria2_exit_code": completed.returncode,
        "planned_bytes": sum(asset["size_bytes"] for asset in assets),
        "assets": entries,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "aria2_exit_code": completed.returncode,
        "report": str(REPORT),
        "verified": sum(entry["verified"] for entry in entries),
        "asset_count": len(entries),
    }, sort_keys=True))
    return 0 if completed.returncode == 0 and all(entry["verified"] for entry in entries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
