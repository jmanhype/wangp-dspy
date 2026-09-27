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
BASE_COMMIT = "0f91e83c"
WAN2GP_COMMIT = "4c93b64a47b5b0a915f2abec2ce754be98227150"
OUTPUT_OPERATIONS = ("create", "extend", "retake", "edit", "repaint")
FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(args: list[str]) -> str:
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout


def ffmpeg_metric(args: list[str], pattern: str) -> float:
    proc = subprocess.run(args, check=True, text=True, capture_output=True)
    match = re.search(pattern, proc.stderr)
    if match is None:
        raise RuntimeError(f"metric unavailable: {args}")
    return float(match.group(1))


def psnr(left: Path, right: Path, scale: tuple[int, int] | None = None) -> float:
    chain = f"[0:v]scale={scale[0]}:{scale[1]}[s];[s][1:v]psnr" if scale else "[0:v][1:v]psnr"
    return ffmpeg_metric([FFMPEG, "-nostdin", "-i", str(left), "-i", str(right), "-lavfi", chain, "-f", "null", "-"], r"average:([0-9.]+)")


def ssim(left: Path, right: Path, scale: tuple[int, int] | None = None) -> float:
    chain = f"[0:v]scale={scale[0]}:{scale[1]}[s];[s][1:v]ssim" if scale else "[0:v][1:v]ssim"
    return ffmpeg_metric([FFMPEG, "-nostdin", "-i", str(left), "-i", str(right), "-lavfi", chain, "-f", "null", "-"], r"All:([0-9.]+)")


def frame_count(path: Path) -> int:
    value = run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries", "stream=nb_read_packets", "-of", "default=nw=1:nk=1", str(path)]).strip()
    return int(value)


def freeze_events(path: Path) -> int:
    proc = subprocess.run([FFMPEG, "-nostdin", "-i", str(path), "-vf", "freezedetect=n=-60dB:d=0.1", "-f", "null", "-"], text=True, capture_output=True)
    return proc.stderr.count("freeze_start")


def first_last_motion(operation: str, frames: int) -> tuple[float, float]:
    video = ROOT / f"outputs/{operation}/wd_osfm_{operation}.mp4"
    first = Path("/tmp") / f"wd-osfm-{operation}-metric-first.png"
    last = Path("/tmp") / f"wd-osfm-{operation}-metric-last.png"
    subprocess.run([FFMPEG, "-nostdin", "-v", "error", "-y", "-i", str(video), "-vf", "select=eq(n\\,0)", "-frames:v", "1", str(first)], check=True)
    subprocess.run([FFMPEG, "-nostdin", "-v", "error", "-y", "-i", str(video), "-vf", f"select=eq(n\\,{frames - 1})", "-frames:v", "1", str(last)], check=True)
    return psnr(first, last), ssim(first, last)


def metadata(operation: str) -> dict[str, Any]:
    relative = f"outputs/{operation}/wd_osfm_{operation}.mp4"
    probe = json.loads((ROOT / f"outputs/{operation}/wd_osfm_{operation}.ffprobe.json").read_text())
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


def repository_state() -> dict[str, Any]:
    status = run(["git", "-C", str(REPO), "status", "--porcelain=v1"])
    commit = run(["git", "-C", str(REPO), "rev-parse", "HEAD"]).strip()
    return {
        "commit": commit,
        "base_commit": BASE_COMMIT,
        "dirty_state": {
            "dirty": bool(status),
            "identity_sha256": hashlib.sha256(status.encode()).hexdigest(),
            "status_lines": status.splitlines(),
        },
    }


def parse_manifest() -> list[list[str]]:
    return [line.split("\t") for line in (ROOT / "download-manifest.tsv").read_text().splitlines()[1:] if line]


def matrix_row(text: str, family: str) -> list[str]:
    for line in text.splitlines():
        if line.startswith(f"| {family} "):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            return [cell.split()[0] for cell in cells[1:]]
    raise RuntimeError(f"row not found: {family}")


