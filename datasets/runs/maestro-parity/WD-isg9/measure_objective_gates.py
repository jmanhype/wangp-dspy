#!/usr/bin/env python3
"""Measure local media gates for the WD-isg9 operation bundle."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, text=True, capture_output=True, check=False)


def ffprobe(path: Path) -> dict:
    result = run([
        "ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)
    ])
    if result.returncode:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


def video_audio(payload: dict) -> tuple[dict, dict]:
    streams = payload.get("streams", [])
    video = next(item for item in streams if item.get("codec_type") == "video")
    audio = next((item for item in streams if item.get("codec_type") == "audio"), {})
    return video, audio


def psnr(reference: Path, output: Path, *, filter_expr: str = "null") -> float:
    lavfi = f"[0:v]{filter_expr}[a];[1:v]{filter_expr}[b];[a][b]psnr"
    result = run([
        "ffmpeg", "-nostdin", "-i", str(reference), "-i", str(output),
        "-lavfi", lavfi, "-f", "null", "-",
    ])
    matches = re.findall(r"average:(inf|[0-9.]+)", result.stderr)
    if not matches:
        raise RuntimeError(f"no PSNR for {reference.name}/{output.name}: {result.stderr[-1000:]}")
    return 999.0 if matches[-1] == "inf" else float(matches[-1])


def black_intervals(path: Path) -> float:
    result = run([
        "ffmpeg", "-nostdin", "-i", str(path),
        "-vf", "blackdetect=d=0.05:pix_th=0.05", "-an", "-f", "null", "-",
    ])
    spans = []
    for start, end in re.findall(r"black_start:([0-9.]+).*?black_end:([0-9.]+)", result.stderr):
        spans.append(max(0.0, float(end) - float(start)))
    return max(spans, default=0.0)


def main() -> int:
    source = ROOT / "inputs/source.mp4"
    outputs = {
        name: ROOT / f"outputs/{name}/wd_isg9_{name}.mp4"
        for name in ("extend", "retake", "edit", "repaint", "upscale")
    }
    rows = []
    for name, path in outputs.items():
        payload = ffprobe(path)
        video, audio = video_audio(payload)
        row = {
            "operation": name,
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": subprocess.run(
                ["shasum", "-a", "256", str(path)], text=True, capture_output=True, check=True
            ).stdout.split()[0],
            "duration_s": float(payload["format"]["duration"]),
            "fps": float(video["r_frame_rate"].split("/")[0]) / float(video["r_frame_rate"].split("/")[1]),
            "width": int(video["width"]),
            "height": int(video["height"]),
            "audio_present": bool(audio),
            "audio_sample_rate_hz": int(audio.get("sample_rate", 0)),
            "audio_channels": int(audio.get("channels", 0)),
            "black_intervals_max_s": black_intervals(path),
            "global_psnr_vs_source_db": psnr(
                source, path,
                filter_expr="scale=480:832" if name == "upscale" else "null",
            ),
        }
        if name in {"extend", "retake"}:
            row["first_frame_psnr_db"] = psnr(source, path, filter_expr="trim=end_frame=1")
        if name == "extend":
            row["source_prefix_psnr_db"] = psnr(source, path, filter_expr="trim=end_frame=56")
        if name == "repaint":
            row["outside_mask_psnr_db"] = psnr(source, path, filter_expr="crop=480:240:0:20")
            row["inside_mask_psnr_db"] = psnr(source, path, filter_expr="crop=240:320:120:250")
        rows.append(row)
    payload = {
        "schema_version": "wangp-dspy.wd-isg9.objective-measurements/v1",
        "source_sha256": subprocess.run(
            ["shasum", "-a", "256", str(source)], text=True, capture_output=True, check=True
        ).stdout.split()[0],
        "distinct_output_hashes": len({row["sha256"] for row in rows}),
        "rows": rows,
    }
    target = ROOT / "objective-measurements.json"
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
