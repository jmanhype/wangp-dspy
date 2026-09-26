#!/usr/bin/env python3
"""Summarize raw live WD-9t9o model/source hash evidence."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    raw = (ROOT / "preflight-model-hash.txt").read_text(encoding="utf-8")
    assets = json.loads((ROOT / "model-assets.json").read_text(encoding="utf-8"))["assets"]
    hash_prefixes = ("30ff", "4550", "37dd", "4df8", "6bec")
    raw_hashes = {
        path: digest for digest, path in (
            line.split("  ", 1) for line in raw.splitlines()
            if line.startswith(hash_prefixes) and "  /home/" in line
        )
    }
    stat_rows = [line for line in raw.splitlines() if line.startswith("/home/straughter/Wan2GP/") and "|" in line]
    stats = {}
    for line in stat_rows:
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
    source_path = "/home/straughter/Wan2GP/wd-9t9o/inputs/source.mp4"
    expected_source = "6becf70d98be579159b0e3ed6b212517ee78c7a1cc01906588c3ad6f0dfb8beb"
    ok_lines = [line for line in raw.splitlines() if line.endswith(": OK")]
    disk_line = next(line for line in raw.splitlines() if line.startswith("/dev/"))
    disk = disk_line.split()
    gpu_line = next(line for line in raw.splitlines() if line.startswith("NVIDIA GeForce RTX 3090,"))
    gpu = [item.strip() for item in gpu_line.split(",")]
    health_line = next(line for line in raw.splitlines() if line.startswith('{"model_loaded"'))
    payload = {
        "schema_version": "wangp-dspy.wd-9t9o.live-hash-preflight/v1",
        "probe_timestamp_utc": raw.splitlines()[0],
        "host": raw.splitlines()[1],
        "model_check_ok_count": len(ok_lines),
        "all_model_hashes_match": bool(rows) and all(row["live_hash_match"] for row in rows),
        "all_model_sizes_match": bool(rows) and all(row["live_size_match"] for row in rows),
        "source": {
            "path": source_path,
            "expected_sha256": expected_source,
            "observed_sha256": raw_hashes.get(source_path),
            "observed_size_bytes": stats.get(source_path, {}).get("size_bytes"),
            "observed_mtime": stats.get(source_path, {}).get("mtime"),
            "hash_match": raw_hashes.get(source_path) == expected_source,
        },
        "assets": rows,
        "disk": {
            "filesystem": disk[0],
            "total_bytes": int(disk[1]),
            "used_bytes": int(disk[2]),
            "available_bytes": int(disk[3]),
        },
        "gpu": {
            "name": gpu[0],
            "memory_total_mib": int(gpu[1].removesuffix(" MiB")),
            "memory_used_mib": int(gpu[2].removesuffix(" MiB")),
            "memory_free_mib": int(gpu[3].removesuffix(" MiB")),
        },
        "qc_health": json.loads(health_line),
        "raw_evidence": "preflight-model-hash.txt",
    }
    (ROOT / "preflight-model-hash-summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    passed = (
        len(ok_lines) == len(assets)
        and payload["all_model_hashes_match"]
        and payload["all_model_sizes_match"]
        and payload["source"]["hash_match"]
    )
    print(json.dumps({"model_checks": len(ok_lines), "source_match": payload["source"]["hash_match"], "passed": passed}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
