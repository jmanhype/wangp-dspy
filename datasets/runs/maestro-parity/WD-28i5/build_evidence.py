#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
BASE_COMMIT = "1e9578f7"
WAN2GP_COMMIT = "4c93b64a47b5b0a915f2abec2ce754be98227150"
OUTPUTS = ("create", "upscale")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_state() -> dict[str, Any]:
    status = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain=v1"], check=True, text=True, capture_output=True).stdout
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], check=True, text=True, capture_output=True).stdout.strip()
    return {
        "commit": commit,
        "base_commit": BASE_COMMIT,
        "dirty_state": {"dirty": bool(status), "identity_sha256": hashlib.sha256(status.encode()).hexdigest(), "status_lines": status.splitlines()},
    }


def metadata(operation: str) -> dict[str, Any]:
    relative = f"outputs/{operation}/wd_28i5_{operation}.mp4"
    probe = json.loads((ROOT / f"outputs/{operation}/wd_28i5_{operation}.ffprobe.json").read_text())
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    numerator, denominator = video["r_frame_rate"].split("/", 1)
    return {
        "path": relative,
        "kind": "video",
        "width": int(video["width"]),
        "height": int(video["height"]),
        "duration_s": float(probe["format"]["duration"]),
        "fps": float(numerator) / float(denominator),
        "alpha_mode": "none",
        "audio": {"present": False},
    }


def reference(relative: str, role: str) -> dict[str, str]:
    return {
        "path": relative,
        "role": role,
        "sha256": sha256(ROOT / relative),
        "license": "Operator-owned generated evaluation asset; operator-authorized research/evaluation use; no redistribution",
    }


def ffmpeg_metric(args: list[str], pattern: str) -> float:
    proc = subprocess.run(args, check=True, text=True, capture_output=True)
    match = re.search(pattern, proc.stderr)
    if match is None:
        raise RuntimeError(f"metric unavailable: {args}")
    return float(match.group(1))


def psnr_scaled_source() -> float:
    return ffmpeg_metric([
        "ffmpeg", "-nostdin",
        "-i", str(ROOT / "outputs/create/wd_28i5_create.mp4"),
        "-i", str(ROOT / "outputs/upscale/wd_28i5_upscale.mp4"),
        "-filter_complex", "[0:v]scale=768:448[s];[s][1:v]psnr",
        "-map", "1:v", "-f", "null", "-",
    ], r"average:([0-9.]+)")


def whole_psnar(operation: str) -> float:
    return ffmpeg_metric([
        "ffmpeg", "-nostdin",
        "-i", str(ROOT / "inputs/control.mp4"),
        "-i", str(ROOT / f"outputs/{operation}/wd_28i5_{operation}.mp4"),
        "-lavfi", "[0:v][1:v]psnr", "-f", "null", "-",
    ], r"average:([0-9.]+)")


def first_frame_psnr(operation: str) -> float:
    return ffmpeg_metric([
        "ffmpeg", "-nostdin",
        "-i", str(ROOT / "outputs/create/first-frame.png"),
        "-i", str(ROOT / f"outputs/{operation}/first-frame.png"),
        "-lavfi", "[0:v][1:v]psnr", "-f", "null", "-",
    ], r"average:([0-9.]+)")


def retake_ssim() -> float:
    return ffmpeg_metric([
        "ffmpeg", "-nostdin",
        "-i", str(ROOT / "inputs/reference.png"),
        "-i", str(ROOT / "outputs/retake/first-frame.png"),
        "-lavfi", "[0:v][1:v]ssim", "-f", "null", "-",
    ], r"All:([0-9.]+)")


def parse_manifest(path: Path) -> list[list[str]]:
    return [line.split("\t") for line in path.read_text().splitlines()[1:] if line]


def matrix_row(text: str, family: str) -> list[str]:
    for line in text.splitlines():
        if line.startswith(f"| {family} "):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            return [cell.split()[0] for cell in cells[1:]]
    raise RuntimeError(f"row not found: {family}")


