#!/usr/bin/env python3
"""Record WD-dmf2 host preflight without mutating operator services."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


def output(argv: list[str]) -> str:
    return subprocess.run(
        argv, text=True, capture_output=True, check=True
    ).stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    df_fields = output(["df", "-B1", "/"]).splitlines()[-1].split()
    free_bytes = int(df_fields[3])
    min_free_bytes = 15_000_000_000
    llama_processes = output(["pgrep", "-af", "llama-server"])
    health = subprocess.run(
        ["curl", "-fsS", "--max-time", "10", "http://127.0.0.1:8000/health"],
        text=True, capture_output=True, check=False,
    )
    whisper = Path("/home/straughter/.cache/whisper/small.pt")
    syncnet = Path("/home/straughter/models/syncnet_v2/syncnet_v2.model")
    payload = {
        "schema_version": "wangp-dspy.director-host-preflight/v1",
        "host": output(["hostname"]),
        "user": output(["id", "-un"]),
        "wgp_root": str(Path("/home/straughter/Wan2GP").resolve()),
        "disk_free_bytes": free_bytes,
        "min_free_bytes": min_free_bytes,
        "disk_floor_pass": free_bytes >= min_free_bytes,
        "llama_server_running": bool(llama_processes),
        "llama_server_processes": llama_processes.splitlines(),
        "llama_server_health": {
            "exit_code": health.returncode,
            "stdout": health.stdout.strip(),
        },
        "gpu": output([
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.used,utilization.gpu",
            "--format=csv,noheader",
        ]),
        "whisper_small": {
            "path": str(whisper),
            "present": whisper.is_file(),
            "size_bytes": whisper.stat().st_size if whisper.is_file() else None,
            "sha256": sha256(whisper) if whisper.is_file() else None,
        },
        "syncnet_v2": {
            "path": str(syncnet),
            "present": syncnet.is_file(),
            "size_bytes": syncnet.stat().st_size if syncnet.is_file() else None,
            "sha256": sha256(syncnet) if syncnet.is_file() else None,
        },
        "operator_service_mutation": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
