"""RED tests — gates/motion_gate.py (64x36 luma-diff per screen third).

Evidence base: seed-responsive freeze finding (verified 2026-08-30/31
controlled A/B — identical prompt+params, different seed produced
frozen 0.11-0.39 motion/third vs alive 2.03-5.06). Threshold >=2.0
separates the two clusters with margin on both sides.

ZERO-MODEL: ffmpeg subprocess + numpy only. No GPU, no LLM, no network.
Synthetic videos generated via ffmpeg lavfi sources in a tmp_path fixture.
"""
from __future__ import annotations

import subprocess

import pytest

from gates.motion_gate import (
    MOTION_ALIVE_THRESHOLD,
    motion_thirds,
    motion_verdict,
)


def _encode_frames(tmp_path, name, frames_np, fps=10):
    """Encode (N,H,W) uint8 frames to mp4 via ffmpeg stdin. Deterministic,
    no lavfi expression quoting hazards."""
    out = tmp_path / name
    n, h, w = frames_np.shape
    proc = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "rawvideo", "-pix_fmt", "gray",
         "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
         "-pix_fmt", "yuv420p", str(out)],
        input=frames_np.tobytes(), check=True)
    return str(out)


def _static(n=30, h=108, w=192):
    import numpy as np
    return np.full((n, h, w), 128, dtype=np.uint8)


def _left_box(n=40, h=108, w=192):
    # white 40x40 box bouncing horizontally within the LEFT third
    import numpy as np
    frames = np.zeros((n, h, w), dtype=np.uint8)
    for i in range(n):
        x = abs((i * 8) % 32 - 16) + 4    # spans 4..60, inside left third
        frames[i, 34:74, x:x + 40] = 255
    return frames


def _checker(n=30, h=108, w=192):
    # alternating checkerboard: every pixel flips every frame
    import numpy as np
    yy, xx = np.mgrid[0:h, 0:w]
    base = ((yy // 8 + xx // 8) % 2) * 255
    return np.stack([base if i % 2 == 0 else 255 - base
                     for i in range(n)]).astype(np.uint8)


@pytest.fixture(scope="module")
def static_video(tmp_path_factory):
    return _encode_frames(tmp_path_factory.mktemp("static"),
                          "static.mp4", _static())


@pytest.fixture(scope="module")
def left_motion_video(tmp_path_factory):
    return _encode_frames(tmp_path_factory.mktemp("leftmotion"),
                          "left.mp4", _left_box())


@pytest.fixture(scope="module")
def full_motion_video(tmp_path_factory):
    return _encode_frames(tmp_path_factory.mktemp("fullmotion"),
                          "full.mp4", _checker())


# ── metric shape ──────────────────────────────────────────────────────

def test_motion_thirds_returns_three_thirds(static_video):
    m = motion_thirds(static_video)
    assert set(m) == {"left", "center", "right"}


def test_static_video_all_thirds_near_zero(static_video):
    m = motion_thirds(static_video)
    assert all(v < 0.5 for v in m.values()), m


# ── frozen vs alive verdicts ──────────────────────────────────────────

def test_static_video_frozen_verdict(static_video):
    v = motion_verdict(static_video)
    assert v["alive"] is False
    assert v["min_third"] < MOTION_ALIVE_THRESHOLD


def test_left_only_motion_localizes(left_motion_video):
    m = motion_thirds(left_motion_video)
    assert m["left"] > m["center"], m
    assert m["left"] > m["right"], m
    assert m["center"] < 1.0 and m["right"] < 1.0, m


def test_left_only_motion_alive(left_motion_video):
    v = motion_verdict(left_motion_video)
    assert v["thirds"]["left"] >= MOTION_ALIVE_THRESHOLD


def test_full_motion_alive(full_motion_video):
    v = motion_verdict(full_motion_video)
    assert v["alive"] is True, v
    assert v["min_third"] >= MOTION_ALIVE_THRESHOLD, v


# ── threshold behavior ────────────────────────────────────────────────

def test_threshold_constant_value():
    assert MOTION_ALIVE_THRESHOLD == 2.0


def test_verdict_shape(full_motion_video):
    v = motion_verdict(full_motion_video)
    assert set(v["thirds"]) == {"left", "center", "right"}
    assert isinstance(v["alive"], bool)
    assert v["min_third"] == min(v["thirds"].values())


# ── error handling ────────────────────────────────────────────────────

def test_missing_file_raises_clean_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        motion_thirds(str(tmp_path / "does-not-exist.mp4"))


def test_invalid_file_raises_clean_error(tmp_path):
    bad = tmp_path / "bad.mp4"
    bad.write_bytes(b"this is not a video")
    with pytest.raises(ValueError):
        motion_thirds(str(bad))
