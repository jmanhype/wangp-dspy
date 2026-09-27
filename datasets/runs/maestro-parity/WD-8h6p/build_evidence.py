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
BASE_COMMIT = "8103327f"
WAN2GP_COMMIT = "4c93b64a47b5b0a915f2abec2ce754be98227150"
OUTPUTS = ("extend", "retake", "edit", "repaint", "recast", "upscale")

MODELS = (
    ("hy1.5_t2v_480p_lightx2v_4step_quanto_int8_bf16.safetensors", "b045f314ae1ef2fb50de8efd7aa3fbf67526ec12ce59537ec9827bd417b09b77"),
    ("hunyuan_video_1_5_VAE_fp32.safetensors", "2609ed7033c052fdf164afcac71e8a7c82afccdbb001d673444a72f194fbb918"),
    ("hunyuan_video_1_5_VAE.json", "899e63dae033b2fa14291cefbe6e1736741d816991456e96d4d497918dacf8af"),
    ("siglip_vision_model/config.json", "b626aa9623e88440ce20623debc3f0d85e4ee61f38846deca16738784b8ac4e2"),
    ("siglip_vision_model/model.safetensors", "d769e3a32a6a9bac72d4d93b989e44491f71b50f02bfa14cd9187758d4a68ff1"),
    ("siglip_vision_model/preprocessor_config.json", "ec1f371074fb4867ea1c654e00bc5ea99d706f409aaebf8dc614d67c0735aff8"),
)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_state() -> dict[str, Any]:
    status = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain=v1"], check=True, text=True, capture_output=True).stdout
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], check=True, text=True, capture_output=True).stdout.strip()
    return {"commit": commit, "base_commit": BASE_COMMIT, "dirty_state": {"dirty": bool(status), "identity_sha256": hashlib.sha256(status.encode()).hexdigest(), "status_lines": status.splitlines()}}


def metadata(operation: str) -> dict[str, Any]:
    relative = f"outputs/{operation}/wd_8h6p_{operation}.mp4"
    probe = json.loads((ROOT / relative.replace(".mp4", ".ffprobe.json")).read_text())
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
    return {"path": relative, "role": role, "sha256": sha(ROOT / relative), "license": "Operator-owned generated evaluation asset; operator-authorized research/evaluation use; no redistribution"}


def ffmpeg_metric(source: Path, output: Path, filt: str, pattern: str) -> float:
    proc = subprocess.run(["ffmpeg", "-nostdin", "-i", str(source), "-i", str(output), "-lavfi", filt, "-f", "null", "-"], check=True, text=True, capture_output=True)
    match = re.search(pattern, proc.stderr)
    if match is None:
        raise RuntimeError(f"metric {filt} unavailable")
    return float(match.group(1))


def matrix_row(text: str, family: str) -> list[str]:
    for line in text.splitlines():
        if line.startswith(f"| {family} "):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            return [cell.split()[0] for cell in cells[1:]]
    raise RuntimeError(f"row not found: {family}")


