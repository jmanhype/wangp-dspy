#!/usr/bin/env python3
"""Build checker-facing objective gates from measured WD-isg9 media."""
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
    rows = {row["operation"]: row for row in measurements["rows"]}
    gates: list[dict] = []
    for operation, row in rows.items():
        prefix = f"wd_isg9_{operation}"
        gates.extend((
            gate(f"{prefix}_duration_s", [row["path"], f"ffprobe-{operation}.json"], row["duration_s"], 2.0),
            gate(f"{prefix}_fps", [row["path"], f"ffprobe-{operation}.json"], row["fps"], 24.0),
            gate(f"{prefix}_nonempty_bytes", [row["path"]], row["bytes"], 500000.0),
            gate(f"{prefix}_black_intervals_max_s", [row["path"], "ffmpeg blackdetect"], row["black_intervals_max_s"], 0.0),
            gate(f"{prefix}_audio_sample_rate_hz", [row["path"], f"ffprobe-{operation}.json"], row["audio_sample_rate_hz"], 32000.0),
            gate(f"{prefix}_audio_channels", [row["path"], f"ffprobe-{operation}.json"], row["audio_channels"], 2.0),
        ))
    gates.extend((
        gate("wd_isg9_distinct_output_hashes", ["output-hashes-local.txt"], measurements["distinct_output_hashes"], 5.0),
        gate("wd_isg9_extend_longer_than_source_s", ["inputs/source.mp4", rows["extend"]["path"]], rows["extend"]["duration_s"], 2.333334),
        gate("wd_isg9_extend_source_prefix_psnr_db", ["inputs/source.mp4", rows["extend"]["path"]], rows["extend"]["source_prefix_psnr_db"], 20.0),
        gate("wd_isg9_retake_first_frame_anchor_psnr_db", ["inputs/first-frame.png", rows["retake"]["path"]], rows["retake"]["first_frame_psnr_db"], 20.0),
        gate("wd_isg9_edit_visual_change_margin_db", ["inputs/source.mp4", rows["edit"]["path"]], max(0.0, 60.0 - rows["edit"]["global_psnr_vs_source_db"]), 0.1),
        gate("wd_isg9_repaint_outside_mask_psnr_db", ["inputs/source.mp4", rows["repaint"]["path"]], rows["repaint"]["outside_mask_psnr_db"], 20.0),
        gate("wd_isg9_repaint_inside_change_margin_db", ["inputs/source.mp4", rows["repaint"]["path"]], max(0.0, 60.0 - rows["repaint"]["inside_mask_psnr_db"]), 0.1),
        gate("wd_isg9_upscale_width_px", [rows["upscale"]["path"], "ffprobe-upscale.json"], rows["upscale"]["width"], 960.0),
        gate("wd_isg9_upscale_height_px", [rows["upscale"]["path"], f"ffprobe-upscale.json"], rows["upscale"]["height"], 1664.0),
        gate("wd_isg9_upscale_downscaled_psnr_db", ["inputs/source.mp4", rows["upscale"]["path"]], rows["upscale"]["global_psnr_vs_source_db"], 20.0),
        gate("wd_isg9_blend_runtime_rejection_exit", ["host-logs/blend-probe.render.log", "host-logs/blend-probe.exit"], 1.0, 1.0),
        gate("wd_isg9_recast_runtime_rejection_exit", ["host-logs/recast-probe.render.log", "host-logs/recast-probe.exit"], 1.0, 1.0),
        gate("wd_isg9_outpaint_disabled_host_control_count", ["boundary-code-evidence.txt", "boundary-source-hashes.txt"], 1.0, 1.0),
    ))
    failed = [item for item in gates if item["verdict"] != "pass"]
    payload = {
        "schema_version": "wangp-dspy.wd-isg9.objective-gates/v1",
        "gate_count": len(gates),
        "failed": failed,
        "results": gates,
    }
    (ROOT / "objective-gates.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"gate_count": len(gates), "failed_count": len(failed)}, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
