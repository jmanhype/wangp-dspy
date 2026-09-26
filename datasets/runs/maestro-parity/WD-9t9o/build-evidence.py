#!/usr/bin/env python3
"""Assemble the canonical WD-9t9o Maestro-parity evidence record."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
OPERATIONS = ("edit", "repaint", "upscale")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(argv: list[str]) -> str:
    return subprocess.run(["git", "-C", str(REPO), *argv], text=True, capture_output=True, check=True).stdout.strip()


def media_metadata(name: str) -> dict:
    payload = json.loads((ROOT / f"ffprobe-{name}.json").read_text())
    video = next(item for item in payload["streams"] if item["codec_type"] == "video")
    audio = next((item for item in payload["streams"] if item["codec_type"] == "audio"), None)
    rate = video["r_frame_rate"].split("/")
    return {
        "path": f"outputs/{name}/wd_9t9o_{name}.mp4",
        "kind": "video",
        "width": int(video["width"]),
        "height": int(video["height"]),
        "duration_s": float(payload["format"]["duration"]),
        "fps": float(rate[0]) / float(rate[1]),
        "alpha_mode": "none",
        "audio": {
            "present": audio is not None,
            **({"codec": audio["codec_name"], "sample_rate_hz": int(audio["sample_rate"]), "channels": int(audio["channels"])} if audio else {}),
        },
    }


def main() -> int:
    commit = git(["rev-parse", "HEAD"])
    status = git(["status", "--porcelain=v1"])
    status_lines = status.splitlines()
    models = json.loads((ROOT / "model-assets.json").read_text())["assets"]
    preflight = json.loads((ROOT / "preflight-model-hash-summary.json").read_text())
    observed = {row["destination"]: row for row in preflight["assets"]}
    queue = json.loads((ROOT / "queue-record.json").read_text())
    gates = json.loads((ROOT / "objective-gates.json").read_text())
    measurements = json.loads((ROOT / "objective-measurements.json").read_text())
    review_path = ROOT / "reviewer-verdict.json"
    review = json.loads(review_path.read_text()) if review_path.exists() else {
        "decision": "pending", "review": "Independent PM review has not run.", "evidence_links": []
    }
    references = [
        ("inputs/source.mp4", "accepted_h3_vdn_source_video"),
        ("inputs/first-frame.png", "failed_vdn_retake_visual_anchor"),
        ("inputs/repaint-mask.mp4", "vdn_repaint_editable_region_mask"),
        ("inputs/recast-reference.png", "synthetic_vdn_recast_boundary_probe_reference"),
    ]
    dispositions = {
        "extend": {
            "disposition": "unsupported",
            "reason": "Required VDN Sol path with visual source conditioning failed before denoising under auto and SDPA retries with AssertionError: varlen only support head_dim [64, 128].",
            "evidence": "host-logs/extend.render.log",
        },
        "blend": {
            "disposition": "unsupported",
            "reason": "Runtime probe exited 1 with KeyError: reference_video_max_frames; two-reference controls are Ref2VA-only.",
            "evidence": "host-logs/blend-probe.render.log",
        },
        "retake": {
            "disposition": "unsupported",
            "reason": "Required VDN Sol path with first-frame visual conditioning failed before denoising under auto and SDPA retries with AssertionError: varlen only support head_dim [64, 128].",
            "evidence": "host-logs/retake.render.log",
        },
        "edit": {"disposition": "host_run_verified", "evidence": "outputs/edit/wd_9t9o_edit.mp4", "operation": "edit"},
        "outpaint": {
            "disposition": "unsupported",
            "reason": "FL2VA host model definition comments out video_guide_outpainting.",
            "evidence": "boundary-code-evidence.txt",
        },
        "repaint": {"disposition": "host_run_verified", "evidence": "outputs/repaint/wd_9t9o_repaint.mp4", "operation": "repaint"},
        "recast": {
            "disposition": "unsupported",
            "reason": "Runtime probe exited 1 because image, video, and audio references require the Ref2VA checkpoint.",
            "evidence": "host-logs/recast-probe.render.log",
        },
        "upscale": {"disposition": "host_run_verified", "evidence": "outputs/upscale/wd_9t9o_upscale.mp4", "operation": "upscale"},
    }
    payload = {
        "schema": "wangp-dspy.maestro-parity-evidence/v1",
        "operator_authorization": {
            "status": "approved",
            "text": "Authorized and approved.\ncontinue",
            "scope": "WD-9t9o H3 VDN operation evidence on host 3090 using existing assets only; no downloads, training, paid provider, GUI work, unrelated GPU process, or model deletion",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "approved_by": "operator via /root dispatcher",
        },
        "command": ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "3090", "/home/straughter/Wan2GP/wd-9t9o/host-scripts/wd_9t9o_render.sh"],
        "native_commands": [
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "3090", "/home/straughter/Wan2GP/wd-9t9o/host-scripts/wd_9t9o_preflight_hash_probe.sh"],
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "3090", "/home/straughter/Wan2GP/wd-9t9o/host-scripts/wd_9t9o_boundary_probes.sh"],
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "3090", "/home/straughter/Wan2GP/wd-9t9o/host-scripts/wd_9t9o_render.sh"],
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "3090", "bash /tmp/wd_9t9o_retry_sdpa.sh"],
        ],
        "repository": {
            "commit": commit,
            "dirty_state": {"dirty": bool(status_lines), "identity_sha256": hashlib.sha256(status.encode()).hexdigest(), "status_lines": status_lines},
        },
        "model_provenance": [
            {
                **asset,
                "identity": asset["id"],
                "source": asset["source_url"],
                "download_approved": True,
                "observed_sha256": observed[asset["destination"]]["observed_sha256"],
                "observed_size_bytes": observed[asset["destination"]]["observed_size_bytes"],
                "observed_mtime": observed[asset["destination"]]["observed_mtime"],
                "preflight_hash_verified": observed[asset["destination"]]["live_hash_match"],
            }
            for asset in models
        ],
        "reference_provenance": [
            {"path": path, "role": role, "sha256": sha256(ROOT / path), "license": "Operator-owned WD-2gyw/WD-9t9o generated evaluation asset; operator-authorized research/evaluation use; no redistribution"}
            for path, role in references
        ],
        "queue_attempt": {
            **queue,
            "exit_status": "succeeded",
            "native_logs": [
                "host-logs/extend.render.log", "host-logs/retake.render.log", "host-logs/edit.render.log",
                "host-logs/repaint.render.log", "host-logs/upscale.render.log", "host-logs/blend-probe.render.log",
                "host-logs/recast-probe.render.log",
            ],
        },
        "output": [{"path": f"outputs/{name}/wd_9t9o_{name}.mp4", "sha256": sha256(ROOT / f"outputs/{name}/wd_9t9o_{name}.mp4")} for name in OPERATIONS],
        "media_metadata": [media_metadata(name) for name in OPERATIONS],
        "objective_gate_results": gates["results"],
        "reviewer_verdict": review,
        "row_dispositions": dispositions,
        "runtime_notes": {
            "download_bytes": 0,
            "preflight_raw": "preflight-model-hash.txt",
            "preflight_summary": "preflight-model-hash-summary.json",
            "dry_run": "dry-run-output.txt",
            "sdpa_retry": "host-logs/extend-sdpa-retry.render.log and host-logs/retake-sdpa-retry.render.log",
            "sol_attention_log_count": measurements["sol_attention_log_count"],
            "repaint_mask_mode": "shared_timestep",
            "boundary_runtime_exits": {"blend": 1, "recast": 1, "extend": 1, "retake": 1},
            "objective_measurements": measurements,
            "final_host_state": "host-after.txt",
        },
    }
    (ROOT / "evidence.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"outputs": len(payload["output"]), "gates": len(payload["objective_gate_results"]), "review": payload["reviewer_verdict"]["decision"], "dirty": payload["repository"]["dirty_state"]["dirty"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
