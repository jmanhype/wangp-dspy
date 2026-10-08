#!/usr/bin/env python3
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN = Path("/home/straughter/wd-28ac-run/phase-b-gate22-corrected-retry-final-cell-20261008")
AUTH = json.loads((RUN / "authorization.json").read_text(encoding="utf-8"))
STATE_PATH = RUN / "runtime-state.json"
STATE = json.loads(STATE_PATH.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(argv):
    result = subprocess.run(argv, text=True, capture_output=True, check=False)
    return {
        "argv": argv,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


asset_paths = {
    "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors": Path("/home/straughter/Wan2GP-story-WD-m7xw/loras/ltx2/ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors"),
    "ltx-2.3-22b-ic-lora-outpaint.safetensors": Path("/home/straughter/Wan2GP-story-WD-m7xw/loras/ltx2/ltx-2.3-22b-ic-lora-outpaint.safetensors"),
    "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors": Path("/home/straughter/Wan2GP-story-WD-m7xw/loras/ltx2/ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors"),
    "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors": Path("/home/straughter/Wan2GP-story-WD-m7xw/loras/ltx2/ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors"),
    "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors": Path("/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors"),
}
assets = {}
for name, path in asset_paths.items():
    assets[name] = {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "expected_sha256": AUTH["reauthorized_model_assets"][name],
        "match": sha256(path) == AUTH["reauthorized_model_assets"][name],
    }

sources = {}
for source_root in (
    "/home/straughter/Wan2GP-story-WD-m7xw",
    "/home/straughter/Wan2GP-story-WD-osfm",
):
    sources[source_root] = {
        "commit": run(("git", "-C", source_root, "rev-parse", "HEAD"))["stdout"].strip(),
        "status": run(("git", "-C", source_root, "status", "--porcelain=v1"))["stdout"].strip(),
    }

runtime_dir = Path(STATE["directory"])
inventory = []
for item in STATE["payload"]["inventory"]:
    path = runtime_dir / item["path"]
    observed = {
        "path": item["path"],
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
    inventory.append(observed)
canonical = json.dumps(sorted(inventory, key=lambda item: item["path"]), sort_keys=True, separators=(",", ":"))
payload_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
STATE["captured_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
STATE["fresh_host_recheck"] = True
STATE["payload"]["inventory"] = inventory
STATE["payload"]["canonical_sha256_observed"] = payload_hash
STATE_PATH.write_text(json.dumps(STATE, indent=2, sort_keys=True) + "\n", encoding="utf-8")

gpu = run(("nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu", "--format=csv,noheader,nounits"))
gpu_apps = run(("nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader"))
disk = run(("df", "-B1", "/home/straughter/Wan2GP"))
qc = run(("curl", "-fsS", "-m", "3", "http://127.0.0.1:8377/health"))
payload = {
    "schema_version": "wangp-dspy.wd-28ac.final-cell-preflight/v1",
    "captured_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    "assets": assets,
    "assets_all_match": all(item["match"] for item in assets.values()),
    "sources": sources,
    "sources_clean_except_ckpts": all(value["status"] == "?? ckpts" for value in sources.values()),
    "runtime_payload_observed_sha256": payload_hash,
    "runtime_payload_expected_sha256": STATE["payload"]["canonical_sha256"],
    "runtime_payload_match": payload_hash == STATE["payload"]["canonical_sha256"],
    "gpu": gpu,
    "gpu_apps": gpu_apps,
    "gpu_idle": gpu_apps["stdout"].strip() == "" and gpu["returncode"] == 0,
    "disk": disk,
    "qc_health": qc,
    "queue_db_absent": not (RUN / "jobs.db").exists(),
    "run_root": str(RUN),
    "operation_count": len(json.loads((RUN / "plan.json").read_text(encoding="utf-8"))["operations"]),
}
(RUN / "preflight.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    "assets_all_match": payload["assets_all_match"],
    "sources_clean_except_ckpts": payload["sources_clean_except_ckpts"],
    "runtime_payload_match": payload["runtime_payload_match"],
    "gpu_idle": payload["gpu_idle"],
    "queue_db_absent": payload["queue_db_absent"],
    "qc_health_returncode": qc["returncode"],
}, sort_keys=True))
if not all((
    payload["assets_all_match"],
    payload["sources_clean_except_ckpts"],
    payload["runtime_payload_match"],
    payload["gpu_idle"],
    payload["queue_db_absent"],
)):
    raise SystemExit(1)
