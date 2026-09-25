#!/usr/bin/env python3
"""Measure local bundle bytes and objective before/after finishing gates."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


BUNDLE = Path(__file__).resolve().parent
SOURCE = BUNDLE / "inputs/source.mp4"
OUTPUTS = sorted((BUNDLE / "outputs").glob("*.mp4"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_probe(name: str) -> dict[str, Any]:
    stem = "source" if name == "source.mp4" else Path(name).stem
    return json.loads((BUNDLE / f"ffprobe-{stem}.json").read_text(encoding="utf-8"))


def video(probe: dict[str, Any]) -> dict[str, Any]:
    return next(stream for stream in probe["streams"] if stream["codec_type"] == "video")


def audio(probe: dict[str, Any]) -> dict[str, Any] | None:
    return next((stream for stream in probe["streams"] if stream["codec_type"] == "audio"), None)


def rate(value: str) -> float:
    numerator, separator, denominator = value.partition("/")
    return float(numerator) if not separator else float(numerator) / float(denominator)


def psnr(left: Path, right: Path, *, downscale_right: bool = False) -> float:
    graph = (
        "[1:v]scale=480:832:flags=bicubic[scaled];[0:v][scaled]psnr"
        if downscale_right
        else "[0:v][1:v]psnr"
    )
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostdin", "-i", str(left), "-i", str(right),
         "-filter_complex", graph, "-f", "null", "-"],
        text=True, capture_output=True, timeout=180, check=False,
    )
    match = re.search(r"average:(inf|[0-9.]+)", result.stderr)
    if result.returncode != 0 or match is None:
        raise RuntimeError(f"PSNR probe failed for {right}: {result.stderr[-1000:]}")
    return float("100.0" if match.group(1) == "inf" else match.group(1))


def ssim(left: Path, right: Path, *, downscale_right: bool = False) -> float:
    graph = (
        "[1:v]scale=480:832:flags=bicubic[scaled];[0:v][scaled]ssim"
        if downscale_right
        else "[0:v][1:v]ssim"
    )
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostdin", "-i", str(left), "-i", str(right),
         "-filter_complex", graph, "-f", "null", "-"],
        text=True, capture_output=True, timeout=180, check=False,
    )
    match = re.search(r"All:([0-9.]+)", result.stderr)
    if result.returncode != 0 or match is None:
        raise RuntimeError(f"SSIM probe failed for {right}: {result.stderr[-1000:]}")
    return float(match.group(1))


def gate(name: str, inputs: list[str], threshold: float, measured: float) -> dict[str, Any]:
    return {
        "name": name,
        "inputs": inputs,
        "threshold": threshold,
        "measured": round(measured, 6),
        "verdict": "pass" if measured >= threshold else "fail",
    }


def main() -> int:
    source_probe = load_probe("source.mp4")
    source_video = video(source_probe)
    source_audio = audio(source_probe)
    source_frames = int(source_video["nb_frames"])
    source_fps = rate(source_video["avg_frame_rate"])
    source_duration = float(source_probe["format"]["duration"])

    media: dict[str, Any] = {"source": {
        "path": "inputs/source.mp4",
        "sha256": sha256(SOURCE),
        "video": source_video,
        "audio": source_audio,
        "duration_s": source_duration,
    }}
    gates: list[dict[str, Any]] = []
    comparisons: dict[str, Any] = {}
    for output in OUTPUTS:
        probe = load_probe(output.name)
        stream = video(probe)
        sound = audio(probe)
        media[output.name] = {
            "path": f"outputs/{output.name}",
            "sha256": sha256(output),
            "video": stream,
            "audio": sound,
            "duration_s": float(probe["format"]["duration"]),
        }
        output_frames = int(stream.get("nb_frames", 0))
        output_fps = rate(stream["avg_frame_rate"])
        output_duration = float(probe["format"]["duration"])
        name = output.stem
        if "interpolation" in name:
            gates.append(gate(f"{name}.fps_factor", [f"outputs/{output.name}"], 1.99, output_fps / source_fps))
            gates.append(gate(f"{name}.frame_factor", [f"outputs/{output.name}"], 1.9, output_frames / source_frames))
            gates.append(gate(f"{name}.duration_abs_error_s", [f"outputs/{output.name}"], 0.0, 0.13 - abs(output_duration - source_duration)))
        elif "spatial" in name:
            gates.append(gate(f"{name}.width_factor", [f"outputs/{output.name}"], 2.0, stream["width"] / source_video["width"]))
            gates.append(gate(f"{name}.height_factor", [f"outputs/{output.name}"], 2.0, stream["height"] / source_video["height"]))
            if "real_esrgan" in name:
                measured = psnr(SOURCE, output, downscale_right=True)
                measured_ssim = ssim(SOURCE, output, downscale_right=True)
                comparisons[name] = {
                    "downscaled_psnr_db": measured,
                    "downscaled_ssim": measured_ssim,
                }
                gates.append(gate(f"{name}.downscaled_ssim", [f"outputs/{output.name}"], 0.6, measured_ssim))
        elif "film_grain" in name:
            measured = psnr(SOURCE, output)
            comparisons[name] = {"source_psnr_db": measured}
            gates.append(gate(f"{name}.source_psnr_db", [f"outputs/{output.name}"], 20.0, measured))
        if sound is not None and source_audio is not None:
            audio_match = (
                sound.get("codec_name") == source_audio.get("codec_name")
                and int(sound.get("sample_rate", 0)) == int(source_audio.get("sample_rate", 0))
                and int(sound.get("channels", 0)) == int(source_audio.get("channels", 0))
            )
            gates.append(gate(f"{name}.audio_layout_match", [f"outputs/{output.name}"], 1.0, float(audio_match)))
        gates.append(gate(f"{name}.duration_positive", [f"outputs/{output.name}"], 0.001, output_duration))

    codec_control = BUNDLE / "outputs/wd_r81u_ffmpeg_codec_h264.mp4"
    codec_psnr = psnr(SOURCE, codec_control)
    comparisons["codec_control"] = {"source_psnr_db": codec_psnr}
    for grain_name in ("wd_r81u_ffmpeg_film_grain", "wd_r81u_film_film_grain"):
        grain_psnr = comparisons[grain_name]["source_psnr_db"]
        gates.append(gate(f"{grain_name}.visual_delta_below_codec_control_db", [f"outputs/{grain_name}.mp4"], 3.0, codec_psnr - grain_psnr))

    failed = [item["name"] for item in gates if item["verdict"] != "pass"]
    payload = {
        "schema": "wangp-dspy.finishing-measurements/v1",
        "source_sha256": media["source"]["sha256"],
        "media": media,
        "comparisons": comparisons,
        "objective_gates": gates,
        "failed_gates": failed,
    }
    (BUNDLE / "media-qc.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (BUNDLE / "objective-gates.json").write_text(json.dumps(gates, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (BUNDLE / "output-hashes-local.txt").write_text(
        "".join(f"{media[item.name]['sha256']}  outputs/{item.name}\n" for item in OUTPUTS), encoding="utf-8"
    )
    files = [path for path in BUNDLE.rglob("*") if path.is_file() and ".venv" not in path.parts]
    (BUNDLE / "bundle-size.txt").write_text(
        f"file_count={len(files)}\naggregate_bytes={sum(path.stat().st_size for path in files)}\n", encoding="utf-8"
    )
    print(json.dumps({"outputs": len(OUTPUTS), "gates": len(gates), "failed": failed}, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