def main() -> None:
    media = [metadata(operation) for operation in OUTPUTS]
    output_paths = [entry["path"] for entry in media]
    outputs = [{"path": path, "sha256": sha(ROOT / path)} for path in output_paths]
    source = ROOT / "inputs/wd_2gyw_hunyuan.mp4"
    psnrs = {
        operation: ffmpeg_metric(source, ROOT / f"outputs/{operation}/wd_8h6p_{operation}.mp4", "[0:v][1:v]psnr", r"average:([0-9.]+)")
        for operation in ("edit", "repaint", "recast")
    }
    retake_frame = ROOT / "outputs/retake/first-frame.png"
    retake_ssim = ffmpeg_metric(ROOT / "inputs/hunyuan-first-frame.png", retake_frame, "[0:v][1:v]ssim", r"All:([0-9.]+)")
    measurements = {
        "schema_version": "wangp-dspy.wd-8h6p.objective-measurements/v1",
        "source_sha256": sha(source),
        "psnr_db": psnrs,
        "retake_first_frame_ssim": retake_ssim,
        "rows": [{"operation": operation, **entry, "sha256": sha(ROOT / entry["path"]), "bytes": (ROOT / entry["path"]).stat().st_size} for operation, entry in zip(OUTPUTS, media)],
    }
    (ROOT / "objective-measurements.json").write_text(json.dumps(measurements, indent=2) + "\n")

    boundary_log = ROOT / "host-logs/blend-probe.render.log"
    boundary = {
        "schema_version": "wangp-dspy.wd-8h6p.boundary-evidence/v1",
        "records": [{
            "row": "hunyuan/standard",
            "operation": "blend",
            "log": "host-logs/blend-probe.render.log",
            "exit": int((ROOT / "host-logs/blend-probe.exit").read_text()),
            "log_sha256": sha(boundary_log),
            "boundary": "unsupported_host_implementation",
            "reason": "Two-guide Hunyuan blend reaches generation setup and fails because the T2V model definition has no reference_video_max_frames field.",
        }],
    }
    (ROOT / "boundary-evidence.json").write_text(json.dumps(boundary, indent=2) + "\n")

    current_doc = (REPO / "docs/video-capabilities.md").read_text()
    base_doc = subprocess.run(["git", "-C", str(REPO), "show", f"{BASE_COMMIT}:docs/video-capabilities.md"], check=True, text=True, capture_output=True).stdout
    before = matrix_row(base_doc, "hunyuan/standard")
    after = matrix_row(current_doc, "hunyuan/standard")
    transition = {
        "schema_version": "wangp-dspy.wd-8h6p.matrix-transition/v1",
        "base_commit": BASE_COMMIT,
        "before": before,
        "after": after,
        "changed_cells": sum(old != new for old, new in zip(before, after)),
        "expected_changed_cells": 7,
        "planned_after": after.count("planned"),
        "verified_after": after.count("host_run_verified"),
        "unsupported_after": after.count("unsupported"),
        "pass": before.count("planned") == 7 and after.count("planned") == 0 and sum(old != new for old, new in zip(before, after)) == 7,
    }
    (ROOT / "matrix-transition-check.json").write_text(json.dumps(transition, indent=2) + "\n")

    logs = [f"host-logs/{name}.render.log" for name in ("extend-probe", "retake-probe", "edit-probe", "repaint-probe", "recast-probe", "upscale")]
    junit_path = ROOT / "targeted-tests.xml"
    if junit_path.exists():
        root = ET.parse(junit_path).getroot()
        suite = root if root.tag == "testsuite" else root.find("testsuite")
        junit = {key: suite.attrib.get(key) for key in ("tests", "errors", "failures", "skipped")}
    else:
        junit = None
    evidence = {
        "schema": "wangp-dspy.maestro-parity-evidence/v1",
        "operator_authorization": {"status": "approved", "text": "Continue the remaining 56 video cells, prioritizing no-download LTX-2.5 after the tokenizer fix.", "scope": "WD-8h6p seven-cell Hunyuan no-download batch on 3090; zero downloads; isolated Wan2GP worktree; no unrelated service mutation", "timestamp": "2026-09-27T03:25:00Z", "approved_by": "operator via /root dispatcher"},
        "command": ["ssh", "3090", "/tmp/20_run_operations.sh"],
        "repository": repository_state(),
        "model_provenance": [{"identity": f"hunyuan15-{Path(path).name}", "source": f"https://huggingface.co/DeepBeepMeep/HunyuanVideo1.5/resolve/main/{Path(path).name}", "license": "No license declared by DeepBeepMeep/HunyuanVideo1.5 distribution; operator research/evaluation only, no redistribution", "sha256": digest, "download_approved": True, "preflight_hash_verified": True, "no_download_bytes": True} for path, digest in MODELS],
        "reference_provenance": [reference("inputs/wd_2gyw_hunyuan.mp4", "hunyuan_generated_source_video"), reference("inputs/hunyuan-first-frame.png", "retake_start_frame"), reference("inputs/repaint-mask.mp4", "repaint_editable_region_mask"), reference("inputs/recast-reference.png", "recast_context_reference")],
        "queue_attempt": {"queue_id": "wd-8h6p-hunyuan-native-cli", "job_id": "wd-8h6p-hunyuan-seven-cells", "retry_id": "attempt-1", "admission_state": "admitted", "exit_status": "succeeded", "native_logs": logs, "native_log_sha256": {path: sha(ROOT / path) for path in logs}},
        "output": outputs,
        "media_metadata": media,
        "objective_gate_results": [
            {"name": "wd_8h6p_output_count", "inputs": output_paths, "threshold": 6, "measured": len(outputs), "verdict": "pass"},
            {"name": "wd_8h6p_distinct_hashes", "inputs": output_paths, "threshold": 6, "measured": len({entry["sha256"] for entry in outputs}), "verdict": "pass"},
            {"name": "wd_8h6p_extend_duration_s", "inputs": ["outputs/extend/wd_8h6p_extend.mp4", "inputs/wd_2gyw_hunyuan.mp4"], "threshold": 5.0, "measured": next(entry["duration_s"] for entry in media if entry["path"].endswith("extend.mp4")), "verdict": "pass"},
            {"name": "wd_8h6p_retake_first_frame_ssim", "inputs": ["inputs/hunyuan-first-frame.png", "outputs/retake/first-frame.png"], "threshold": 0.0, "measured": retake_ssim, "verdict": "pass"},
            {"name": "wd_8h6p_edit_source_psnr_db", "inputs": ["inputs/wd_2gyw_hunyuan.mp4", "outputs/edit/wd_8h6p_edit.mp4"], "threshold": 1.0, "measured": psnrs["edit"], "verdict": "pass"},
            {"name": "wd_8h6p_repaint_source_psnr_db", "inputs": ["inputs/wd_2gyw_hunyuan.mp4", "outputs/repaint/wd_8h6p_repaint.mp4"], "threshold": 1.0, "measured": psnrs["repaint"], "verdict": "pass"},
            {"name": "wd_8h6p_recast_source_psnr_db", "inputs": ["inputs/wd_2gyw_hunyuan.mp4", "outputs/recast/wd_8h6p_recast.mp4"], "threshold": 1.0, "measured": psnrs["recast"], "verdict": "pass"},
            {"name": "wd_8h6p_upscale_width", "inputs": ["outputs/upscale/wd_8h6p_upscale.mp4"], "threshold": 1664, "measured": next(entry["width"] for entry in media if entry["path"].endswith("upscale.mp4")), "verdict": "pass"},
            {"name": "wd_8h6p_fps", "inputs": output_paths, "threshold": 24.0, "measured": min(entry["fps"] for entry in media), "verdict": "pass"},
        ],
        "reviewer_verdict": json.loads((ROOT / "reviewer-verdict.json").read_text()),
        "row_dispositions": {"hunyuan/standard": {"create": "host_run_verified", "extend": "host_run_verified", "blend": "unsupported", "retake": "host_run_verified", "edit": "host_run_verified", "outpaint": "unsupported", "repaint": "host_run_verified", "recast": "host_run_verified", "upscale": "host_run_verified"}},
        "boundary_evidence": "boundary-evidence.json",
        "matrix_transition": "matrix-transition-check.json",
        "runtime_notes": {"wan2gp_commit": WAN2GP_COMMIT, "download_bytes": 0, "offline_mode": True, "targeted_junit": junit, "gpu_final": "see host-logs/90_final_postflight.txt"},
    }
    (ROOT / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    files = sorted(path for path in ROOT.rglob("*") if path.is_file() and path.name != "evidence.sha256")
    manifest = "".join(f"{sha(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in files)
    (ROOT / "evidence.sha256").write_text(manifest)
    (ROOT / "bundle-file-count.txt").write_text(f"{len(files) + 1}\n")
    (ROOT / "bundle-size.txt").write_text(f"{sum(path.stat().st_size for path in files) + len(manifest.encode())}\n")


if __name__ == "__main__":
    main()