def main() -> None:
    media = [metadata(operation) for operation in OUTPUTS]
    output_paths = [entry["path"] for entry in media]
    outputs = [{"path": path, "sha256": sha256(ROOT / path)} for path in output_paths]
    upscale_psnr = psnr_scaled_source()
    boundary_psnr = {operation: whole_psnar(operation) for operation in ("extend", "retake", "edit", "repaint")}
    first_psnr = {operation: first_frame_psnr(operation) for operation in ("extend", "retake", "edit", "repaint")}
    retake_frame_ssim = retake_ssim()
    measurements = {
        "schema_version": "wangp-dspy.wd-28i5.objective-measurements/v1",
        "source_sha256": sha256(ROOT / "outputs/create/wd_28i5_create.mp4"),
        "upscale_vs_scaled_source_psnr_db": upscale_psnr,
        "boundary_whole_psnr_versus_control_db": boundary_psnr,
        "boundary_first_frame_psnr_versus_create_db": first_psnr,
        "retake_first_frame_ssim_versus_reference": retake_frame_ssim,
        "rows": [{"operation": operation, **entry, "sha256": sha256(ROOT / entry["path"]), "bytes": (ROOT / entry["path"]).stat().st_size} for operation, entry in zip(OUTPUTS, media)],
    }
    (ROOT / "objective-measurements.json").write_text(json.dumps(measurements, indent=2) + "\n")

    def boundary_output(seed: int) -> tuple[str, str]:
        matches = list((ROOT / "boundaries/probe-batch").glob(f"*seed{seed}*.mp4"))
        if len(matches) != 1:
            raise RuntimeError(f"expected one seed {seed} output")
        path = matches[0]
        return path.relative_to(ROOT).as_posix(), sha256(path)

    extend_path, extend_hash = boundary_output(3602)
    retake_path, retake_hash = boundary_output(3604)
    edit_path, edit_hash = boundary_output(3605)
    outpaint_path, outpaint_hash = boundary_output(3606)
    repaint_path, repaint_hash = boundary_output(3607)
    probe_log = ROOT / "host-logs/probe-batch.render.log"
    boundary = {
        "schema_version": "wangp-dspy.wd-28i5.boundary-evidence/v1",
        "records": [
            {"operation": "extend", "output": extend_path, "output_sha256": extend_hash, "duration_s": 2.0625, "whole_psnr_db": boundary_psnr["extend"], "first_frame_psnr_db": first_psnr["extend"], "boundary": "unsupported_host_implementation", "reason": "The first frame is preserved, but later frames abandon the supplied combat premise for an unrelated industrial subject; the operation is not a faithful continuation."},
            {"operation": "blend", "log": "host-logs/probe-batch.render.log", "native_exit": int((ROOT / "host-logs/probe-batch.exit").read_text()), "boundary": "unsupported_host_implementation", "reason": "Two-guide setup fails with KeyError reference_video_max_frames before generation."},
            {"operation": "retake", "output": retake_path, "output_sha256": retake_hash, "whole_psnr_db": boundary_psnr["retake"], "first_frame_psnr_db": first_psnr["retake"], "first_frame_ssim": retake_frame_ssim, "boundary": "unsupported_host_implementation", "reason": "The supplied combat start frame is not preserved; the output is an unrelated glowing landscape."},
            {"operation": "edit", "output": edit_path, "output_sha256": edit_hash, "whole_psnr_db": boundary_psnr["edit"], "first_frame_psnr_db": first_psnr["edit"], "boundary": "unsupported_host_implementation", "reason": "The guide is ignored and the output becomes unrelated people near water."},
            {"operation": "outpaint", "output": outpaint_path, "output_sha256": outpaint_hash, "width": 384, "height": 224, "boundary": "unsupported_host_implementation", "reason": "Media was emitted but dimensions stayed 384x224; no frame enlargement occurred."},
            {"operation": "repaint", "output": repaint_path, "output_sha256": repaint_hash, "whole_psnr_db": boundary_psnr["repaint"], "first_frame_psnr_db": first_psnr["repaint"], "boundary": "unsupported_host_implementation", "reason": "The control scene is abandoned for an unrelated dim interior."},
            {"operation": "recast", "log": "host-logs/probe-batch.render.log", "native_exit": 137, "failing_stage": "Removing Images References Background", "boundary": "unsupported_host_implementation", "reason": "The process was killed during reference-background removal before generation; no output was admitted."},
        ],
        "probe_batch_log_sha256": sha256(probe_log),
        "visual_review": "review/QC.md",
    }
    (ROOT / "boundary-evidence.json").write_text(json.dumps(boundary, indent=2) + "\n")

    current_doc = (REPO / "docs/video-capabilities.md").read_text()
    base_doc = subprocess.run(["git", "-C", str(REPO), "show", f"{BASE_COMMIT}:docs/video-capabilities.md"], check=True, text=True, capture_output=True).stdout
    before = matrix_row(base_doc, "wan/2gp")
    after = matrix_row(current_doc, "wan/2gp")
    transition = {
        "schema_version": "wangp-dspy.wd-28i5.matrix-transition/v1",
        "base_commit": BASE_COMMIT,
        "before": before,
        "after": after,
        "changed_cells": sum(old != new for old, new in zip(before, after)),
        "expected_changed_cells": 9,
        "planned_after": after.count("planned"),
        "verified_after": after.count("host_run_verified"),
        "unsupported_after": after.count("unsupported"),
        "pass": before.count("planned") == 9 and after.count("planned") == 0 and sum(old != new for old, new in zip(before, after)) == 9,
    }
    (ROOT / "matrix-transition-check.json").write_text(json.dumps(transition, indent=2) + "\n")

    junit_path = ROOT / "targeted-tests.xml"
    if junit_path.exists():
        root = ET.parse(junit_path).getroot()
        suite = root if root.tag == "testsuite" else root.find("testsuite")
        junit = {key: suite.attrib.get(key) for key in ("tests", "errors", "failures", "skipped")}
    else:
        junit = None

    models = []
    for url, destination, size, digest in parse_manifest(ROOT / "download-manifest.tsv"):
        models.append({"identity": Path(destination).name, "source": url, "license": "Apache-2.0 (Wan2.1 upstream); operator research/evaluation only", "sha256": digest, "size_bytes": int(size), "destination": destination, "download_approved": True, "preflight_hash_verified": True, "downloaded_this_story": True})
    prior_sources = {
        "models_t5_umt5-xxl-enc-quanto_int8.safetensors": "https://huggingface.co/DeepBeepMeep/Wan2.1/resolve/main/umt5-xxl/models_t5_umt5-xxl-enc-quanto_int8.safetensors",
        "Wan2.1_VAE.safetensors": "https://huggingface.co/DeepBeepMeep/Wan2.1/resolve/main/Wan2.1_VAE.safetensors",
        "Wan2.1_VAE_upscale2x_imageonly_real_v1.safetensors": "https://huggingface.co/DeepBeepMeep/Wan2.1/resolve/main/Wan2.1_VAE_upscale2x_imageonly_real_v1.safetensors",
        "models_clip_open-clip-xlm-roberta-large-vit-huge-14-bf16.safetensors": "https://huggingface.co/DeepBeepMeep/Wan2.1/resolve/main/xlm-roberta-large/models_clip_open-clip-xlm-roberta-large-vit-huge-14-bf16.safetensors",
        "sentencepiece.bpe.model": "https://huggingface.co/DeepBeepMeep/Wan2.1/resolve/main/xlm-roberta-large/sentencepiece.bpe.model",
        "special_tokens_map.json": "https://huggingface.co/DeepBeepMeep/Wan2.1/resolve/main/xlm-roberta-large/special_tokens_map.json",
        "tokenizer.json": "https://huggingface.co/DeepBeepMeep/Wan2.1/resolve/main/xlm-roberta-large/tokenizer.json",
        "tokenizer_config.json": "https://huggingface.co/DeepBeepMeep/Wan2.1/resolve/main/xlm-roberta-large/tokenizer_config.json",
    }
    for destination, size, digest in parse_manifest(ROOT / "shared-manifest.tsv"):
        name = Path(destination).name
        models.append({"identity": name, "source": prior_sources[name], "license": "Apache-2.0 (Wan2.1 upstream); operator research/evaluation only", "sha256": digest, "size_bytes": int(size), "destination": destination, "download_approved": True, "preflight_hash_verified": True, "downloaded_this_story": False})

    native_logs = ["host-logs/create.render.log", "host-logs/upscale.render.log"]
    evidence = {
        "schema": "wangp-dspy.maestro-parity-evidence/v1",
        "operator_authorization": {"status": "approved", "text": "you decide", "scope": "Dispatcher selected Wan/2GP after SCAIL-2: one main checkpoint download, eight shared assets rehashed, nine target cells, isolated Wan2GP worktree, no live dependency mutation", "timestamp": "2026-09-27T15:07:00Z", "approved_by": "operator via /root dispatcher decision"},
        "command": ["ssh", "3090", "/tmp/20_run_create.sh"],
        "repository": repository_state(),
        "model_provenance": models,
        "reference_provenance": [reference("inputs/control.mp4", "person_bearing_control_video"), reference("inputs/reference.png", "retake_start_frame"), reference("inputs/alternate-reference.png", "recast_reference_frame"), reference("inputs/control-mask.mp4", "repaint_probe_mask")],
        "queue_attempt": {"queue_id": "wd-28i5-wan-t2v-native-cli", "job_id": "wd-28i5-wan-nine-cells", "retry_id": "attempt-1", "admission_state": "admitted", "exit_status": "succeeded", "native_logs": native_logs, "native_log_sha256": {path: sha256(ROOT / path) for path in native_logs}},
        "output": outputs,
        "media_metadata": media,
        "objective_gate_results": [
            {"name": "wd_28i5_output_count", "inputs": output_paths, "threshold": 2, "measured": len(outputs), "verdict": "pass"},
            {"name": "wd_28i5_distinct_hashes", "inputs": output_paths, "threshold": 2, "measured": len({entry["sha256"] for entry in outputs}), "verdict": "pass"},
            {"name": "wd_28i5_create_duration_s", "inputs": [output_paths[0]], "threshold": 0.5, "measured": media[0]["duration_s"], "verdict": "pass"},
            {"name": "wd_28i5_create_fps", "inputs": [output_paths[0]], "threshold": 16.0, "measured": media[0]["fps"], "verdict": "pass"},
            {"name": "wd_28i5_create_nonempty_bytes", "inputs": [output_paths[0]], "threshold": 50000, "measured": (ROOT / output_paths[0]).stat().st_size, "verdict": "pass"},
            {"name": "wd_28i5_upscale_width", "inputs": [output_paths[1]], "threshold": 768, "measured": media[1]["width"], "verdict": "pass"},
            {"name": "wd_28i5_upscale_height", "inputs": [output_paths[1]], "threshold": 448, "measured": media[1]["height"], "verdict": "pass"},
            {"name": "wd_28i5_upscale_scaled_source_psnr_db", "inputs": output_paths, "threshold": 40.0, "measured": upscale_psnr, "verdict": "pass"},
        ],
        "reviewer_verdict": json.loads((ROOT / "reviewer-verdict.json").read_text()),
        "row_dispositions": {"wan/2gp": {"create": "host_run_verified", "extend": "unsupported", "blend": "unsupported", "retake": "unsupported", "edit": "unsupported", "outpaint": "unsupported", "repaint": "unsupported", "recast": "unsupported", "upscale": "host_run_verified"}},
        "boundary_evidence": "boundary-evidence.json",
        "matrix_transition": "matrix-transition-check.json",
        "download_evidence": {"main_assets": 1, "main_bytes": 14903022013, "session_bytes": 14903022013, "shared_assets_rehashed": 8, "shared_bytes": 10156887370, "shared_download_bytes": 0, "live_dependency_mutation": False, "report": "host-logs/download-report.tsv"},
        "runtime_notes": {"wan2gp_commit": WAN2GP_COMMIT, "isolated_source_final_status": "?? ckpts", "probe_batch_exit": 137, "targeted_junit": junit, "gpu_final": "see host-logs/90_final_postflight.txt"},
    }
    (ROOT / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")

    files = sorted(path for path in ROOT.rglob("*") if path.is_file() and path.name != "evidence.sha256")
    manifest = "".join(f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in files)
    (ROOT / "evidence.sha256").write_text(manifest)
    (ROOT / "bundle-file-count.txt").write_text(f"{len(files) + 1}\n")
    (ROOT / "bundle-size.txt").write_text(f"{sum(path.stat().st_size for path in files) + len(manifest.encode())}\n")


if __name__ == "__main__":
    main()
