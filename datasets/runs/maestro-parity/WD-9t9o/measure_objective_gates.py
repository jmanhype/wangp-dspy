#!/usr/bin/env python3
"""Measure local media gates for WD-9t9o."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OPERATIONS = ("edit", "repaint", "upscale")


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, text=True, capture_output=True, check=False)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ffprobe(path: Path) -> dict:
    result = run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)])
    if result.returncode:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


def psnr(reference: Path, output: Path, filter_expr: str = "null") -> float:
    lavfi = f"[0:v]{filter_expr}[a];[1:v]{filter_expr}[b];[a][b]psnr"
    result = run(["ffmpeg", "-nostdin", "-i", str(reference), "-i", str(output), "-lavfi", lavfi, "-f", "null", "-"])
    values = re.findall(r"average:(inf|[0-9.]+)", result.stderr)
    if not values:
        raise RuntimeError(result.stderr[-1000:])
    return 999.0 if values[-1] == "inf" else float(values[-1])


def black_intervals(path: Path) -> float:
    result = run(["ffmpeg", "-nostdin", "-i", str(path), "-vf", "blackdetect=d=0.05:pix_th=0.05", "-an", "-f", "null", "-"])
    spans = []
    for start, end in re.findall(r"black_start:([0-9.]+).*?black_end:([0-9.]+)", result.stderr):
        spans.append(max(0.0, float(end) - float(start)))
    return max(spans, default=0.0)


def main() -> int:
    source = ROOT / "inputs/source.mp4"
    rows = []
    for name in OPERATIONS:
        path = ROOT / f"outputs/{name}/wd_9t9o_{name}.mp4"
        payload = ffprobe(path)
        video = next(item for item in payload["streams"] if item["codec_type"] == "video")
        audio = next((item for item in payload["streams"] if item["codec_type"] == "audio"), {})
        rate = video["r_frame_rate"].split("/")
        row = {
            "operation": name,
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "duration_s": float(payload["format"]["duration"]),
            "fps": float(rate[0]) / float(rate[1]),
            "width": int(video["width"]),
            "height": int(video["height"]),
            "audio_present": bool(audio),
            "audio_sample_rate_hz": int(audio.get("sample_rate", 0)),
            "audio_channels": int(audio.get("channels", 0)),
            "black_intervals_max_s": black_intervals(path),
            "global_psnr_vs_source_db": psnr(source, path, "scale=480:832" if name == "upscale" else "null"),
        }
        if name == "repaint":
            row["outside_mask_psnr_db"] = psnr(source, path, "crop=480:240:0:20")
            row["inside_mask_psnr_db"] = psnr(source, path, "crop=240:320:120:250")
        rows.append(row)
    payload = {
        "schema_version": "wangp-dspy.wd-9t9o.objective-measurements/v1",
        "source_sha256": sha256(source),
        "distinct_output_hashes": len({row["sha256"] for row in rows}),
        "sol_attention_log_count": sum(
            "Sol-Attn enabled" in (ROOT / f"host-logs/{name}.render.log").read_text(errors="replace")
            for name in ("edit", "repaint")
        ),
        "rows": rows,
    }
    (ROOT / "objective-measurements.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
