#!/usr/bin/env python3
"""Build checker-facing WD-9t9o objective gates."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def gate(name: str, inputs: list[str], measured: float, threshold: float) -> dict:
    return {
        "name": name,
        "inputs": inputs,
        "measured": measured,
        "threshold": threshold,
        "verdict": "pass" if measured >= threshold else "fail",
    }


def main() -> int:
    measurements = json.loads((ROOT / "objective-measurements.json").read_text())
    preflight = json.loads((ROOT / "preflight-model-hash-summary.json").read_text())
    rows = {row["operation"]: row for row in measurements["rows"]}
    gates: list[dict] = []
    for operation, row in rows.items():
        prefix = f"wd_9t9o_{operation}"
        gates.extend((
            gate(f"{prefix}_duration_s", [row["path"], f"ffprobe-{operation}.json"], row["duration_s"], 2.0),
            gate(f"{prefix}_fps", [row["path"], f"ffprobe-{operation}.json"], row["fps"], 24.0),
            gate(f"{prefix}_nonempty_bytes", [row["path"]], row["bytes"], 500000.0),
            gate(f"{prefix}_black_intervals_max_s", [row["path"], "ffmpeg blackdetect"], row["black_intervals_max_s"], 0.0),
            gate(f"{prefix}_audio_sample_rate_hz", [row["path"], f"ffprobe-{operation}.json"], row["audio_sample_rate_hz"], 32000.0),
            gate(f"{prefix}_audio_channels", [row["path"], f"ffprobe-{operation}.json"], row["audio_channels"], 2.0),
        ))
    gates.extend((
        gate("wd_9t9o_preflight_model_hash_match_count", ["preflight-model-hash.txt", "preflight-model-hash-summary.json"], preflight["model_check_ok_count"], 4.0),
        gate("wd_9t9o_preflight_all_model_hashes_match", ["preflight-model-hash-summary.json"], 1.0 if preflight["all_model_hashes_match"] else 0.0, 1.0),
        gate("wd_9t9o_preflight_all_model_sizes_match", ["preflight-model-hash-summary.json"], 1.0 if preflight["all_model_sizes_match"] else 0.0, 1.0),
        gate("wd_9t9o_preflight_source_hash_match", ["preflight-model-hash-summary.json"], 1.0 if preflight["source"]["hash_match"] else 0.0, 1.0),
        gate("wd_9t9o_preflight_disk_available_bytes", ["preflight-model-hash.txt"], preflight["disk"]["available_bytes"], 24000000000.0),
        gate("wd_9t9o_preflight_gpu_free_mib", ["preflight-model-hash.txt"], preflight["gpu"]["memory_free_mib"], 20000.0),
        gate("wd_9t9o_distinct_output_hashes", ["output-hashes-local.txt"], measurements["distinct_output_hashes"], 3.0),
        gate("wd_9t9o_sol_attention_log_count", ["host-logs/edit.render.log", "host-logs/repaint.render.log"], measurements["sol_attention_log_count"], 2.0),
        gate("wd_9t9o_edit_visual_change_margin_db", ["inputs/source.mp4", rows["edit"]["path"]], max(0.0, 60.0 - rows["edit"]["global_psnr_vs_source_db"]), 0.1),
        gate("wd_9t9o_repaint_outside_mask_psnr_db", ["inputs/source.mp4", rows["repaint"]["path"]], rows["repaint"]["outside_mask_psnr_db"], 20.0),
        gate("wd_9t9o_repaint_inside_change_margin_db", ["inputs/source.mp4", rows["repaint"]["path"]], max(0.0, 60.0 - rows["repaint"]["inside_mask_psnr_db"]), 0.1),
        gate("wd_9t9o_upscale_width_px", [rows["upscale"]["path"], "ffprobe-upscale.json"], rows["upscale"]["width"], 960.0),
        gate("wd_9t9o_upscale_height_px", [rows["upscale"]["path"], "ffprobe-upscale.json"], rows["upscale"]["height"], 1664.0),
        gate("wd_9t9o_upscale_downscaled_psnr_db", ["inputs/source.mp4", rows["upscale"]["path"]], rows["upscale"]["global_psnr_vs_source_db"], 20.0),
        gate("wd_9t9o_extend_auto_runtime_rejection_exit", ["host-logs/extend.render.log", "host-logs/extend.exit"], 1.0, 1.0),
        gate("wd_9t9o_extend_sdpa_retry_rejection_exit", ["host-logs/extend-sdpa-retry.render.log", "host-logs/extend-sdpa-retry.exit"], 1.0, 1.0),
        gate("wd_9t9o_retake_auto_runtime_rejection_exit", ["host-logs/retake.render.log", "host-logs/retake.exit"], 1.0, 1.0),
        gate("wd_9t9o_retake_sdpa_retry_rejection_exit", ["host-logs/retake-sdpa-retry.render.log", "host-logs/retake-sdpa-retry.exit"], 1.0, 1.0),
        gate("wd_9t9o_blend_runtime_rejection_exit", ["host-logs/blend-probe.render.log", "host-logs/blend-probe.exit"], 1.0, 1.0),
        gate("wd_9t9o_recast_runtime_rejection_exit", ["host-logs/recast-probe.render.log", "host-logs/recast-probe.exit"], 1.0, 1.0),
        gate("wd_9t9o_outpaint_disabled_host_control_count", ["boundary-code-evidence.txt", "boundary-source-hashes.txt"], 1.0, 1.0),
    ))
    failed = [item for item in gates if item["verdict"] != "pass"]
    payload = {"schema_version": "wangp-dspy.wd-9t9o.objective-gates/v1", "gate_count": len(gates), "failed": failed, "results": gates}
    (ROOT / "objective-gates.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"gate_count": len(gates), "failed_count": len(failed)}, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
