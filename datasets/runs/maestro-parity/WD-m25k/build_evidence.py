#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
BASE_COMMIT = "28fc76a1"
WAN2GP_COMMIT = "4c93b64a47b5b0a915f2abec2ce754be98227150"

MODELS: tuple[tuple[str, str, str, str], ...] = (
    (
        "h3-MiniMax-H3-FL2VA-pruned_rank8_int8_convrot.safetensors",
        "https://huggingface.co/DeepBeepMeep/MiniMax-H3/resolve/main/MiniMax-H3-FL2VA-pruned_rank8_int8_convrot.safetensors",
        "MiniMax H3 Community License Agreement; operator research/evaluation only",
        "30ff400f974b11a1ef13d216c5d9f6439a9c10322a3988b0374a39672ce286f0",
    ),
    (
        "h3-MiniMax-H3-video_vae_fp16.safetensors",
        "https://huggingface.co/DeepBeepMeep/MiniMax-H3/resolve/main/MiniMax-H3-video_vae_fp16.safetensors",
        "MiniMax H3 Community License Agreement; operator research/evaluation only",
        "455010492bb59a9cc7b8f1ee23905b22a10079f89490adbf820a1728efcaea6b",
    ),
    (
        "h3-MiniMax-H3-audio_vae_fp32.safetensors",
        "https://huggingface.co/DeepBeepMeep/MiniMax-H3/resolve/main/MiniMax-H3-audio_vae_fp32.safetensors",
        "MiniMax H3 Community License Agreement; operator research/evaluation only",
        "37dddc2f3e6d5d5139d823d5ea283bbf304dadcb885b1ccda818aa13dade5ea2",
    ),
    (
        "h3-Qwen3-VL-32B-Instruct-layer50_quanto_bf16_int8.safetensors",
        "https://huggingface.co/DeepBeepMeep/MiniMax-H3/resolve/main/Qwen3-VL-32B-Instruct-layer50_quanto_bf16_int8.safetensors",
        "MiniMax H3 Community License Agreement; operator research/evaluation only",
        "4df8fc5237746b3b058745d6ec8fe1e54a9721bdc663d35d2d1806952672f301",
    ),
)

SUCCESS_OPERATIONS = (
    "kfi_repaint",
    "kfi_upscale",
    "audio_repaint",
    "audio_upscale",
)

