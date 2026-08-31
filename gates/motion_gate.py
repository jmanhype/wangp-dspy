"""Motion gate — 64x36 luma-diff per screen third, alive/frozen verdict.

Evidence base (verified 2026-08-30/31, controlled seed A/B on H3):
identical prompt+params, different seed produced frozen renders
(0.11-0.39 motion/third) vs alive renders (2.03-5.06). The 2.0
threshold separates the two clusters with margin on both sides.
Fix for frozen renders: motion gate + seed re-roll.

Metric: decode frames via ffmpeg subprocess, downscale to 64x36
grayscale, mean absolute luma diff between consecutive frames,
averaged per screen third (left / center / right columns of the
64-column grid: 21 / 22 / 21 columns).

ZERO-MODEL: ffmpeg subprocess + numpy only. No GPU, no LLM, no network.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

__all__ = [
    "MOTION_ALIVE_THRESHOLD",
    "MotionGateError",
    "motion_thirds",
    "motion_verdict",
]

MOTION_ALIVE_THRESHOLD = 2.0

_W = 64
_H = 36
# 64 columns -> 21 / 22 / 21
_SPLITS = (0, 21, 43, 64)
_THIRDS = ("left", "center", "right")


class MotionGateError(ValueError):
    """Raised when the video cannot be decoded (missing/corrupt file)."""


def _decode_gray(video_path: str) -> np.ndarray:
    """Decode video to (_H, _W) uint8 grayscale frames, shape (N, H, W)."""
    p = Path(video_path)
    if not p.exists():
        raise FileNotFoundError(f"video not found: {video_path}")
    proc = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-nostdin",
         "-i", str(p),
         "-vf", f"scale={_W}:{_H}", "-pix_fmt", "gray",
         "-f", "rawvideo", "-"],
        capture_output=True)
    if proc.returncode != 0 or not proc.stdout:
        raise MotionGateError(
            f"cannot decode video: {video_path} "
            f"(ffmpeg rc={proc.returncode}: {proc.stderr.decode(errors='replace').strip()})")
    frames = np.frombuffer(proc.stdout, dtype=np.uint8)
    if frames.size == 0 or frames.size % (_W * _H) != 0:
        raise MotionGateError(f"not a valid video frame stream: {video_path}")
    return frames.reshape(-1, _H, _W)


def motion_thirds(video_path: str) -> dict[str, float]:
    """Mean abs luma diff per consecutive frame pair, per screen third.

    Returns {"left": float, "center": float, "right": float} in 0-255
    luma units. Single-frame or static video -> all zeros.
    """
    frames = _decode_gray(video_path)
    if len(frames) < 2:
        return {name: 0.0 for name in _THIRDS}
    diffs = np.abs(frames[1:].astype(np.int16) - frames[:-1].astype(np.int16))
    out = {}
    for i, name in enumerate(_THIRDS):
        third = diffs[:, :, _SPLITS[i]:_SPLITS[i + 1]]
        out[name] = float(third.mean())
    return out


def motion_verdict(video_path: str) -> dict:
    """Full gate verdict: per-third metrics, min_third, alive flag.

    alive := min third >= MOTION_ALIVE_THRESHOLD (the weakest third
    must clear the bar — matches how the frozen/alive clusters were
    separated in the controlled seed A/B evidence).
    """
    thirds = motion_thirds(video_path)
    min_third = min(thirds.values())
    return {
        "thirds": thirds,
        "min_third": min_third,
        "alive": min_third >= MOTION_ALIVE_THRESHOLD,
    }