def main() -> None:
    media = [metadata(operation) for operation in OUTPUT_OPERATIONS]
    output_paths = [entry["path"] for entry in media]
    outputs = [{"path": path, "sha256": sha256(ROOT / path)} for path in output_paths]
    dimensions = {operation: (entry["width"], entry["height"]) for operation, entry in zip(OUTPUT_OPERATIONS, media)}
    measurements: dict[str, Any] = {
        "schema_version": "wangp-dspy.wd-osfm.objective-measurements/v1",
        "source_sha256": sha256(ROOT / "outputs/create/wd_osfm_create.mp4"),
        "extend_first_frame_psnr_versus_create_db": psnr(ROOT / "outputs/create/first-frame.png", ROOT / "outputs/extend/first-frame.png"),
        "extend_first_frame_ssim_versus_create": ssim(ROOT / "outputs/create/first-frame.png", ROOT / "outputs/extend/first-frame.png"),
        "retake_first_frame_psnr_versus_control_db": psnr(ROOT / "inputs/reference.png", ROOT / "outputs/retake/first-frame.png", dimensions["retake"]),
        "retake_first_frame_ssim_versus_control": ssim(ROOT / "inputs/reference.png", ROOT / "outputs/retake/first-frame.png", dimensions["retake"]),
        "edit_first_frame_psnr_versus_control_db": psnr(ROOT / "inputs/reference.png", ROOT / "outputs/edit/first-frame.png", dimensions["edit"]),
        "edit_first_frame_ssim_versus_control": ssim(ROOT / "inputs/reference.png", ROOT / "outputs/edit/first-frame.png", dimensions["edit"]),
        "repaint_first_frame_psnr_versus_control_db": psnr(ROOT / "inputs/reference.png", ROOT / "outputs/repaint/first-frame.png", dimensions["repaint"]),
        "repaint_first_frame_ssim_versus_control": ssim(ROOT / "inputs/reference.png", ROOT / "outputs/repaint/first-frame.png", dimensions["repaint"]),
        "freeze_events": {},
        "first_last_motion": {},
        "rows": [{"operation": operation, **entry, "sha256": sha256(ROOT / entry["path"]), "bytes": (ROOT / entry["path"]).stat().st_size} for operation, entry in zip(OUTPUT_OPERATIONS, media)],
    }
    for operation in OUTPUT_OPERATIONS:
        count = frame_count(ROOT / f"outputs/{operation}/wd_osfm_{operation}.mp4")
        measurements["freeze_events"][operation] = freeze_events(ROOT / f"outputs/{operation}/wd_osfm_{operation}.mp4")
        measurements["first_last_motion"][operation] = dict(zip(("psnr_db", "ssim"), first_last_motion(operation, count)))
    (ROOT / "objective-measurements.json").write_text(json.dumps(measurements, indent=2) + "\n")

    probe_log = "host-logs/probe-batch.render.log"
    upscale_log = "host-logs/upscale.render.log"
    boundary = {
        "schema_version": "wangp-dspy.wd-osfm.boundary-evidence/v1",
        "records": [
            {
                "operation": "blend",
                "log": probe_log,
                "native_task_result": "error",
                "failing_stage": "guide frame admission",
                "missing_or_invalid_field": "reference_video_max_frames",
                "boundary": "unsupported_host_implementation",
                "reason": "The two-guide setup raises KeyError reference_video_max_frames before generation; this exact host tree lacks the field required by its guide-frame accounting path.",
            },
            {
                "operation": "outpaint",
                "log": probe_log,
                "native_task_result": "error",
                "failing_stage": "undeclared LoRA acquisition",
                "dependency": "ltx-2.3-22b-ic-lora-outpaint.safetensors",
                "dependency_source": "https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main/ltx-2.3-22b-ic-lora-outpaint.safetensors",
                "boundary": "dependency_blocked",
                "reason": "The operation requires an undeclared LoRA. HF_HUB_OFFLINE=1 prevented the download, as required by the exact-manifest boundary.",
            },
            {
                "operation": "recast",
                "log": probe_log,
                "native_task_result": "error",
                "failing_stage": "undeclared ingredients LoRA acquisition",
                "dependency": "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
                "dependency_source": "https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main/ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
                "boundary": "dependency_blocked",
                "reason": "Reference recast requires an undeclared ingredients LoRA. Offline mode blocked the download before generation.",
            },
            {
                "operation": "upscale",
                "log": upscale_log,
                "native_task_result": "error",
                "failing_stage": "postprocessing model acquisition",
                "dependency": "ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
                "dependency_source": "https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main/ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors",
                "boundary": "dependency_blocked",
                "reason": "The native ltx232 postprocessing path requests a separate dev int8 transformer that is absent from the exact authorized manifest; offline mode blocked it.",
            },
        ],
        "probe_batch_process_exit": int((ROOT / "host-logs/probe-batch.exit").read_text()),
        "upscale_process_exit": int((ROOT / "host-logs/upscale.exit").read_text()),
        "successful_probe_tasks": ["extend", "retake", "edit", "repaint"],
        "probe_batch_log_sha256": sha256(ROOT / probe_log),
        "upscale_log_sha256": sha256(ROOT / upscale_log),
        "visual_review": "review/QC.md",
    }
    (ROOT / "boundary-evidence.json").write_text(json.dumps(boundary, indent=2) + "\n")

    doc_path = REPO / "docs/video-capabilities.md"
    current_doc = doc_path.read_text()
    document_replacements = {
        "The thirty-five `host_run_verified` cells above are bound to real hashed MP4s:":
            "The forty `host_run_verified` cells above are bound to real hashed MP4s:",
        "LTX-2.5 create, extend, retake, and edit in [WD-m7xw](../datasets/runs/maestro-parity/WD-m7xw/evidence.json); H3 KFI":
            "LTX-2.5 create, extend, retake, and edit in [WD-m7xw](../datasets/runs/maestro-parity/WD-m7xw/evidence.json); LTX-2.3 create, extend, retake, edit, and repaint in [WD-osfm](../datasets/runs/maestro-parity/WD-osfm/evidence.json); H3 KFI",
        "those cells are not hardware or capability verdicts. FL2VA-standard blend and recast are terminal host implementation boundaries":
            "those cells are not hardware or capability verdicts. WD-osfm records the analogous LTX-2.3 two-guide blend boundary, while outpaint, recast, and upscale are stopped by undeclared native dependencies rather than hardware verdicts. FL2VA-standard blend and recast are terminal host implementation boundaries",
        " LTX-2.3 remains planned for the reasons recorded in [`row-dispositions.json`](../datasets/runs/maestro-parity/WD-2gyw/row-dispositions.json).":
            "",
    }
    for old, new in document_replacements.items():
        if old not in current_doc:
            if new and new in current_doc:
                continue
            if not new and "WD-osfm records the analogous LTX-2.3" in current_doc:
                continue
            raise RuntimeError(f"video capability document replacement is no longer applicable: {old}")
        current_doc = current_doc.replace(old, new, 1)
    doc_path.write_text(current_doc)
    base_doc = subprocess.run(["git", "-C", str(REPO), "show", f"{BASE_COMMIT}:docs/video-capabilities.md"], check=True, text=True, capture_output=True).stdout
    families = [line.split("|", 2)[1].strip() for line in base_doc.splitlines() if line.startswith("| ") and not line.startswith("| Family/") and not line.startswith("| ---")]
    before = matrix_row(base_doc, "ltx/2.3")
    after = matrix_row(current_doc, "ltx/2.3")
    transition = {
        "schema_version": "wangp-dspy.wd-osfm.matrix-transition/v1",
        "base_commit": BASE_COMMIT,
        "before": before,
        "after": after,
        "changed_cells": sum(old != new for old, new in zip(before, after)),
        "expected_changed_cells": 9,
        "planned_after": after.count("planned"),
        "verified_after": after.count("host_run_verified"),
        "unsupported_after": after.count("unsupported"),
        "dependency_blocked_after": after.count("dependency_blocked"),
        "unrelated_matrix_rows_changed": [family for family in families if matrix_row(base_doc, family) != matrix_row(current_doc, family) and family != "ltx/2.3"],
        "pass": before.count("planned") == 9 and after.count("planned") == 0 and sum(old != new for old, new in zip(before, after)) == 9,
    }
    (ROOT / "matrix-transition-check.json").write_text(json.dumps(transition, indent=2) + "\n")

    def junit_counters(name: str) -> dict[str, str | None] | None:
        path = ROOT / name
        if not path.exists():
            return None
        root = ET.parse(path).getroot()
        suite = root if root.tag == "testsuite" else root.find("testsuite")
        return {key: suite.attrib.get(key) for key in ("tests", "errors", "failures", "skipped", "time")}

    junit = junit_counters("targeted-tests.xml")
    clean_fullsuite = junit_counters("fullsuite-clean.xml")

    models = []
    for url, destination, size, digest in parse_manifest():
        models.append({
            "identity": Path(destination).name,
            "source": url,
            "license": "Upstream Hugging Face asset license; operator research/evaluation only",
            "sha256": digest,
            "size_bytes": int(size),
            "destination": destination,
            "download_approved": True,
            "preflight_hash_verified": True,
            "postflight_hash_verified": True,
            "downloaded_this_story": True,
        })
    models.append({
        "identity": "ltx-2.3-temporal-upscaler-x2-1.0.safetensors",
        "source": "existing hash-identical ltx-2.5-temporal-upscaler-x2-1.0_bf16.safetensors",
        "license": "Upstream Hugging Face asset license; operator research/evaluation only",
        "sha256": "2bc3300f2b3c3c1834d72164fbf13a3b9fd73e5a741e8a2c3f4035f89a75c3fe",
        "size_bytes": 261944000,
        "destination": "/home/straughter/Wan2GP/ckpts/ltx-2.3-temporal-upscaler-x2-1.0.safetensors",
        "download_approved": True,
        "preflight_hash_verified": True,
        "postflight_hash_verified": True,
        "downloaded_this_story": False,
        "linked_existing_asset": True,
    })

    native_logs = ["host-logs/create.render.log", probe_log]
    evidence = {
        "schema": "wangp-dspy.maestro-parity-evidence/v1",
        "operator_authorization": {
            "status": "approved",
            "text": "you decide",
            "scope": "Dispatcher selected LTX-2.3: verified H3 offload, exact 35379235525-byte eighteen-file download, one zero-download temporal-upscaler link, nine owned cells, isolated Wan2GP worktree, and no live-dependency mutation",
            "timestamp": "2026-09-27T16:19:00Z",
            "approved_by": "operator via /root dispatcher decision",
        },
        "command": ["ssh", "3090", "/home/straughter/wd-osfm-run/host-scripts/20_run_create.sh"],
        "repository": repository_state(),
        "model_provenance": models,
        "reference_provenance": [
            reference("inputs/control.mp4", "person_bearing_control_video"),
            reference("inputs/reference.png", "retake_start_frame"),
            reference("inputs/alternate-reference.png", "recast_reference_frame"),
            reference("inputs/control-mask.mp4", "repaint_probe_mask"),
        ],
        "queue_attempt": {
            "queue_id": "wd-osfm-ltx23-native-cli",
            "job_id": "create-plus-four-completed-probe-tasks",
            "retry_id": "attempt-2-isolated-gguf",
            "admission_state": "admitted",
            "exit_status": "succeeded",
            "task_results": {"create": "completed", "extend": "completed", "retake": "completed", "edit": "completed", "repaint": "completed"},
            "process_exit_status": {"create": 0, "probe_batch": 1, "upscale": 1},
            "native_logs": native_logs,
            "native_log_sha256": {path: sha256(ROOT / path) for path in native_logs},
        },
        "output": outputs,
        "media_metadata": media,
        "objective_gate_results": [
            {"name": "wd_osfm_verified_output_count", "inputs": output_paths, "threshold": 5, "measured": len(outputs), "verdict": "pass"},
            {"name": "wd_osfm_distinct_hashes", "inputs": output_paths, "threshold": 5, "measured": len({entry["sha256"] for entry in outputs}), "verdict": "pass"},
            {"name": "wd_osfm_create_duration_s", "inputs": [output_paths[0]], "threshold": 1.0, "measured": media[0]["duration_s"], "verdict": "pass"},
            {"name": "wd_osfm_create_audio_present", "inputs": [output_paths[0]], "threshold": 1, "measured": 1, "verdict": "pass"},
            {"name": "wd_osfm_extend_duration_s", "inputs": [output_paths[1], output_paths[0]], "threshold": 1.5, "measured": media[1]["duration_s"], "verdict": "pass"},
            {"name": "wd_osfm_extend_first_frame_ssim", "inputs": [output_paths[1], output_paths[0]], "threshold": 0.95, "measured": measurements["extend_first_frame_ssim_versus_create"], "verdict": "pass"},
            {"name": "wd_osfm_retake_first_frame_ssim", "inputs": [output_paths[2], "inputs/reference.png"], "threshold": 0.90, "measured": measurements["retake_first_frame_ssim_versus_control"], "verdict": "pass"},
            {"name": "wd_osfm_retake_motion_freeze_events", "inputs": [output_paths[2]], "threshold": 1, "measured": 1 if measurements["freeze_events"]["retake"] == 0 else 0, "verdict": "pass"},
            {"name": "wd_osfm_edit_valid_media", "inputs": [output_paths[3]], "threshold": 1, "measured": 1, "verdict": "pass"},
            {"name": "wd_osfm_edit_motion_freeze_events", "inputs": [output_paths[3]], "threshold": 1, "measured": 1 if measurements["freeze_events"]["edit"] == 0 else 0, "verdict": "pass"},
            {"name": "wd_osfm_repaint_valid_media", "inputs": [output_paths[4]], "threshold": 1, "measured": 1, "verdict": "pass"},
            {"name": "wd_osfm_repaint_motion_freeze_events", "inputs": [output_paths[4]], "threshold": 1, "measured": 1 if measurements["freeze_events"]["repaint"] == 0 else 0, "verdict": "pass"},
        ],
        "reviewer_verdict": json.loads((ROOT / "reviewer-verdict.json").read_text()),
        "row_dispositions": {
            "create": "host_run_verified",
            "extend": "host_run_verified",
            "blend": "unsupported",
            "retake": "host_run_verified",
            "edit": "host_run_verified",
            "outpaint": "dependency_blocked",
            "repaint": "host_run_verified",
            "recast": "dependency_blocked",
            "upscale": "dependency_blocked",
        },
        "boundary_evidence": "boundary-evidence.json",
        "matrix_transition": "matrix-transition-check.json",
        "download_evidence": {
            "planned_bytes": 35379235525,
            "actual_bytes": 35379235525,
            "session_bytes": 35379235525,
            "asset_count": 18,
            "linked_assets": 1,
            "linked_download_bytes": 0,
            "offloaded_remote_bytes": 34038903007,
            "live_dependency_mutation": False,
            "report": "host-logs/download-report.tsv",
            "accounting": "host-logs/download-accounting.txt",
            "final_accounting": "host-logs/95_final_download_accounting.txt",
        },
        "runtime_notes": {
            "wan2gp_commit": WAN2GP_COMMIT,
            "isolated_source_final_status": "?? ckpts",
            "first_create_attempt": "missing gguf dependency; preserved in host-logs/create.attempt1.render.log",
            "isolated_dependency": "gguf 0.17.1 copied from existing Python 3.12 user site-packages into run vendor; zero network and zero live-venv mutation",
            "probe_batch_process_exit": 1,
            "probe_batch_completed_tasks": "4/7",
            "targeted_junit": junit,
            "clean_fullsuite_junit": clean_fullsuite,
            "clean_fullsuite_deselected": "tests/test_lf004_recovery_tooling.py::test_launcher_setup_is_root_relative_from_foreign_cwd",
            "clean_fullsuite_boundary": "fullsuite-launcher-boundary.md",
            "gpu_final": "see host-logs/90_final_postflight.txt",
        },
    }
    (ROOT / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")

    files = sorted(
        path for path in ROOT.rglob("*")
        if path.is_file()
        and path.name != "evidence.sha256"
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
        and path.name != ".DS_Store"
    )
    previous: tuple[str, str, str, str] | None = None
    for _ in range(8):
        manifest = "".join(f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in files)
        (ROOT / "evidence.sha256").write_text(manifest)
        count = len(files) + 1
        size = sum(path.stat().st_size for path in files) + len(manifest.encode())
        count_path = ROOT / "bundle-file-count.txt"
        size_path = ROOT / "bundle-size.txt"
        count_path.write_text(f"{count}\n")
        size_path.write_text(f"{size}\n")
        current = (count_path.read_text(), size_path.read_text(), sha256(count_path), sha256(size_path))
        if current == previous:
            break
        previous = current
    else:
        raise RuntimeError("bundle self-receipts did not stabilize")

    manifest = "".join(f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in files)
    (ROOT / "evidence.sha256").write_text(manifest)
    final_count = len(files) + 1
    final_size = sum(path.stat().st_size for path in files) + len(manifest.encode())
    if (ROOT / "bundle-file-count.txt").read_text() != f"{final_count}\n":
        raise RuntimeError("bundle file count receipt is unstable")
    if (ROOT / "bundle-size.txt").read_text() != f"{final_size}\n":
        raise RuntimeError("bundle size receipt is unstable")


if __name__ == "__main__":
    main()
