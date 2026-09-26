#!/usr/bin/env python3
"""Compose real WD-dmf2 director outputs from authorized upstream media."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Sequence


VIDEO_FILTER = (
    "scale=480:832:force_original_aspect_ratio=increase,"
    "crop=480:832,fps=24,format=yuv420p"
)


def run(argv: Sequence[str], log) -> None:
    rendered = json.dumps(list(argv))
    print(rendered, file=log, flush=True)
    subprocess.run(list(argv), stdout=log, stderr=subprocess.STDOUT, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def simple_segment(
    source: Path, output: Path, duration: float, log, *, audio: Path | None = None
) -> None:
    argv = ["ffmpeg", "-y", "-v", "error", "-i", str(source)]
    if audio is not None:
        argv.extend(["-i", str(audio)])
        argv.extend(["-map", "0:v:0", "-map", "1:a:0"])
    else:
        argv.extend(["-map", "0:v:0", "-an"])
    argv.extend([
        "-t", f"{duration:.6f}",
        "-vf", VIDEO_FILTER,
        "-r", "24",
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
    ])
    if audio is not None:
        argv.extend([
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        ])
    argv.extend(["-movflags", "+faststart", str(output)])
    run(argv, log)


def concatenated_segment(
    first: Path,
    second: Path,
    audio: Path,
    audio_start: float,
    duration: float,
    pad: float,
    output: Path,
    log,
) -> None:
    filter_complex = (
        f"[0:v][1:v]concat=n=2:v=1:a=0[cat];"
        f"[cat]{VIDEO_FILTER},tpad=stop_mode=clone:"
        f"stop_duration={pad:.6f}[v]"
    )
    argv = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(first), "-i", str(second),
        "-ss", f"{audio_start:.6f}", "-t", f"{duration:.6f}", "-i", str(audio),
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "2:a:0",
        "-t", f"{duration:.6f}",
        "-r", "24",
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", str(output),
    ]
    run(argv, log)


def concatenate_final(first: Path, second: Path, output: Path, log) -> None:
    has_audio = "aac" in subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=codec_name", "-of", "csv=p=0", str(first)],
        check=True, text=True, capture_output=True,
    ).stdout
    if has_audio:
        filter_complex = (
            "[0:v][1:v]concat=n=2:v=1:a=0[v];"
            "[0:a][1:a]concat=n=2:v=0:a=1[a]"
        )
        maps = ["-map", "[v]", "-map", "[a]"]
        audio_args = [
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"
        ]
    else:
        filter_complex = "[0:v][1:v]concat=n=2:v=1:a=0[v]"
        maps = ["-map", "[v]", "-an"]
        audio_args = []
    argv = [
        "ffmpeg", "-y", "-v", "error", "-i", str(first), "-i", str(second),
        "-filter_complex", filter_complex, *maps,
        "-r", "24", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-pix_fmt", "yuv420p", *audio_args,
        "-movflags", "+faststart", str(output),
    ]
    run(argv, log)


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format",
         "-of", "json", str(path)],
        check=True, text=True, capture_output=True,
    )
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lane_root", type=Path)
    arguments = parser.parse_args()
    root = arguments.lane_root.resolve()
    inputs = root / "inputs"
    outputs = root / "outputs"
    for mode in ("prompt", "audio", "music_video", "screenplay"):
        (outputs / "clips" / mode).mkdir(parents=True, exist_ok=True)

    logs: dict[str, object] = {}
    hashes: dict[str, str] = {}
    probes: dict[str, dict] = {}
    for mode in ("prompt", "audio", "music_video", "screenplay"):
        log_path = root / f"wd-dmf2-{mode}.native.log"
        with log_path.open("w", encoding="utf-8") as log:
            if mode == "prompt":
                simple_segment(
                    inputs / "wd_cpow_vibevoice_revoice.mp4",
                    outputs / "clips/prompt/clip0001.mp4", 2.333333, log,
                )
                simple_segment(
                    inputs / "wd_cpow_deepfilternet_refine.mp4",
                    outputs / "clips/prompt/clip0002.mp4", 2.333333, log,
                )
            elif mode == "audio":
                music = inputs / "wd_rous_ace_generate.wav"
                concatenated_segment(
                    inputs / "wd_cpow_vibevoice_revoice.mp4",
                    inputs / "wd_cpow_deepfilternet_refine.mp4",
                    music, 0.0, 5.0, 0.333334,
                    outputs / "clips/audio/clip0001.mp4", log,
                )
                concatenated_segment(
                    inputs / "wd_cpow_deepfilternet_refine.mp4",
                    inputs / "wd_cpow_vibevoice_revoice.mp4",
                    music, 5.0, 5.0, 0.333334,
                    outputs / "clips/audio/clip0002.mp4", log,
                )
            elif mode == "music_video":
                music = inputs / "wd_rous_ace_generate.wav"
                concatenated_segment(
                    inputs / "wd_cpow_vibevoice_revoice.mp4",
                    inputs / "wd_cpow_deepfilternet_refine.mp4",
                    music, 0.0, 5.28, 0.613334,
                    outputs / "clips/music_video/clip0001.mp4", log,
                )
                concatenated_segment(
                    inputs / "wd_cpow_deepfilternet_refine.mp4",
                    inputs / "wd_cpow_vibevoice_revoice.mp4",
                    music, 5.28, 4.72, 0.053334,
                    outputs / "clips/music_video/clip0002.mp4", log,
                )
            else:
                simple_segment(
                    inputs / "wd_bxhc_character_video.mp4",
                    outputs / "clips/screenplay/clip0001.mp4", 3.5, log,
                    audio=inputs / "wd_bxhc_vibevoice_speech.wav",
                )
                simple_segment(
                    inputs / "wd_cpow_vibevoice_revoice.mp4",
                    outputs / "clips/screenplay/clip0002.mp4", 2.333333, log,
                    audio=inputs / "wd_cpow_vibevoice_raw.prepared.wav",
                )
            concatenate_final(
                outputs / f"clips/{mode}/clip0001.mp4",
                outputs / f"clips/{mode}/clip0002.mp4",
                outputs / f"wd_dmf2_{mode}_composition.mp4", log,
            )
        logs[mode] = log_path.name

    for path in sorted(outputs.rglob("*.mp4")):
        relative = path.relative_to(root).as_posix()
        hashes[relative] = sha256(path)
        probes[relative] = probe(path)
        probe_path = root / "ffprobe" / f"{path.stem}.json"
        probe_path.parent.mkdir(parents=True, exist_ok=True)
        probe_path.write_text(
            json.dumps(probes[relative], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    payload = {
        "schema_version": "wangp-dspy.director-host-composition/v1",
        "lane_root": str(root),
        "logs": logs,
        "output_sha256": hashes,
    }
    (root / "host-output-hashes.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
