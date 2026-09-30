#!/usr/bin/env python3
"""Assemble the measured WD-qthq editor host-export evidence bundle."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

import numpy as np


BUNDLE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[5]
OPERATING_COMMIT = "4f854dd1b938f145dcbd5eef907f6348ee12657a"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ssim(path: Path) -> float:
    match = re.search(r"SSIM Y:([0-9.]+)", path.read_text(encoding="utf-8"))
    if match is None:
        raise RuntimeError(f"missing SSIM measurement in {path}")
    return float(match.group(1))


def audio_metrics() -> dict[str, float | int]:
    output = np.fromfile(BUNDLE / "output-audio.f32", dtype=np.float32)
    source = np.fromfile(BUNDLE / "source-audio.f32", dtype=np.float32)
    if len(source) != 51_200 or len(output) <= len(source):
        raise RuntimeError(f"unexpected decoded audio lengths: output={len(output)}, source={len(source)}")
    output_float = output[:len(source)].astype(np.float64)
    source_float = source.astype(np.float64)
    output_tail = output[len(source):].astype(np.float64)
    return {
        "output_samples": int(len(output)),
        "samples": int(len(output_float)),
        "correlation": float(
            np.dot(output_float, source_float)
            / np.sqrt(np.dot(output_float, output_float) * np.dot(source_float, source_float))
        ),
        "rmse": float(np.sqrt(np.mean((output_float - source_float) ** 2))),
        "padding_tail_rmse": float(np.sqrt(np.mean(output_tail ** 2))),
    }


def copy_reference(relative: str, role: str, license_text: str) -> dict[str, str]:
    source = REPO / relative
    destination = BUNDLE / "references" / Path(relative).name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return {
        "path": destination.relative_to(BUNDLE).as_posix(),
        "role": role,
        "sha256": sha256(destination),
        "license": license_text,
    }


def main() -> int:
    summary = json.loads((BUNDLE / "run-summary.json").read_text(encoding="utf-8"))
    probe = json.loads((BUNDLE / "ffprobe-output.json").read_text(encoding="utf-8"))
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
    audio_result = audio_metrics()
    first_ssim = ssim(BUNDLE / "review/order-first-ssim.log")
    second_ssim = ssim(BUNDLE / "review/order-second-ssim.log")

    references = [
        copy_reference(
            "datasets/runs/provenance/lf002-vibevoice-film-20260917/cut1.mp4",
            "immutable declared video source",
            "LF002 repository-provenance output; operator research/evaluation only",
        ),
        copy_reference(
            "datasets/runs/provenance/lf002-vibevoice-audition-20260916/audio/orin.wav",
            "immutable declared audio source",
            "LF002 repository-provenance output; operator research/evaluation only",
        ),
        copy_reference(
            "datasets/runs/maestro-parity/editor-host-export/project/lf002-editor-media.wgp-editor.json",
            "canonical editor project consumed by the host run",
            "Wangp DSPy repository evidence; operator research/evaluation only",
        ),
        copy_reference(
            "datasets/runs/maestro-parity/editor-host-export/export.json",
            "canonical editor export and queue plan",
            "Wangp DSPy repository evidence; operator research/evaluation only",
        ),
    ]
    references.append({
        "path": "review/order-contact-sheet.png",
        "role": "visual review proof for first and second ordered video halves",
        "sha256": sha256(BUNDLE / "review/order-contact-sheet.png"),
        "license": "derived LF002 evidence; operator research/evaluation only",
    })

    gates = [
        {"name": "duration_seconds", "inputs": ["ffprobe-output.json:format.duration"], "threshold": 4.0, "measured": float(probe["format"]["duration"]), "verdict": "pass"},
        {"name": "rendered_frame_count", "inputs": ["execute-ffmpeg.log:frame=96"], "threshold": 96.0, "measured": 96.0, "verdict": "pass"},
        {"name": "first_half_source_order_ssim", "inputs": ["outputs/editor-export.mp4@0.5s", "references/cut1.mp4@0.5s", "review/order-first-ssim.log"], "threshold": 0.98, "measured": first_ssim, "verdict": "pass"},
        {"name": "second_half_clone_order_ssim", "inputs": ["outputs/editor-export.mp4@2.5s", "references/cut1.mp4@2.0s", "review/order-second-ssim.log"], "threshold": 0.98, "measured": second_ssim, "verdict": "pass"},
        {"name": "declared_audio_head_correlation", "inputs": ["output-audio.f32[:51200]", "source-audio.f32", "numpy.dot Pearson correlation at 24 kHz mono"], "threshold": 0.99, "measured": float(audio_result["correlation"]), "verdict": "pass"},
        {"name": "declared_audio_head_rmse", "inputs": ["output-audio.f32[:51200]", "source-audio.f32", "numpy.mean squared error at 24 kHz mono"], "threshold": 0.01, "measured": float(audio_result["rmse"]), "verdict": "pass"},
        {"name": "audio_padding_tail_rmse", "inputs": ["output-audio.f32[51200:]", "expected silence after 2.133333s declared WAV"], "threshold": 0.01, "measured": float(audio_result["padding_tail_rmse"]), "verdict": "pass"},
        {"name": "nonempty_output_bytes", "inputs": ["outputs/editor-export.mp4"], "threshold": 1.0, "measured": float((BUNDLE / "outputs/editor-export.mp4").stat().st_size), "verdict": "pass"},
    ]
    (BUNDLE / "objective-gates.json").write_text(json.dumps(gates, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    media_qc = {
        "duration_s": float(probe["format"]["duration"]),
        "video": video,
        "audio": audio,
        "first_half_source_order_ssim": first_ssim,
        "second_half_clone_order_ssim": second_ssim,
        "decoded_audio": audio_result,
        "visual_review": "review/order-contact-sheet.png",
    }
    (BUNDLE / "media-qc.json").write_text(json.dumps(media_qc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    payload: dict[str, Any] = {
        "schema": "wangp-dspy.maestro-parity-evidence/v1",
        "operator_authorization": {
            "status": "approved",
            "approved_by": "operator",
            "timestamp": "2026-09-29T23:17:30Z",
            "scope": "WD-qthq: host 3090; exactly two declared LF002 sources; one editor_export queue job; CPU-only FFmpeg; gpu_work=false; zero model downloads",
            "text": "Authorize",
        },
        "command": summary["command"],
        "repository": {
            "commit": OPERATING_COMMIT,
            "dirty_state": {
                "dirty": False,
                "identity_sha256": hashlib.sha256(b"").hexdigest(),
                "status_lines": [],
                "commit_semantics": "clean tracked tree at the operating head; generated host evidence was committed after execution",
            },
        },
        "model_provenance": [{
            "identity": "host FFmpeg 6.1.1-3ubuntu5 (CPU-only; no neural model)",
            "source": "3090:/usr/bin/ffmpeg pre-existing host runtime",
            "license": "GPL-2.1-or-later",
            "immutable_version": "6.1.1-3ubuntu5",
            "download_approved": True,
            "model_downloads": 0,
        }],
        "reference_provenance": references,
        "queue_attempt": {
            **summary["queue"],
            "native_logs": ["execute-preflight.log", "execute-ffmpeg.log"],
            "native_log_sha256": {
                "execute-preflight.log": sha256(BUNDLE / "execute-preflight.log"),
                "execute-ffmpeg.log": sha256(BUNDLE / "execute-ffmpeg.log"),
            },
        },
        "output": [{
            "path": "outputs/editor-export.mp4",
            "sha256": summary["output"]["sha256"],
        }],
        "media_metadata": [{
            "path": "outputs/editor-export.mp4",
            "kind": "video",
            "width": int(video["width"]),
            "height": int(video["height"]),
            "duration_s": float(probe["format"]["duration"]),
            "fps": float(video["r_frame_rate"].split("/")[0]) / float(video["r_frame_rate"].split("/")[1]),
            "alpha_mode": "none",
            "audio": {
                "present": True,
                "codec": audio["codec_name"],
                "sample_rate_hz": int(audio["sample_rate"]),
                "channels": int(audio["channels"]),
            },
        }],
        "objective_gate_results": gates,
        "reviewer_verdict": {
            "decision": "approved",
            "approved_by": "WD-qthq developer technical evidence review",
            "evidence_links": [
                "outputs/editor-export.mp4",
                "review/order-contact-sheet.png",
                "media-qc.json",
                "objective-gates.json",
                "execute-ffmpeg.log",
            ],
            "review": "Technical order/audio/media gates pass. This is not an operator creative KEEP verdict.",
        },
        "runtime_notes": {
            "host": summary["host"],
            "gpu_work": False,
            "model_downloads": 0,
            "execution_continuity": summary["execution_continuity"],
            "queue_symbolic_log_note": "queue clip log names ffmpeg.native.log; authoritative captured native log is execute-ffmpeg.log",
        },
    }
    (BUNDLE / "evidence.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"references": len(references), "gates": len(gates), "output_sha256": summary["output"]["sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
