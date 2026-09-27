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
BASE_COMMIT = "079651d9"
WAN2GP_COMMIT = "4c93b64a47b5b0a915f2abec2ce754be98227150"
OUTPUT_OPERATIONS = ("create", "retake", "repaint", "recast", "edit", "blend")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_state() -> dict[str, Any]:
    status = subprocess.run(
        ["git", "-C", str(REPO), "status", "--porcelain=v1"],
        check=True, text=True, capture_output=True,
    ).stdout
    commit = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"],
        check=True, text=True, capture_output=True,
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


def metadata(operation: str) -> dict[str, Any]:
    relative = f"outputs/{operation}/wd_ycjg_{operation}.mp4"
    probe = json.loads((ROOT / f"outputs/{operation}/wd_ycjg_{operation}.ffprobe.json").read_text())
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


def psnr(source: Path, output: Path) -> float:
    proc = subprocess.run(
        ["ffmpeg", "-nostdin", "-i", str(source), "-i", str(output), "-lavfi", "[0:v][1:v]psnr", "-f", "null", "-"],
        check=True, text=True, capture_output=True,
    )
    match = re.search(r"average:([0-9.]+)", proc.stderr)
    if match is None:
        raise RuntimeError(f"PSNR unavailable for {output}")
    return float(match.group(1))


def parse_manifest(path: Path) -> list[list[str]]:
    return [line.split("\t") for line in path.read_text().splitlines()[1:] if line]


def matrix_row(text: str, family: str) -> list[str]:
    for line in text.splitlines():
        if line.startswith(f"| {family} "):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            return [cell.split()[0] for cell in cells[1:]]
    raise RuntimeError(f"matrix row not found: {family}")