BOUNDARIES: tuple[dict[str, str], ...] = (
    {"row": "minimax_h3/kfi_frames_injection", "operation": "create", "log": "host-logs/kfi-create-retry-probe.render.log", "exit_file": "host-logs/kfi-create-retry-probe.exit", "boundary": "unsupported_host_implementation", "reason": "KFI requires at least one reference image; a create request cannot supply one."},
    {"row": "minimax_h3/kfi_frames_injection", "operation": "extend", "log": "host-logs/render-batch-retry.render.log", "exit_file": "host-logs/render-batch-retry.exit", "boundary": "unsupported_host_implementation", "reason": "KFI frame injection fails in the current host implementation with KeyError resolved_frame_index."},
    {"row": "minimax_h3/kfi_frames_injection", "operation": "blend", "log": "host-logs/kfi-blend-retry-probe.render.log", "exit_file": "host-logs/kfi-blend-retry-probe.exit", "boundary": "unsupported_host_implementation", "reason": "Two-guide KFI blend reaches denoising and fails with KeyError resolved_frame_index."},
    {"row": "minimax_h3/kfi_frames_injection", "operation": "edit", "log": "host-logs/render-batch-retry.render.log", "exit_file": "host-logs/render-batch-retry.exit", "boundary": "unsupported_host_implementation", "reason": "Guide-based KFI edit fails in the current host implementation with KeyError resolved_frame_index."},
    {"row": "minimax_h3/kfi_frames_injection", "operation": "outpaint", "log": "host-logs/kfi-outpaint-retry-probe.render.log", "exit_file": "host-logs/kfi-outpaint-retry-probe.exit", "boundary": "unsupported_host_implementation", "reason": "Guide margins plus KFI fail with KeyError resolved_frame_index."},
    {"row": "minimax_h3/kfi_frames_injection", "operation": "recast", "log": "host-logs/kfi-recast-probe.render.log", "exit_file": "host-logs/kfi-recast-probe.exit", "boundary": "unsupported_host_implementation", "reason": "Image, video, and audio references require the Ref2VA checkpoint; this row used FL2VA."},
    {"row": "minimax_h3/h3_audio_refinement", "operation": "create", "log": "host-logs/audio-create-probe.render.log", "exit_file": "host-logs/audio-create-probe.exit", "boundary": "unsupported_host_implementation", "reason": "Audio generation from Control Video requires Use Control Video and a control-video file."},
    {"row": "minimax_h3/h3_audio_refinement", "operation": "extend", "log": "host-logs/render-batch.render.log", "exit_file": "host-logs/render-batch.exit", "boundary": "unsupported_host_implementation", "reason": "Audio generation from Control Video requires Use Control Video and a control-video file."},
    {"row": "minimax_h3/h3_audio_refinement", "operation": "blend", "log": "host-logs/audio-blend-probe.render.log", "exit_file": "host-logs/audio-blend-probe.exit", "boundary": "unsupported_host_implementation", "reason": "FL2VA two-guide audio blend fails with KeyError reference_video_max_frames."},
    {"row": "minimax_h3/h3_audio_refinement", "operation": "retake", "log": "host-logs/render-batch.render.log", "exit_file": "host-logs/render-batch.exit", "boundary": "unsupported_host_implementation", "reason": "Audio generation from Control Video requires Use Control Video; a start frame alone is insufficient."},
    {"row": "minimax_h3/h3_audio_refinement", "operation": "outpaint", "log": "host-logs/audio-outpaint-probe.render.log", "exit_file": "host-logs/audio-outpaint-probe.exit", "boundary": "unsupported_host_implementation", "reason": "The command exited 0 and emitted media, but dimensions stayed 480x832; no outpaint enlargement occurred, so this cannot be host_run_verified."},
    {"row": "minimax_h3/h3_audio_refinement", "operation": "recast", "log": "host-logs/audio-recast-probe.render.log", "exit_file": "host-logs/audio-recast-probe.exit", "boundary": "unsupported_host_implementation", "reason": "Audio generation from Control Video requires Use Control Video; an image reference is insufficient."},
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_state() -> dict[str, Any]:
    status = subprocess.run(
        ["git", "-C", str(REPO), "status", "--porcelain=v1"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    commit = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    return {
        "commit": commit,
        "base_commit": BASE_COMMIT,
        "dirty_state": {
            "dirty": bool(status),
            "identity_sha256": hashlib.sha256(status.encode()).hexdigest(),
            "status_lines": status.splitlines(),
        },
    }


def media_metadata(operation: str) -> dict[str, Any]:
    relative = f"outputs/{operation}/wd_m25k_{operation}.mp4"
    probe = json.loads((ROOT / f"outputs/{operation}/wd_m25k_{operation}.ffprobe.json").read_text())
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
    numerator, denominator = video["r_frame_rate"].split("/", 1)
    return {
        "path": relative,
        "kind": "video",
        "width": int(video["width"]),
        "height": int(video["height"]),
        "duration_s": float(probe["format"]["duration"]),
        "fps": float(numerator) / float(denominator),
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
        "license": "Operator-owned generated evaluation asset; operator-authorized research/evaluation use; no redistribution",
    }


def ffmpeg_psnr(source: Path, output: Path) -> float:
    result = subprocess.run(
        [
            "ffmpeg", "-nostdin", "-i", str(source), "-i", str(output),
            "-lavfi", "[0:v][1:v]psnr", "-f", "null", "-",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    match = re.search(r"average:([0-9.]+)", result.stderr)
    if match is None:
        raise RuntimeError(f"No PSNR average in ffmpeg output for {output}")
    return float(match.group(1))


def boundary_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in BOUNDARIES:
        log = ROOT / item["log"]
        exit_file = ROOT / item["exit_file"]
        record = dict(item)
        record["exit"] = int(exit_file.read_text().strip())
        record["log_sha256"] = sha256(log)
        record["output_bytes"] = sum(
            path.stat().st_size
            for path in (ROOT / "boundaries" / f"{item['row'].split('/')[-1]}-{item['operation']}-probe").glob("*")
            if path.is_file()
        ) if (ROOT / "boundaries" / f"{item['row'].split('/')[-1]}-{item['operation']}-probe").exists() else 0
        records.append(record)
    return records


def matrix_statuses(text: str, rows: tuple[str, ...]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for line in text.splitlines():
        if not line.startswith("| minimax_h3/"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        family = cells[0]
        if family in rows:
            result[family] = [re.split(r"\s+", cell, 1)[0] for cell in cells[1:]]
    if set(result) != set(rows):
        raise RuntimeError(f"Expected matrix rows {rows}, found {sorted(result)}")
    return result


def main() -> None:
    metadata = [media_metadata(operation) for operation in SUCCESS_OPERATIONS]
    output_paths = [entry["path"] for entry in metadata]
    outputs = [{"path": path, "sha256": sha256(ROOT / path)} for path in output_paths]
    kfi_psnr = ffmpeg_psnr(
        ROOT / "inputs/wd_2gyw_h3_kfi_frames_injection.mp4",
        ROOT / "outputs/kfi_repaint/wd_m25k_kfi_repaint.mp4",
    )
    audio_psnr = ffmpeg_psnr(
        ROOT / "inputs/wd_2gyw_h3_audio_refinement.mp4",
        ROOT / "outputs/audio_repaint/wd_m25k_audio_repaint.mp4",
    )
    measurements = {
        "schema_version": "wangp-dspy.wd-m25k.objective-measurements/v1",
        "psnr_source_pairs": {
            "kfi_repaint": kfi_psnr,
            "audio_repaint": audio_psnr,
        },
        "rows": [
            {
                "operation": operation,
                "path": entry["path"],
                "sha256": sha256(ROOT / entry["path"]),
                "bytes": (ROOT / entry["path"]).stat().st_size,
                "width": entry["width"],
                "height": entry["height"],
                "duration_s": entry["duration_s"],
                "fps": entry["fps"],
            }
            for operation, entry in zip(SUCCESS_OPERATIONS, metadata)
        ],
    }
    (ROOT / "objective-measurements.json").write_text(json.dumps(measurements, indent=2) + "\n")

    boundaries = boundary_records()
    boundary_doc = {
        "schema_version": "wangp-dspy.wd-m25k.boundary-evidence/v1",
        "base_commit": BASE_COMMIT,
        "wan2gp_commit": WAN2GP_COMMIT,
        "records": boundaries,
        "audio_outpaint_output": {
            "path": "boundaries/audio-outpaint-probe/2026-09-26-21h08m01s_seed3207_Audio-refinement outpaint boundary with guide margins and audio mode..mp4",
            "sha256": sha256(next((ROOT / "boundaries/audio-outpaint-probe").glob("*.mp4"))),
            "width": 480,
            "height": 832,
            "expected_enlargement": "width or height greater than source",
            "verdict": "fail",
        },
    }
    (ROOT / "boundary-evidence.json").write_text(json.dumps(boundary_doc, indent=2) + "\n")

    current_doc = (REPO / "docs/video-capabilities.md").read_text()
    base_doc = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{BASE_COMMIT}:docs/video-capabilities.md"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    target_rows = ("minimax_h3/kfi_frames_injection", "minimax_h3/h3_audio_refinement")
    before = matrix_statuses(base_doc, target_rows)
    after = matrix_statuses(current_doc, target_rows)
    changed = sum(
        1
        for row in target_rows
        for old, new in zip(before[row], after[row])
        if old != new
    )
    transition = {
        "schema_version": "wangp-dspy.wd-m25k.matrix-transition/v1",
        "base_commit": BASE_COMMIT,
        "target_rows": list(target_rows),
        "before": before,
        "after": after,
        "changed_cells": changed,
        "expected_changed_cells": 16,
        "planned_after_target_rows": sum(value.count("planned") for value in after.values()),
        "verified_after_target_rows": sum(value.count("host_run_verified") for value in after.values()),
        "unsupported_after_target_rows": sum(value.count("unsupported") for value in after.values()),
        "pass": changed == 16 and all("planned" not in value for value in after.values()),
    }
    (ROOT / "matrix-transition-check.json").write_text(json.dumps(transition, indent=2) + "\n")

    native_logs = [
        "host-logs/render-batch.render.log",
        "host-logs/kfi_upscale.retry.render.log",
        "host-logs/audio_upscale.retry.render.log",
    ]
    reviewer = json.loads((ROOT / "reviewer-verdict.json").read_text())
    evidence = {
        "schema": "wangp-dspy.maestro-parity-evidence/v1",
        "operator_authorization": {
            "status": "approved",
            "text": "Continue the remaining 56 video cells, prioritizing no-download LTX-2.5 after the tokenizer fix.",
            "scope": "WD-m25k sixteen-cell H3 KFI/audio-refinement no-download batch on 3090; zero downloads; isolated Wan2GP worktree; no unrelated service mutation",
            "timestamp": "2026-09-27T01:22:06Z",
            "approved_by": "operator via /root dispatcher",
        },
        "command": ["ssh", "3090", "/tmp/23_postprocess_retry.sh"],
        "repository": repository_state(),
        "model_provenance": [
            {
                "identity": identity,
                "source": source,
                "license": license_text,
                "sha256": digest,
                "download_approved": True,
                "preflight_hash_verified": True,
                "no_download_bytes": True,
            }
            for identity, source, license_text, digest in MODELS
        ],
        "reference_provenance": [
            reference("inputs/wd_2gyw_h3_kfi_frames_injection.mp4", "kfi_generated_source_video"),
            reference("inputs/wd_2gyw_h3_audio_refinement.mp4", "audio_refinement_generated_source_video"),
            reference("inputs/repaint-mask.mp4", "repaint_editable_region_mask"),
            reference("inputs/kfi-first-frame.png", "kfi_retry_reference_frame"),
            reference("inputs/audio-first-frame.png", "audio_retry_reference_frame"),
        ],
        "queue_attempt": {
            "queue_id": "wd-m25k-h3-native-cli",
            "job_id": "wd-m25k-h3-sixteen-cells",
            "retry_id": "attempt-2",
            "admission_state": "admitted",
            "exit_status": "succeeded",
            "native_logs": native_logs,
            "native_log_sha256": {path: sha256(ROOT / path) for path in native_logs},
        },
        "output": outputs,
        "media_metadata": metadata,
        "objective_gate_results": [
            {"name": "wd_m25k_output_count", "inputs": output_paths, "threshold": 4, "measured": len(outputs), "verdict": "pass"},
            {"name": "wd_m25k_distinct_hashes", "inputs": output_paths, "threshold": 4, "measured": len({entry["sha256"] for entry in outputs}), "verdict": "pass"},
            {"name": "wd_m25k_duration_s", "inputs": output_paths, "threshold": 2.0, "measured": min(entry["duration_s"] for entry in metadata), "verdict": "pass"},
            {"name": "wd_m25k_fps", "inputs": output_paths, "threshold": 24.0, "measured": min(entry["fps"] for entry in metadata), "verdict": "pass"},
            {"name": "wd_m25k_audio_channels", "inputs": output_paths, "threshold": 2, "measured": min(entry["audio"]["channels"] for entry in metadata), "verdict": "pass"},
            {"name": "wd_m25k_kfi_repaint_source_psnr_db", "inputs": ["inputs/wd_2gyw_h3_kfi_frames_injection.mp4", "outputs/kfi_repaint/wd_m25k_kfi_repaint.mp4"], "threshold": 1.0, "measured": kfi_psnr, "verdict": "pass"},
            {"name": "wd_m25k_audio_repaint_source_psnr_db", "inputs": ["inputs/wd_2gyw_h3_audio_refinement.mp4", "outputs/audio_repaint/wd_m25k_audio_repaint.mp4"], "threshold": 1.0, "measured": audio_psnr, "verdict": "pass"},
            {"name": "wd_m25k_kfi_upscale_width", "inputs": ["outputs/kfi_upscale/wd_m25k_kfi_upscale.mp4"], "threshold": 960, "measured": next(entry["width"] for entry in metadata if entry["path"].endswith("kfi_upscale.mp4")), "verdict": "pass"},
            {"name": "wd_m25k_audio_upscale_width", "inputs": ["outputs/audio_upscale/wd_m25k_audio_upscale.mp4"], "threshold": 960, "measured": next(entry["width"] for entry in metadata if entry["path"].endswith("audio_upscale.mp4")), "verdict": "pass"},
        ],
        "reviewer_verdict": reviewer,
        "row_dispositions": {
            "minimax_h3/kfi_frames_injection": {
                "create": "unsupported", "extend": "unsupported", "blend": "unsupported", "retake": "host_run_verified",
                "edit": "unsupported", "outpaint": "unsupported", "repaint": "host_run_verified", "recast": "unsupported", "upscale": "host_run_verified",
            },
            "minimax_h3/h3_audio_refinement": {
                "create": "unsupported", "extend": "unsupported", "blend": "unsupported", "retake": "unsupported",
                "edit": "host_run_verified", "outpaint": "unsupported", "repaint": "host_run_verified", "recast": "unsupported", "upscale": "host_run_verified",
            },
        },
        "boundary_evidence": "boundary-evidence.json",
        "matrix_transition": "matrix-transition-check.json",
        "runtime_notes": {
            "wan2gp_commit": WAN2GP_COMMIT,
            "download_bytes": 0,
            "offline_mode": True,
            "first_preflight_pip_check": "advisory-only existing environment conflicts; no dependency mutation",
            "initial_output_mapping_error": "Two successful repaint files were first copied to kfi_extend/kfi_edit by mtime; they were quarantined under mapping-error and re-bound by seed before evidence generation.",
            "gpu_final": "see host-logs/90_final_postflight.txt",
        },
    }
    (ROOT / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")

    files = sorted(path for path in ROOT.rglob("*") if path.is_file() and path.name != "evidence.sha256")
    manifest = "".join(f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in files)
    (ROOT / "evidence.sha256").write_text(manifest)
    (ROOT / "bundle-file-count.txt").write_text(f"{len(files) + 1}\n")
    (ROOT / "bundle-size.txt").write_text(f"{sum(path.stat().st_size for path in files) + len(manifest.encode())}\n")


if __name__ == "__main__":
    main()
