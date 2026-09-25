#!/usr/bin/env python3
"""Lane-specific coexistence preflight for the operator-reserved judge."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


MODELS = json.loads(Path("/tmp/wd-bxhc-selected-models.json").read_text(encoding="utf-8"))


def run(argv: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, text=True, capture_output=True, check=False, timeout=timeout)


def main() -> int:
    model_results = []
    for item in MODELS:
        result = run(["sha256sum", item["remote_path"]])
        actual = result.stdout.split()[0] if result.stdout.split() else None
        model_results.append({
            "path": item["remote_path"], "expected": item["sha256"], "actual": actual,
            "passed": result.returncode == 0 and actual == item["sha256"],
        })
    disk_raw = run(["df", "-B1", "--output=avail", "/"]).stdout.strip().splitlines()[-1].strip()
    disk_free = int(disk_raw)
    gpu_raw = run([
        "nvidia-smi", "--query-gpu=memory.total,memory.used,memory.free",
        "--format=csv,noheader,nounits",
    ]).stdout.strip()
    total, used, free = (int(value.strip()) for value in gpu_raw.split(","))
    compute = run([
        "nvidia-smi", "--query-compute-apps=pid,used_memory,process_name",
        "--format=csv,noheader,nounits",
    ]).stdout.strip()
    occupants = [line.strip() for line in compute.splitlines() if line.strip()]
    reserved_judge = len(occupants) == 1 and "llama-server" in occupants[0]
    health = run(["curl", "-fsS", "-m", "30", "http://localhost:8000/health"])
    checks = {
        "models": all(item["passed"] for item in model_results),
        "disk_headroom": disk_free >= 15 * 1024**3,
        "operator_judge_only_and_enough_free_vram": reserved_judge and free >= 4096,
        "qc_available": health.returncode == 0 and "ok" in health.stdout,
    }
    payload = {
        "schema": "wangp-dspy.wd-bxhc.coexistence-preflight/v1",
        "passed": all(checks.values()),
        "checks": checks,
        "models": model_results,
        "disk_free_bytes": disk_free,
        "min_free_bytes": 15 * 1024**3,
        "gpu": {"total_mib": total, "used_mib": used, "free_mib": free},
        "compute_apps": occupants,
        "qc_http_status_body": health.stdout.strip(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