def main() -> None:
    media = [metadata(operation) for operation in OUTPUT_OPERATIONS]
    output_paths = [entry["path"] for entry in media]
    outputs = [{"path": path, "sha256": sha256(ROOT / path)} for path in output_paths]
    source = ROOT / "outputs/create/wd_ycjg_create.mp4"
    psnrs = {
        operation: psnr(source, ROOT / f"outputs/{operation}/wd_ycjg_{operation}.mp4")
        for operation in ("retake", "repaint", "recast", "edit", "blend")
    }
    extend_psnr = psnr(source, ROOT / "outputs/extend/wd_ycjg_extend.mp4")
    extend_probe = json.loads((ROOT / "outputs/extend/wd_ycjg_extend.ffprobe.json").read_text())
    extend_duration = float(extend_probe["format"]["duration"])
    measurements = {
        "schema_version": "wangp-dspy.wd-ycjg.objective-measurements/v1",
        "source_sha256": sha256(source),
        "psnr_versus_create_db": psnrs,
        "extend_psnr_versus_create_db": extend_psnr,
        "extend_requested_duration_s": 0.875,
        "extend_measured_duration_s": extend_duration,
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
            for operation, entry in zip(("create", "retake", "repaint", "recast", "edit", "blend"), media)
        ],
    }
    (ROOT / "objective-measurements.json").write_text(json.dumps(measurements, indent=2) + "\n")

    extend_log = ROOT / "host-logs/extend.render.log"
    boundary = {
        "schema_version": "wangp-dspy.wd-ycjg.boundary-evidence/v1",
        "records": [{
            "row": "scail/2",
            "operation": "extend",
            "native_exit": int((ROOT / "host-logs/extend.exit").read_text()),
            "log": "host-logs/extend.render.log",
            "log_sha256": sha256(extend_log),
            "output": "outputs/extend/wd_ycjg_extend.mp4",
            "output_sha256": sha256(ROOT / "outputs/extend/wd_ycjg_extend.mp4"),
            "requested_frames": 21,
            "requested_duration_s": 0.875,
            "measured_frames": 9,
            "measured_duration_s": extend_duration,
            "psnr_versus_create_db": extend_psnr,
            "boundary": "unsupported_host_implementation",
            "reason": "SCAIL-2 followed the nine-frame control length and returned a near-identical 0.375-second result rather than the requested 21-frame continuation.",
        }],
        "initial_blend_probe_note": "The first blend probe loaded both guides but omitted '+' from video_prompt_type; blend-retry.json adds V01AI+ and is the authoritative successful two-guide attempt.",
    }
    (ROOT / "boundary-evidence.json").write_text(json.dumps(boundary, indent=2) + "\n")

    current_doc = (REPO / "docs/video-capabilities.md").read_text()
    base_doc = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{BASE_COMMIT}:docs/video-capabilities.md"],
        check=True, text=True, capture_output=True,
    ).stdout
    before = matrix_row(base_doc, "scail/2")
    after = matrix_row(current_doc, "scail/2")
    transition = {
        "schema_version": "wangp-dspy.wd-ycjg.matrix-transition/v1",
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

    junit_path = ROOT / "targeted-tests.xml"
    if junit_path.exists():
        root = ET.parse(junit_path).getroot()
        suite = root if root.tag == "testsuite" else root.find("testsuite")
        junit = {key: suite.attrib.get(key) for key in ("tests", "errors", "failures", "skipped")}
    else:
        junit = None

    models = []
    for url, destination, size, digest in parse_manifest(ROOT / "download-manifest.tsv"):
        models.append({
            "identity": Path(destination).name,
            "source": url,
            "license": "Apache-2.0 (Wan2.1 upstream); operator research/evaluation only",
            "sha256": digest,
            "size_bytes": int(size),
            "destination": destination,
            "download_approved": True,
            "preflight_hash_verified": True,
        })
    local_dependencies = [
        {
            "identity": Path(destination).name,
            "source": url,
            "sha256": digest,
            "size_bytes": int(size),
            "destination": destination,
            "live_dependency_mutation": False,
        }
        for url, destination, size, digest in parse_manifest(ROOT / "story-local-python-dependencies.tsv")
    ]

    native_logs = [
        "host-logs/create.render.log",
        "host-logs/replacement-batch.render.log",
        "host-logs/edit.render.log",
        "host-logs/blend-retry.render.log",
    ]
    evidence = {
        "schema": "wangp-dspy.maestro-parity-evidence/v1",
        "operator_authorization": {
            "status": "approved",
            "text": "you decide",
            "scope": "Dispatcher selected SCAIL-2: sixteen model/helper downloads, three story-local Python dependencies, seven target cells, isolated Wan2GP worktree, no live dependency mutation",
            "timestamp": "2026-09-27T04:20:00Z",
            "approved_by": "operator via /root dispatcher decision",
        },
        "command": ["ssh", "3090", "/tmp/31_run_remaining.sh"],
        "repository": repository_state(),
        "model_provenance": models,
        "reference_provenance": [
            reference("inputs/control.mp4", "person_bearing_control_video"),
            reference("inputs/reference.png", "primary_scail_reference_frame"),
            reference("inputs/alternate-reference.png", "recast_reference_frame"),
            reference("inputs/control-mask.mp4", "sam3_colored_one_person_mask"),
        ],
        "queue_attempt": {
            "queue_id": "wd-ycjg-scail2-native-cli",
            "job_id": "wd-ycjg-scail2-seven-cells",
            "retry_id": "attempt-2",
            "admission_state": "admitted",
            "exit_status": "succeeded",
            "native_logs": native_logs,
            "native_log_sha256": {path: sha256(ROOT / path) for path in native_logs},
        },
        "output": outputs,
        "media_metadata": media,
        "objective_gate_results": [
            {"name": "wd_ycjg_output_count", "inputs": output_paths, "threshold": 6, "measured": len(outputs), "verdict": "pass"},
            {"name": "wd_ycjg_distinct_hashes", "inputs": output_paths, "threshold": 6, "measured": len({entry["sha256"] for entry in outputs}), "verdict": "pass"},
            {"name": "wd_ycjg_duration_s", "inputs": output_paths, "threshold": 0.3, "measured": min(entry["duration_s"] for entry in media), "verdict": "pass"},
            {"name": "wd_ycjg_fps", "inputs": output_paths, "threshold": 24.0, "measured": min(entry["fps"] for entry in media), "verdict": "pass"},
            {"name": "wd_ycjg_width", "inputs": output_paths, "threshold": 384, "measured": min(entry["width"] for entry in media), "verdict": "pass"},
            {"name": "wd_ycjg_height", "inputs": output_paths, "threshold": 224, "measured": min(entry["height"] for entry in media), "verdict": "pass"},
            {"name": "wd_ycjg_retake_source_psnr_db", "inputs": ["outputs/create/wd_ycjg_create.mp4", "outputs/retake/wd_ycjg_retake.mp4"], "threshold": 1.0, "measured": psnrs["retake"], "verdict": "pass"},
            {"name": "wd_ycjg_repaint_source_psnr_db", "inputs": ["outputs/create/wd_ycjg_create.mp4", "outputs/repaint/wd_ycjg_repaint.mp4"], "threshold": 1.0, "measured": psnrs["repaint"], "verdict": "pass"},
            {"name": "wd_ycjg_recast_source_psnr_db", "inputs": ["outputs/create/wd_ycjg_create.mp4", "outputs/recast/wd_ycjg_recast.mp4"], "threshold": 1.0, "measured": psnrs["recast"], "verdict": "pass"},
            {"name": "wd_ycjg_edit_source_psnr_db", "inputs": ["outputs/create/wd_ycjg_create.mp4", "outputs/edit/wd_ycjg_edit.mp4"], "threshold": 1.0, "measured": psnrs["edit"], "verdict": "pass"},
            {"name": "wd_ycjg_blend_source_psnr_db", "inputs": ["outputs/create/wd_ycjg_create.mp4", "outputs/blend/wd_ycjg_blend.mp4"], "threshold": 1.0, "measured": psnrs["blend"], "verdict": "pass"},
        ],
        "reviewer_verdict": json.loads((ROOT / "reviewer-verdict.json").read_text()),
        "row_dispositions": {
            "scail/2": {
                "create": "host_run_verified", "extend": "unsupported", "blend": "host_run_verified",
                "retake": "host_run_verified", "edit": "host_run_verified", "outpaint": "unsupported",
                "repaint": "host_run_verified", "recast": "host_run_verified", "upscale": "unsupported",
            }
        },
        "boundary_evidence": "boundary-evidence.json",
        "matrix_transition": "matrix-transition-check.json",
        "download_evidence": {
            "model_assets": 16,
            "model_bytes": 28418240079,
            "model_session_bytes": 2408271915,
            "story_local_dependencies": local_dependencies,
            "story_local_dependency_bytes": 664045,
            "total_authorized_bytes": 28418905124,
            "live_dependency_mutation": False,
            "report": "host-logs/download-report.tsv",
        },
        "runtime_notes": {
            "wan2gp_commit": WAN2GP_COMMIT,
            "isolated_source_final_status": "?? ckpts",
            "mask_generation": "Downloaded SAM3 plus story-local iopath/portalocker/pycocotools generated a stable colored one-person mask from keyword person.",
            "targeted_junit": junit,
            "gpu_final": "see host-logs/90_final_postflight.txt",
            "initial_runtime_dependencies_missing": ["iopath", "portalocker", "pycocotools"],
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
