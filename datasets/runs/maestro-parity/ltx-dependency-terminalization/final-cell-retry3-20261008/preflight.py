#!/usr/bin/env python3
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN = Path("/home/straughter/wd-28ac-run/phase-b-gate22-corrected-retry-final-cell-20261008-retry3")
AUTH = json.loads((RUN / "authorization.json").read_text(encoding="utf-8"))
PLAN = json.loads((RUN / "plan.json").read_text(encoding="utf-8"))
STATE_PATH = RUN / "runtime-state.json"
STATE = json.loads(STATE_PATH.read_text(encoding="utf-8"))
PYI = "shared/gradio/hierarchy_selector/hierarchy_selector.pyi"
PYI_COMMIT_SHA256 = "44594db6c103b6942734afb2986e31ba951f442cf2a853dac5d509c01eb4c125"
SPATIAL_SOURCE = Path("/home/straughter/Wan2GP/loras/ltx2/ltx-2.3-22b-ic-lora-pixel-spatial-upscaler-x2-0.9.safetensors")
SPATIAL_LINK = Path("/home/straughter/Wan2GP-story-WD-osfm/loras/ltx2/ltx-2.3-22b-ic-lora-pixel-spatial-upscaler-x2-0.9.safetensors")
DISTILLED_SOURCE = Path("/home/straughter/Wan2GP/loras/ltx2/ltx-2.3-22b-distilled-lora-384-1.1.safetensors")
DISTILLED_LINK = Path("/home/straughter/Wan2GP-story-WD-osfm/loras/ltx2/ltx-2.3-22b-distilled-lora-384-1.1.safetensors")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(argv):
    result = subprocess.run(argv, text=True, capture_output=True, check=False)
    return {"argv": list(argv), "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def restore_pyi(source_root: str):
    checkout = run(("git", "-C", source_root, "checkout", "--", PYI))
    if checkout["returncode"]:
        raise SystemExit(checkout["stderr"])
    observed = sha256(Path(source_root) / PYI)
    if observed != PYI_COMMIT_SHA256:
        raise SystemExit(f"PYI_RESTORE_HASH_MISMATCH {source_root} {observed}")


restore_pyi("/home/straughter/Wan2GP-story-WD-m7xw")
restore_pyi("/home/straughter/Wan2GP-story-WD-osfm")

sources_before_link = {}
for source_root in ("/home/straughter/Wan2GP-story-WD-m7xw", "/home/straughter/Wan2GP-story-WD-osfm"):
    sources_before_link[source_root] = {
        "commit": run(("git", "-C", source_root, "rev-parse", "HEAD"))["stdout"].strip(),
        "status": run(("git", "-C", source_root, "status", "--porcelain=v1"))["stdout"].strip(),
    }
    if sources_before_link[source_root]["status"] != "?? ckpts":
        raise SystemExit(f"SOURCE_NOT_CLEAN {source_root} {sources_before_link[source_root]['status']}")

if SPATIAL_LINK.exists() or SPATIAL_LINK.is_symlink():
    raise SystemExit("SPATIAL_UPSCALER_LINK_DESTINATION_EXISTS")
if not SPATIAL_SOURCE.is_file() or SPATIAL_SOURCE.is_symlink():
    raise SystemExit("DOWNLOADED_SPATIAL_UPSCALER_INVALID")
spatial_size = SPATIAL_SOURCE.stat().st_size
spatial_hash = sha256(SPATIAL_SOURCE)
if spatial_size != 654465286 or spatial_hash != AUTH["retry3_assets"]["downloaded_spatial_upscaler_lora"]["sha256"]:
    raise SystemExit("DOWNLOADED_SPATIAL_UPSCALER_IDENTITY_MISMATCH")
SPATIAL_LINK.parent.mkdir(parents=True, exist_ok=True)
os.symlink(SPATIAL_SOURCE, SPATIAL_LINK)
if not SPATIAL_LINK.is_symlink() or sha256(SPATIAL_LINK) != spatial_hash:
    raise SystemExit("SPATIAL_UPSCALER_LINK_VERIFY_FAILED")

if not DISTILLED_LINK.is_symlink() or not DISTILLED_SOURCE.is_file():
    raise SystemExit("EXISTING_DISTILLED_LORA_LINK_INVALID")
distilled_size = DISTILLED_SOURCE.stat().st_size
distilled_hash = sha256(DISTILLED_SOURCE)
if distilled_size != 7605507256 or distilled_hash != AUTH["retry3_assets"]["existing_distilled_lora"]["sha256"]:
    raise SystemExit("EXISTING_DISTILLED_LORA_IDENTITY_MISMATCH")

sources_after_link = {}
for source_root in ("/home/straughter/Wan2GP-story-WD-m7xw", "/home/straughter/Wan2GP-story-WD-osfm"):
    sources_after_link[source_root] = {
        "commit": run(("git", "-C", source_root, "rev-parse", "HEAD"))["stdout"].strip(),
        "status": run(("git", "-C", source_root, "status", "--porcelain=v1"))["stdout"].strip(),
    }

asset_paths = {
    "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors": Path("/home/straughter/Wan2GP-story-WD-m7xw/loras/ltx2/ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors"),
    "ltx-2.3-22b-ic-lora-outpaint.safetensors": Path("/home/straughter/Wan2GP-story-WD-m7xw/loras/ltx2/ltx-2.3-22b-ic-lora-outpaint.safetensors"),
    "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors": Path("/home/straughter/Wan2GP-story-WD-m7xw/loras/ltx2/ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors"),
    "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors": Path("/home/straughter/Wan2GP-story-WD-m7xw/loras/ltx2/ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors"),
    "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors": Path("/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors"),
}
expected_hashes = {
    "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors": "515e4e139001ac6282357a5b35372e42e98b3affd5fcc886a52242abeed19559",
    "ltx-2.3-22b-ic-lora-outpaint.safetensors": "32c5d3e0649aa4e89b192319f3c79460dfd2319d2859ca11fa6f88e983a81665",
    "ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors": "73dd0841c0d4f0eb26fb1f017781b841b2752021944ac5ecefe57917f6dae6b5",
    "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors": "984851b769ea2bcb4c9e0a239a7676239e42c6a6001ddc69943b41ff0b283c1d",
    "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors": "5fc8d83656cdabf93b79bfb8799ee1c84c8270c59a49caccd4f8d1a27c77f6ec",
}
assets = {}
for name, path in asset_paths.items():
    observed = sha256(path)
    assets[name] = {"path": str(path), "size_bytes": path.stat().st_size, "sha256": observed, "match": observed == expected_hashes[name]}

runtime_dir = Path(STATE["directory"])
inventory = []
for item in STATE["payload"]["inventory"]:
    path = runtime_dir / item["path"]
    inventory.append({"path": item["path"], "size_bytes": path.stat().st_size, "sha256": sha256(path)})
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
    "schema_version": "wangp-dspy.wd-28ac.retry3-preflight/v1",
    "captured_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    "operator_approval": PLAN["operator_retry3_authorization_20261008"],
    "sources_before_link": sources_before_link,
    "sources_after_link": sources_after_link,
    "downloaded_spatial_upscaler": {
        "source": str(SPATIAL_SOURCE),
        "destination_link": str(SPATIAL_LINK),
        "size_bytes": spatial_size,
        "sha256": spatial_hash,
        "link_created": True,
    },
    "existing_distilled_lora": {
        "source": str(DISTILLED_SOURCE),
        "destination_link": str(DISTILLED_LINK),
        "size_bytes": distilled_size,
        "sha256": distilled_hash,
        "link_verified": True,
    },
    "assets": assets,
    "assets_all_match": all(item["match"] for item in assets.values()),
    "runtime_payload_observed_sha256": payload_hash,
    "runtime_payload_match": payload_hash == STATE["payload"]["canonical_sha256"],
    "gpu": gpu,
    "gpu_apps": gpu_apps,
    "gpu_idle": gpu_apps["stdout"].strip() == "" and gpu["returncode"] == 0,
    "disk": disk,
    "qc_health": qc,
    "queue_db_absent": not (RUN / "jobs.db").exists(),
    "operation_count": len(PLAN["operations"]),
}
(RUN / "preflight.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    "assets_all_match": payload["assets_all_match"],
    "runtime_payload_match": payload["runtime_payload_match"],
    "gpu_idle": payload["gpu_idle"],
    "queue_db_absent": payload["queue_db_absent"],
    "qc_health_returncode": qc["returncode"],
}, sort_keys=True))
if not all((payload["assets_all_match"], payload["runtime_payload_match"], payload["gpu_idle"], payload["queue_db_absent"])):
    raise SystemExit(1)
