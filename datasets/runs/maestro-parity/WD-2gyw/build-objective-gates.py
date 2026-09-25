#!/usr/bin/env python3
"""Measure objective media gates from the emitted WD-2gyw MP4s."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


BUNDLE = Path(__file__).resolve().parent
ROWS = {
    "wd_2gyw_h3_standard": "minimax_h3/standard",
    "wd_2gyw_h3_vdn_hybrid_attention": "minimax_h3/h3_vdn_hybrid_attention",
    "wd_2gyw_h3_kfi_frames_injection": "minimax_h3/kfi_frames_injection",
    "wd_2gyw_h3_audio_refinement": "minimax_h3/h3_audio_refinement",
    "wd_2gyw_hunyuan": "hunyuan/standard",
}


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, check=False, capture_output=True, text=True)


def fraction(value: str) -> float:
    if "/" not in value:
        return float(value)
    numerator, denominator = value.split("/", 1)
    return float(numerator) / float(denominator)


def gate(row: str, name: str, inputs: list[str], threshold: float,
         measured: float) -> dict:
    return {
        "name": name,
        "row": row,
        "inputs": inputs,
        "threshold": threshold,
        "measured": measured,
        "verdict": "pass" if measured >= threshold else "fail",
    }


def main() -> int:
    gates: list[dict] = []
    media: list[dict] = []
    for stem, row in ROWS.items():
        relative = f"outputs/{stem}.mp4"
        path = BUNDLE / relative
        probe_path = BUNDLE / f"ffprobe-{stem}.json"
        probe = json.loads(probe_path.read_text(encoding="utf-8"))
        video = next(item for item in probe["streams"] if item["codec_type"] == "video")
        audio = next(
            (item for item in probe["streams"] if item["codec_type"] == "audio"), None
        )
        duration = float(probe["format"]["duration"])
        fps = fraction(video["avg_frame_rate"])
        width, height = int(video["width"]), int(video["height"])
        size = path.stat().st_size
        black = run([
            "ffmpeg", "-v", "info", "-i", str(path), "-an",
            "-vf", "blackdetect=d=0.05:pix_th=0.03", "-f", "null", "-",
        ])
        black_intervals = len(re.findall(r"\[blackdetect @", black.stderr))
        audio_rms_db = None
        if audio is not None:
            volume = run([
                "ffmpeg", "-i", str(path), "-map", "0:a:0", "-vn",
                "-af", "volumedetect", "-f", "null", "-",
            ])
            match = re.search(r"mean_volume:\s*(-?[0-9.]+)\s*dB", volume.stderr)
            if match is None:
                raise RuntimeError(f"no mean_volume for {relative}: {volume.stderr[-500:]}")
            audio_rms_db = float(match.group(1))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        media.append({
            "path": relative,
            "row": row,
            "sha256": digest,
            "size_bytes": size,
            "width": width,
            "height": height,
            "duration_s": duration,
            "fps": fps,
            "black_intervals_detected": black_intervals,
            "audio_rms_db": audio_rms_db,
        })
        gates.extend((
            gate(row, f"{stem}_duration_s", [relative, probe_path.name], 2.0, duration),
            gate(row, f"{stem}_fps", [relative, probe_path.name], 24.0, fps),
            gate(row, f"{stem}_nonempty_bytes", [relative], 500000.0, float(size)),
            gate(row, f"{stem}_black_intervals_max", [relative, "ffmpeg blackdetect"], 0.0, float(black_intervals)),
        ))
        if audio is not None:
            assert audio_rms_db is not None
            gates.append(gate(
                row, f"{stem}_audio_sample_rate_hz", [relative, probe_path.name],
                32000.0, float(audio["sample_rate"]),
            ))
            gates.append(gate(
                row, f"{stem}_audio_channels", [relative, probe_path.name],
                2.0, float(audio["channels"]),
            ))
    payload = {
        "schema_version": "wangp-dspy.maestro-parity-objective-gates/v1",
        "media": media,
        "objective_gate_results": gates,
    }
    (BUNDLE / "media-qc.json").write_text(
        json.dumps(media, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (BUNDLE / "objective-gates.json").write_text(
        json.dumps(gates, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (BUNDLE / "media-and-objective-gates.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    failed = [item for item in gates if item["verdict"] != "pass"]
    print(json.dumps({
        "gate_count": len(gates),
        "failed": failed,
        "media_count": len(media),
    }, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
