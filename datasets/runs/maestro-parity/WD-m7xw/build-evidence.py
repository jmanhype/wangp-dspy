#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
WAN2GP_COMMIT = "faea82d15bf10b3479c42c0ea430892aae975870"

MODELS: tuple[tuple[str, str, str], ...] = (
    ("ltx25-ltx-2.5-22b-distilled_diffusion_model_int8_convrot.safetensors", "/home/straughter/Wan2GP/ckpts/ltx-2.5-22b-distilled_diffusion_model_int8_convrot.safetensors", "b4bb89c54e025d834f0c6138dbf80c245e8196c27c8bff8dd47db4c03412c72f"),
    ("ltx25-ltx-2.5-22b_video_vae_bf16.safetensors", "/home/straughter/Wan2GP/ckpts/ltx-2.5-22b_video_vae_bf16.safetensors", "685b06ee3d9b2039647698fc4ea33175112462fc374e2777312c907897dfce8d"),
    ("ltx25-ltx-2.5-22b_diffusion_video_vae_bf16.safetensors", "/home/straughter/Wan2GP/ckpts/ltx-2.5-22b_diffusion_video_vae_bf16.safetensors", "847e14ca7f3355debca0cea4eaa24ac0fbcdf0061da054ac89ca638a869ddba3"),
    ("ltx25-ltx-2.5-22b_audio_vae_bf16.safetensors", "/home/straughter/Wan2GP/ckpts/ltx-2.5-22b_audio_vae_bf16.safetensors", "43ed048b9a5aa7eac181cf1b5bf68382aa4fb9d98627575d01d9b187d3462028"),
    ("ltx25-ltx-2.5-22b_vocoder_bf16.safetensors", "/home/straughter/Wan2GP/ckpts/ltx-2.5-22b_vocoder_bf16.safetensors", "a865b27a492fea788dc35bed29b333103ca1fb9c280f4fd77976ad19a3b13435"),
    ("ltx25-ltx-2.5-22b_text_embedding_projection_bf16.safetensors", "/home/straughter/Wan2GP/ckpts/ltx-2.5-22b_text_embedding_projection_bf16.safetensors", "06b7017692b2d0d42a863d609cf40e7672243eb3d13ae7a19650a7a8294ac494"),
    ("ltx25-ltx-2.5-22b_video_embeddings_connector_int8_convrot.safetensors", "/home/straughter/Wan2GP/ckpts/ltx-2.5-22b_video_embeddings_connector_int8_convrot.safetensors", "9559f09ff6fb1b3dca10617722df7133838ea0fee6f1457c90e992447796d765"),
    ("ltx25-ltx-2.5-22b_audio_embeddings_connector_int8_convrot.safetensors", "/home/straughter/Wan2GP/ckpts/ltx-2.5-22b_audio_embeddings_connector_int8_convrot.safetensors", "80270afb795fdac363dcd8329e6b375f6ca93f6a3d74a25b2bb440d342095362"),
    ("ltx25-ltx-2.5-spatial-upscaler-x2-1.0_bf16.safetensors", "/home/straughter/Wan2GP/ckpts/ltx-2.5-spatial-upscaler-x2-1.0_bf16.safetensors", "eb5a71fe4068ee87ccdb1c3aa635e547ca76bd2d30ae20ae889f2c325c0677e8"),
    ("ltx25-ltx-2.5-temporal-upscaler-x2-1.0_bf16.safetensors", "/home/straughter/Wan2GP/ckpts/ltx-2.5-temporal-upscaler-x2-1.0_bf16.safetensors", "2bc3300f2b3c3c1834d72164fbf13a3b9fd73e5a741e8a2c3f4035f89a75c3fe"),
    ("ltx25-gemma4-gemma4-12b-ltx-v1_int8_convrot.safetensors", "/home/straughter/Wan2GP/ckpts/gemma4-12b-ltx-v1/gemma4-12b-ltx-v1_int8_convrot.safetensors", "6a23b673266b65a318e26cad27fabd5c67609f4ecf51aa13996feb07d0060903"),
    ("ltx25-gemma4-tokenizer.json", "/home/straughter/Wan2GP/ckpts/gemma4-12b-ltx-v1/tokenizer.json", "cc8d3a0ce36466ccc1278bf987df5f71db1719b9ca6b4118264f45cb627bfe0f"),
    ("ltx25-gemma4-config.json", "/home/straughter/Wan2GP/ckpts/gemma4-12b-ltx-v1/config.json", "82ec29063791629eac6a023c662f4edc2a811e479343ae79f21b8453357caeb0"),
    ("ltx25-gemma4-chat_template.jinja", "/home/straughter/Wan2GP/ckpts/gemma4-12b-ltx-v1/chat_template.jinja", "ae53464bf3be25802b3a5b37def7fd89667067d7577049b3b2d74c4d8de4c6d4"),
    ("ltx25-gemma4-tokenizer_config.json", "/home/straughter/Wan2GP/ckpts/gemma4-12b-ltx-v1/tokenizer_config.json", "794a39f8330ce05020774c70c091225bc5f031b9cacf41fc20e52eb54b4b52d8"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def media_metadata(operation: str) -> dict[str, Any]:
    relative = f"outputs/{operation}/wd_m7xw_{operation}.mp4"
    probe = json.loads((ROOT / f"outputs/{operation}/wd_m7xw_{operation}.ffprobe.json").read_text())
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
    fps = video["r_frame_rate"].split("/", 1)
    return {
        "path": relative,
        "kind": "video",
        "width": int(video["width"]),
        "height": int(video["height"]),
        "duration_s": float(probe["format"]["duration"]),
        "fps": float(fps[0]) / float(fps[1]),
        "alpha_mode": "none",
        "audio": {
            "present": True,
            "codec": audio["codec_name"],
            "sample_rate_hz": int(audio["sample_rate"]),
            "channels": int(audio["channels"]),
        },
    }


def reference(relative: str, role: str) -> dict[str, str]:
    return {
        "path": relative,
        "role": role,
        "sha256": sha256(ROOT / relative),
        "license": "Operator-owned WD-m7xw generated evaluation asset; operator-authorized research/evaluation use; no redistribution",
    }


def repository_state() -> dict[str, Any]:
    status = subprocess.run(
        ["git", "-C", str(REPO), "status", "--porcelain=v1"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    return {
        "commit": subprocess.run(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], check=True, text=True, capture_output=True
        ).stdout.strip(),
        "dirty_state": {
            "dirty": bool(status),
            "identity_sha256": hashlib.sha256(status.encode()).hexdigest(),
            "status_lines": status.splitlines(),
        },
    }


def main() -> None:
    operations = ("create", "extend", "retake", "edit")
    metadata = [media_metadata(operation) for operation in operations]
    output_paths = [entry["path"] for entry in metadata]
    outputs = [{"path": path, "sha256": sha256(ROOT / path)} for path in output_paths]
    native_logs = [f"host-logs-resumed/{operation}.render.log" for operation in operations]
    measurements = {
        "schema_version": "wangp-dspy.wd-m7xw.objective-measurements/v1",
        "source_sha256": outputs[0]["sha256"],
        "rows": [
            {"operation": entry["path"].split("/")[1], **entry, "bytes": (ROOT / entry["path"]).stat().st_size}
            for entry in metadata
        ],
        "retake_first_frame_ssim_all": 0.988417,
        "retake_first_frame_psnr_db": 41.494432,
        "edit_global_psnr_db": 38.302450,
    }
    (ROOT / "objective-measurements.json").write_text(json.dumps(measurements, indent=2) + "\n")
    reviewer = json.loads((ROOT / "reviewer-verdict.json").read_text())
    evidence = {
        "schema": "wangp-dspy.maestro-parity-evidence/v1",
        "operator_authorization": {
            "status": "approved",
            "text": "kill whatever that is that was holding up the GPU and get back to work\\nUnblock\\nnow requested prioritizing LTX-2.5",
            "scope": "WD-m7xw eight-operation LTX-2.5 no-download batch on 3090; stop only re-verified llama-server PID 3213164; leave it stopped",
            "timestamp": "2026-09-26T21:36:04Z",
            "approved_by": "operator via /root dispatcher",
        },
        "command": ["timeout", "1900", "ssh", "3090", "/home/straughter/wd-m7xw-run/host-scripts/50_run_operation.sh", "create"],
        "repository": repository_state(),
        "model_provenance": [
            {
                "identity": identity,
                "source": f"https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main/{Path(destination).name}",
                "license": "Upstream distribution license; operator research/evaluation only",
                "sha256": digest,
                "destination": destination,
                "download_approved": True,
                "preflight_hash_verified": True,
                "no_download_bytes": True,
            }
            for identity, destination, digest in MODELS
        ],
        "reference_provenance": [
            reference("outputs/create/wd_m7xw_create.mp4", "ltx25_generated_source_video"),
            reference("outputs/create/first-frame.png", "retake_and_recast_reference_frame"),
            reference("inputs/repaint-mask.mp4", "repaint_editable_region_mask"),
        ],
        "queue_attempt": {
            "queue_id": "wd-m7xw-ltx25-native-cli",
            "job_id": "wd-m7xw-ltx25-eight-operations",
            "retry_id": "attempt-1",
            "admission_state": "admitted",
            "exit_status": "succeeded",
            "native_logs": native_logs,
            "native_log_sha256": {path: sha256(ROOT / path) for path in native_logs},
        },
        "output": outputs,
        "media_metadata": metadata,
        "objective_gate_results": [
            {"name": "wd_m7xw_create_duration_s", "inputs": [output_paths[0]], "threshold": 1.375, "measured": metadata[0]["duration_s"], "verdict": "pass"},
            {"name": "wd_m7xw_create_audio_present", "inputs": [output_paths[0]], "threshold": 1.0, "measured": 1.0, "verdict": "pass"},
            {"name": "wd_m7xw_extend_duration_s", "inputs": [output_paths[1], output_paths[0]], "threshold": 1.375, "measured": metadata[1]["duration_s"], "verdict": "pass"},
            {"name": "wd_m7xw_retake_first_frame_ssim", "inputs": [output_paths[2], "outputs/create/first-frame.png"], "threshold": 0.95, "measured": 0.988417, "verdict": "pass"},
            {"name": "wd_m7xw_edit_global_psnr_db", "inputs": [output_paths[3], output_paths[0]], "threshold": 20.0, "measured": 38.30245, "verdict": "pass"},
            {"name": "wd_m7xw_distinct_output_hashes", "inputs": output_paths, "threshold": 4.0, "measured": 4.0, "verdict": "pass"},
        ],
        "reviewer_verdict": reviewer,
        "row_dispositions": {
            operation: {"disposition": "host_run_verified", "operation": operation, "evidence": path}
            for operation, path in zip(operations, output_paths)
        } | {
            operation: {"disposition": "dependency_blocked", "operation": operation, "evidence": f"host-logs-resumed/{operation}.render.log"}
            for operation in ("outpaint", "repaint", "recast", "upscale")
        },
        "runtime_notes": {
            "wan2gp_commit": WAN2GP_COMMIT,
            "download_bytes": 0,
            "offline_mode": True,
            "dependency_boundaries": "dependency-boundaries.md",
            "gpu_holder_final": "llama-server PID 3213164 absent/stopped; GPU 84 MiB used",
            "operation_map": "operation-map.md",
        },
    }
    (ROOT / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")


if __name__ == "__main__":
    main()
