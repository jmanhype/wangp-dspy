#!/usr/bin/env python3
"""Assemble the WD-2gyw evidence record from measured bundle artifacts."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


BUNDLE = Path(__file__).resolve().parent
ROOT = BUNDLE.parents[3]
STEMS = (
    "wd_2gyw_h3_standard",
    "wd_2gyw_h3_vdn_hybrid_attention",
    "wd_2gyw_h3_kfi_frames_injection",
    "wd_2gyw_h3_audio_refinement",
    "wd_2gyw_hunyuan",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fraction(value: str) -> float:
    if "/" not in value:
        return float(value)
    numerator, denominator = value.split("/", 1)
    return float(numerator) / float(denominator)


def git_output(argv: list[str]) -> str:
    return subprocess.run(
        argv, cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def main() -> int:
    commit = git_output(["git", "rev-parse", "HEAD"])
    status_lines = [
        line for line in git_output(["git", "status", "--porcelain=v1"]).splitlines()
        if line.startswith((" M ", "M  ", "?? "))
    ]
    dirty_identity = hashlib.sha256(
        "\n".join(status_lines).encode("utf-8")
    ).hexdigest()
    outputs = json.loads((BUNDLE / "output-hashes.json").read_text(encoding="utf-8"))
    media = []
    for stem in STEMS:
        probe = json.loads((BUNDLE / f"ffprobe-{stem}.json").read_text(encoding="utf-8"))
        video = next(item for item in probe["streams"] if item["codec_type"] == "video")
        audio = next(
            (item for item in probe["streams"] if item["codec_type"] == "audio"), None
        )
        entry = {
            "path": f"outputs/{stem}.mp4",
            "kind": "video",
            "width": int(video["width"]),
            "height": int(video["height"]),
            "duration_s": float(probe["format"]["duration"]),
            "fps": fraction(video["avg_frame_rate"]),
            "alpha_mode": "none",
            "audio": {"present": audio is not None},
            "measured_format": {
                "video_codec": video["codec_name"],
                "video_duration_s": float(video["duration"]),
                "container_duration_s": float(probe["format"]["duration"]),
                "fps": fraction(video["avg_frame_rate"]),
                "width": int(video["width"]),
                "height": int(video["height"]),
            },
        }
        if audio is not None:
            entry["audio"].update({
                "codec": audio["codec_name"],
                "sample_rate_hz": int(audio["sample_rate"]),
                "channels": int(audio["channels"]),
            })
            entry["measured_format"].update({
                "audio_codec": audio["codec_name"],
                "audio_duration_s": float(audio["duration"]),
                "sample_rate_hz": int(audio["sample_rate"]),
                "channels": int(audio["channels"]),
            })
        media.append(entry)
    references = []
    for relative, role in (
        ("inputs/wd_2gyw_h3_standard_first_frame.png", "kfi_injected_source_frame"),
        ("outputs/wd_2gyw_h3_standard.mp4", "kfi_and_audio_refinement_source_video"),
    ):
        path = BUNDLE / relative
        references.append({
            "path": relative,
            "role": role,
            "sha256": sha256(path),
            "license": "Operator-owned WD-2gyw generated evaluation asset; operator-authorized research/evaluation use; no redistribution",
        })
    record = {
        "schema": "wangp-dspy.maestro-parity-evidence/v1",
        "operator_authorization": {
            "status": "approved",
            "text": "I agree\nyou need to kill whatever that is that was holding up the GPU and get back to work so that we can finish and complete this\nUnblock and cont\nYes",
            "scope": "WD-2gyw feasible video subset on host 3090: H3 assets already present, LTX-2.5 int8 and Hunyuan-1.5 int8 downloads bounded to 57,801,926,853 bytes under the dispatcher-approved 60,000,000,000-byte lane ceiling; synchronous renders; no llama-server restart or unrelated GPU work",
            "timestamp": "2026-09-25T14:15:32Z",
            "approved_by": "operator via /root parent authorization",
        },
        "command": [
            "timeout", "4200", "ssh", "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=15", "3090", "timeout", "4000",
            "/home/straughter/Wan2GP/wd_2gyw_hunyuan.sh",
        ],
        "native_commands": [
            [
                "timeout", "3900", "ssh", "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=15", "3090", "timeout", "3700",
                "/home/straughter/Wan2GP/wd_2gyw_h3_standard.sh",
            ],
            [
                "timeout", "4200", "ssh", "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=15", "3090", "timeout", "4000",
                "/home/straughter/Wan2GP/wd_2gyw_h3_specialized.sh",
            ],
            [
                "timeout", "2400", "ssh", "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=15", "3090", "timeout", "2200",
                "/home/straughter/Wan2GP/wd_2gyw_h3_kfi_retry.sh",
            ],
            [
                "timeout", "4200", "ssh", "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=15", "3090", "timeout", "4000",
                "/home/straughter/Wan2GP/wd_2gyw_ltx25.sh",
            ],
            [
                "timeout", "4200", "ssh", "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=15", "3090", "timeout", "4000",
                "/home/straughter/Wan2GP/wd_2gyw_hunyuan.sh",
            ],
        ],
        "repository": {
            "commit": commit,
            "commit_semantics": "efaafa7 is the clean generation base after bounded download, post-download preflight, and queue admission; generated outputs and evidence are intentionally dirty state in this record",
            "dirty_state": {
                "dirty": bool(status_lines),
                "identity_sha256": dirty_identity,
                "status_lines": status_lines,
            },
        },
        "model_provenance": json.loads(
            (BUNDLE / "selected-model-provenance.json").read_text(encoding="utf-8")
        ),
        "reference_provenance": references,
        "queue_attempt": {
            **json.loads((BUNDLE / "queue-record.json").read_text(encoding="utf-8")),
            "exit_status": "succeeded",
            "native_logs": [
                "h3-standard.render.log",
                "h3-specialized.render.log",
                "h3-kfi-retry.render.log",
                "hunyuan.render.log",
                "ltx25.failure.log",
            ],
        },
        "output": outputs,
        "media_metadata": media,
        "objective_gate_results": json.loads(
            (BUNDLE / "objective-gates.json").read_text(encoding="utf-8")
        ),
        "reviewer_verdict": {
            "decision": "pending",
            "evidence_links": [
                "execution-summary.md",
                "operator-authorization.md",
                "download-plan.json",
                "download-report.json",
                "host-before-download.txt",
                "host-after-download.txt",
                "doctor-preflight-before-download.json",
                "doctor-preflight-after-download.json",
                "queue-record.json",
                "queue-complete.log",
                "output-hashes.txt",
                "media-qc.json",
                "objective-gates.json",
                "row-dispositions.json",
                "matrix-transition-check.json",
                "checker-result.txt",
                "final-host-state.txt",
                "bundle-size.txt",
                "ltx25.failure.log",
                "taomate-search-evidence.md",
                "h3-outpaint-boundary.md",
                "planning/cli-summary.json",
            ],
            "review": "Human reviewer approval is pending; no self-approval is claimed.",
        },
        "row_dispositions": json.loads(
            (BUNDLE / "row-dispositions.json").read_text(encoding="utf-8")
        )["rows"],
        "runtime_notes": {
            "gpu": "NVIDIA GeForce RTX 3090, 24576 MiB total",
            "gpu_before_h3_standard": "83 MiB used / 24034 MiB free",
            "gpu_after_each_completed_render": "83 MiB used / 24034 MiB free",
            "planned_download_bytes": 57801926853,
            "actual_network_download_bytes": 57801926853,
            "download_ceiling_bytes": 60000000000,
            "download_verified_assets": 26,
            "download_before_free_bytes": 106745708544,
            "download_after_free_bytes": 48921567232,
            "derived_preflight_min_free_gb_before_download": 77.832239334,
            "derived_preflight_min_free_gb_after_download": 24.0,
            "disk_floor_derivation": "Before download: 53.832239334 GiB selected downloads + 4 GiB render/output working set + 20 GiB safety margin = 77.832239334 GiB. After download: 4 GiB render/output working set + 20 GiB safety margin = 24 GiB.",
            "ltx25_failure": "Authorized synchronous attempt exited before generation with TypeError: tokenizers.pre_tokenizers.Split object does not support item assignment",
            "final_free_bytes": 44842311680,
            "background_state": "No WD-2gyw SSH/render process or GPU compute app remains; CPU-only audio critic stopped; llama-server was not restarted; Maestro continues its pre-existing CPU-only WanGP server respawn loop",
        },
    }
    (BUNDLE / "evidence.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "commit": commit,
        "dirty": bool(status_lines),
        "models": len(record["model_provenance"]),
        "references": len(record["reference_provenance"]),
        "outputs": len(record["output"]),
        "gates": len(record["objective_gate_results"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
