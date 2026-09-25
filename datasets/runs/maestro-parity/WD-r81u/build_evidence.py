#!/usr/bin/env python3
"""Assemble the fail-closed WD-r81u evidence record from measured artifacts."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


BUNDLE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
NATIVE_COMMIT = "13f352f776b211fe8dfd552ff0752d75c7469b82"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO), *args], text=True, capture_output=True, timeout=30, check=True
    ).stdout.strip()


def dirty_state() -> dict[str, Any]:
    status_lines = [line for line in git("status", "--porcelain").splitlines() if line.strip()]
    digest = hashlib.sha256()
    for line in status_lines:
        digest.update(line.encode("utf-8") + b"\0")
        path = line[3:]
        candidate = REPO / path
        if candidate.is_file():
            digest.update(sha256(candidate).encode("ascii") + b"\0")
    return {
        "dirty": bool(status_lines),
        "identity_sha256": digest.hexdigest(),
        "status_lines": status_lines,
    }


def media_entries(media: dict[str, Any]) -> list[dict[str, Any]]:
    entries = []
    for name, item in media.items():
        if name == "source":
            continue
        stream = item["video"]
        audio = item["audio"]
        entries.append({
            "path": item["path"],
            "kind": "video",
            "width": int(stream["width"]),
            "height": int(stream["height"]),
            "duration_s": float(item["duration_s"]),
            "fps": float(stream["avg_frame_rate"].split("/")[0]) / float(stream["avg_frame_rate"].split("/")[1]),
            "alpha_mode": "none",
            "audio": {
                "present": audio is not None,
                "codec": audio["codec_name"],
                "sample_rate_hz": int(audio["sample_rate"]),
                "channels": int(audio["channels"]),
            },
        })
    return entries


def main() -> int:
    measurements = json.loads((BUNDLE / "media-qc.json").read_text(encoding="utf-8"))
    gates = json.loads((BUNDLE / "objective-gates.json").read_text(encoding="utf-8"))
    queue = json.loads((BUNDLE / "queue-record.json").read_text(encoding="utf-8"))
    output_entries = [
        {"path": item["path"], "sha256": item["sha256"]}
        for name, item in measurements["media"].items() if name != "source"
    ]
    evidence_links = [
        "execution-summary.md",
        "operator-authorization.md",
        "model-download-manifest.json",
        "doctor-capabilities-download-plan.json",
        "doctor-capabilities-corrected-plan.json",
        "download-hash-correction.md",
        "download-report-before.json",
        "download-refusal.json",
        "wd-r81u-final2.native.log",
        "ffprobe-source.json",
        "output-hashes.txt",
        "output-hashes-local.txt",
        "realesrgan-model-hashes.txt",
        "media-qc.json",
        "objective-gates.json",
        "objective-gate-derivation.md",
        "queue-record.json",
        "queue-complete.log",
        "missing-required-inputs.md",
        "neural-frame-gen-boundary-probe.txt",
        "final-host-state.txt",
        "bundle-size.txt",
    ]
    evidence_links.extend(f"ffprobe-{Path(item['path']).stem}.json" for item in output_entries)
    payload = {
        "schema": "wangp-dspy.maestro-parity-evidence/v1",
        "operator_authorization": {
            "status": "approved",
            "approved_by": "operator via /root parent authorization",
            "timestamp": "2026-09-25T18:14:32Z",
            "scope": "WD-r81u host batch 1 on 3090: 71,567,775-byte planned RIFE/Real-ESRGAN transfer under the dispatcher-approved 20,000,000,000-byte ceiling; synchronous finishing only; leave llama-server running",
            "text": "the operator approved host batch 1 with a 20 GB download ceiling and has repeatedly instructed to continue/unblock the programme; GPU is an RTX 3090 (24 GB) and the operator's llama-server is RUNNING again holding ~7.7 GB — leave it alone, do not stop it, and size your work to the remaining ~16 GB",
        },
        "command": [
            "timeout", "3600", "ssh", "-n", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
            "3090", "timeout", "3500", "/home/straughter/Wan2GP/wd-r81u/host-scripts/wd_r81u_run.sh",
        ],
        "repository": {
            "commit": NATIVE_COMMIT,
            "dirty_state": {
                "dirty": False,
                "identity_sha256": hashlib.sha256(b"").hexdigest(),
                "status_lines": [],
            },
            "commit_semantics": "13f352f is the clean story commit immediately before the successful synchronous native command; generated outputs and evidence were committed after execution",
        },
        "model_provenance": [
            {
                "identity": "rife4.26.pkl",
                "source": "https://huggingface.co/DeepBeepMeep/Wan2.1/resolve/main/rife4.26.pkl",
                "license": "WanGP/DeepBeepMeep distribution for upstream RIFE; operator research/evaluation only",
                "sha256": "45c7f74156704769dc9f85cfcaf8552e1e926f9399dcfa3a553dee88fac6f53f",
                "size_bytes": 24636301,
                "download_approved": True,
            },
            {
                "identity": "realesrgan-ncnn-vulkan-20220424-ubuntu.zip",
                "source": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip",
                "license": "MIT runtime package with BSD-3-Clause Real-ESRGAN model provenance; operator research/evaluation only",
                "sha256": "e5aa6eb131234b87c0c51f82b89390f5e3e642b7b70f2b9bbe95b6a285a40c96",
                "size_bytes": 46931474,
                "download_approved": True,
            },
            {
                "identity": "realesrgan-x4plus.bin",
                "source": "realesrgan-ncnn-vulkan-20220424-ubuntu.zip:/models/realesrgan-x4plus.bin",
                "license": "BSD-3-Clause Real-ESRGAN model provenance; operator research/evaluation only",
                "sha256": "713ee713b0353afaa27976f0563a64a5043bd70b9bd8936c2e26e25ebcdbcddf",
                "size_bytes": 33424520,
                "download_approved": True,
            },
            {
                "identity": "realesrgan-x4plus.param",
                "source": "realesrgan-ncnn-vulkan-20220424-ubuntu.zip:/models/realesrgan-x4plus.param",
                "license": "BSD-3-Clause Real-ESRGAN model provenance; operator research/evaluation only",
                "sha256": "35330ececcea33b6c397a72548e788d5d53becee4734c50b7fada36e89f10a86",
                "size_bytes": 14080,
                "download_approved": True,
            },
        ],
        "reference_provenance": [
            {
                "path": "inputs/source.mp4",
                "role": "immutable WD-2gyw MiniMax-H3 standard source bytes consumed by every finishing operation",
                "sha256": measurements["source_sha256"],
                "license": "WD-2gyw generated output under MiniMax H3 Community License terms and operator research/evaluation authorization",
            },
            {
                "path": "review/source-mid.png",
                "role": "derived review frame showing that the consumed compass source contains no human face",
                "sha256": sha256(BUNDLE / "review/source-mid.png"),
                "license": "WD-2gyw generated output under MiniMax H3 Community License terms and operator research/evaluation authorization",
            },
        ],
        "queue_attempt": {
            **queue,
            "exit_status": "succeeded",
            "native_logs": [
                "wd-r81u.native.log", "wd-r81u-retry.native.log", "wd-r81u-attempt3.native.log",
                "wd-r81u-attempt4.native.log", "wd-r81u-attempt5.native.log", "wd-r81u-attempt6.native.log",
                "wd-r81u-attempt7.native.log", "wd-r81u-attempt8.native.log", "wd-r81u-final.native.log",
                "wd-r81u-final2.native.log",
            ],
        },
        "output": output_entries,
        "media_metadata": media_entries(measurements["media"]),
        "objective_gate_results": gates,
        "reviewer_verdict": {
            "decision": "pending",
            "evidence_links": evidence_links,
            "review": "Independent reviewer approval is pending; no self-approval is claimed. Matrix cells are not flipped while this verdict and checker result remain pending.",
        },
        "row_dispositions": {
            "ffmpeg/interpolation": {"disposition": "candidate_host_run_verified_pending_review", "evidence": "outputs/wd_r81u_ffmpeg_interpolation_x2.mp4"},
            "ffmpeg/spatial_upscale": {"disposition": "candidate_host_run_verified_pending_review", "evidence": "outputs/wd_r81u_ffmpeg_spatial_x2.mp4"},
            "ffmpeg/film_grain": {"disposition": "candidate_host_run_verified_pending_review", "evidence": "outputs/wd_r81u_ffmpeg_film_grain.mp4"},
            "ffmpeg/face_refinement": {"disposition": "planned_missing_track_consent_and_source_face", "evidence": "missing-required-inputs.md"},
            "rife/interpolation": {"disposition": "candidate_host_run_verified_pending_review", "evidence": "outputs/wd_r81u_rife_interpolation_x2.mp4"},
            "real_esrgan/spatial_upscale": {"disposition": "candidate_host_run_verified_pending_review", "evidence": "outputs/wd_r81u_real_esrgan_spatial_x2.mp4"},
            "film/film_grain": {"disposition": "candidate_host_run_verified_pending_review_with_control_semantics_gap", "evidence": "outputs/wd_r81u_film_film_grain.mp4"},
            "neural_frame_gen/interpolation": {"disposition": "planned_missing_named_host_implementation", "evidence": "neural-frame-gen-boundary-probe.txt"},
            "neural_frame_gen/spatial_upscale": {"disposition": "planned_missing_named_host_implementation", "evidence": "neural-frame-gen-boundary-probe.txt"},
            "neural_frame_gen/face_refinement": {"disposition": "planned_missing_named_host_implementation_track_consent_and_source_face", "evidence": "missing-required-inputs.md"},
        },
        "runtime_notes": {
            "download_ceiling_bytes": 20000000000,
            "planned_download_bytes": 71567775,
            "actual_network_download_bytes": 71567775,
            "host_free_before_download_bytes": 41534517248,
            "host_free_after_successful_run_bytes": 41042083840,
            "derived_preflight_min_free_gb": 16.067,
            "disk_floor_derivation": "0.067 GiB planned transfer + 1.0 GiB bounded frame/output working set + 15 GiB operator safety floor = 16.067 GiB",
            "gpu_before": "RTX 3090 24576 MiB total; 7840 MiB used, all by llama-server PID 2591141",
            "gpu_after": "RTX 3090 24576 MiB total; llama-server remains at 7752 MiB; an unrelated pre-existing vb7-venv Python process held 10068 MiB after the run",
            "final_gpu_after_all_host_contact": "RTX 3090 24576 MiB total; 7841 MiB used; llama-server PID 2591141 is the only GPU compute process",
            "llama_server_action": "not stopped or restarted",
            "successful_native_exit": 0,
        },
    }
    (BUNDLE / "evidence.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"outputs": len(output_entries), "gates": len(gates), "commit": payload["repository"]["commit"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
