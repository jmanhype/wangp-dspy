#!/usr/bin/env python3
"""Summarize the raw live WD-isg9 model hash probe without mutating it."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    raw = (ROOT / "preflight-model-hash-rerun.txt").read_text(encoding="utf-8")
    assets = json.loads((ROOT / "model-assets.json").read_text(encoding="utf-8"))["assets"]
    expected = {item["destination"]: item for item in assets}
    raw_hashes = {
        path: digest for digest, path in (
            line.split("  ", 1) for line in raw.splitlines() if line.startswith(("30ff", "4550", "37dd", "4df8"))
        )
    }
    stat_lines = [line for line in raw.splitlines() if line.startswith("/home/straughter/Wan2GP/ckpts/") and "|" in line]
    stats = {}
    for line in stat_lines:
        path, size, mtime = line.split("|", 2)
        stats[path] = {"size_bytes": int(size), "mtime": mtime.strip()}
    rows = []
    for asset in assets:
        destination = asset["destination"]
        observed = raw_hashes.get(destination)
        rows.append({
            **asset,
            "observed_sha256": observed,
            "observed_size_bytes": stats.get(destination, {}).get("size_bytes"),
            "observed_mtime": stats.get(destination, {}).get("mtime"),
            "live_hash_match": observed == asset["sha256"],
            "live_size_match": stats.get(destination, {}).get("size_bytes") == asset["size_bytes"],
        })
    ok_lines = [line for line in raw.splitlines() if line.endswith(": OK")]
    disk_line = next(line for line in raw.splitlines() if line.startswith("/dev/"))
    disk_fields = disk_line.split()
    gpu_line = next(line for line in raw.splitlines() if line.startswith("NVIDIA GeForce RTX 3090,"))
    gpu_fields = [field.strip() for field in gpu_line.split(",")]
    health_line = next(line for line in raw.splitlines() if line.startswith('{"model_loaded"'))
    payload = {
        "schema_version": "wangp-dspy.wd-isg9.live-model-hash-probe/v1",
        "probe_timestamp_utc": raw.splitlines()[0],
        "host": raw.splitlines()[1],
        "sha256sum_check_ok_count": len(ok_lines),
        "all_expected_assets_checked": len(ok_lines) == len(expected),
        "all_live_hashes_match": bool(rows) and all(row["live_hash_match"] for row in rows),
        "all_live_sizes_match": bool(rows) and all(row["live_size_match"] for row in rows),
        "disk": {
            "filesystem": disk_fields[0],
            "total_bytes": int(disk_fields[1]),
            "used_bytes": int(disk_fields[2]),
            "available_bytes": int(disk_fields[3]),
        },
        "gpu": {
            "name": gpu_fields[0],
            "memory_total_mib": int(gpu_fields[1].removesuffix(" MiB")),
            "memory_used_mib": int(gpu_fields[2].removesuffix(" MiB")),
            "memory_free_mib": int(gpu_fields[3].removesuffix(" MiB")),
        },
        "qc_health": json.loads(health_line),
        "assets": rows,
        "raw_evidence": "preflight-model-hash-rerun.txt",
    }
    (ROOT / "preflight-model-hash-summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "checked": len(ok_lines),
        "all_hashes_match": payload["all_live_hashes_match"],
        "all_sizes_match": payload["all_live_sizes_match"],
    }, sort_keys=True))
    return 0 if payload["all_expected_assets_checked"] and payload["all_live_hashes_match"] and payload["all_live_sizes_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
