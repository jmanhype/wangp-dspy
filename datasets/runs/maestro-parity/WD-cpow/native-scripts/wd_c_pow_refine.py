#!/usr/bin/env python3
"""Run the bounded WD-cpow DeepFilterNet denoise-and-loudness operation."""
from __future__ import annotations

import json
import sys
import types

import numpy as np
import soundfile as sf
import torch


metadata_module = types.ModuleType("torchaudio.backend.common")


class AudioMetaData:
    """Compatibility anchor for DeepFilterNet's torchaudio type import."""

    __slots__ = ()


metadata_module.AudioMetaData = AudioMetaData
sys.modules.setdefault("torchaudio.backend.common", metadata_module)

from df.enhance import enhance, init_df

import shutil
import subprocess
from pathlib import Path


ROOT = Path("/home/straughter/Wan2GP/outputs/wd-cpow/refine")
ASSETS = Path("/home/straughter/Wan2GP/wd-cpow-assets")
MODEL = ASSETS / "DeepFilterNet3"
INPUT = Path("/home/straughter/wangp-dspy-vibevoice-20260916/datasets/runs/maestro-parity/WD-cpow/outputs/wd_cpow_vibevoice_revoice.mp4")
OUTPUT = INPUT.with_name("wd_cpow_deepfilternet_refine.mp4")
WORK = ROOT / "work"


def run(argv: list[str]) -> None:
    subprocess.run(argv, check=True, timeout=300)


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    noisy = WORK / "revoice-audio.wav"
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(INPUT), "-map", "0:a:0",
        "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", str(noisy),
    ])
    audio, sample_rate = sf.read(noisy, dtype="float32", always_2d=True)
    tensor = torch.from_numpy(audio.T)
    model, deep_filter_state, _ = init_df(
        str(MODEL), post_filter=False, log_level="ERROR", log_file=None,
        config_allow_defaults=True, epoch="best", mask_only=False,
    )
    refined = enhance(
        model, deep_filter_state, tensor, pad=True, atten_lim_db=6.0
    )
    denoised = WORK / "revoice-audio_DeepFilterNet3.wav"
    sf.write(
        denoised, refined.numpy().T, sample_rate, subtype="PCM_16",
    )
    denoised = WORK / "revoice-audio_DeepFilterNet3.wav"
    if not denoised.exists():
        candidates = sorted(WORK.glob("*DeepFilterNet3*.wav"))
        if len(candidates) != 1:
            raise RuntimeError(f"expected one DeepFilterNet output, found {candidates}")
        denoised = candidates[0]
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(INPUT), "-i", str(denoised),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
        "-b:a", "128k", "-ar", "48000", "-ac", "2", "-af",
        "loudnorm=I=-18:TP=-1.5:LRA=11", "-shortest", "-movflags", "+faststart",
        str(OUTPUT),
    ])
    ffprobe = INPUT.with_name("ffprobe-wd_cpow_deepfilternet_refine.remote.json")
    subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(OUTPUT)],
        check=True, timeout=60, stdout=ffprobe.open("w"),
    )
    stream_hash = INPUT.with_name("video-stream-hash.refine.txt")
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-i", str(OUTPUT), "-map", "0:v:0",
         "-c", "copy", "-f", "streamhash", "-hash", "sha256", str(stream_hash)],
        check=True, timeout=60,
    )
    report = {
        "input": str(INPUT),
        "output": str(OUTPUT),
        "denoised": str(denoised),
        "model": str(MODEL),
        "noise_reduction_db": 6.0,
        "target_lufs": -18.0,
    }
    (ROOT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    shutil.copyfile(OUTPUT, ROOT / OUTPUT.name)
    shutil.copyfile(ffprobe, ROOT / ffprobe.name)
    shutil.copyfile(stream_hash, ROOT / stream_hash.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
