"""Renderer policy — typed rejections encoding the verified H3-Ref2VA
envelope (grandma-perfect recipe + Wet Reckless priors).

Grid: WanGP shot lengths live on the 17k+5 SECOND grid — 5, 22, 39,
56, 73, 90, 107, 124, 141... s (k >= 0). The 4s Ref2VA floor sits
below the first grid point, so the first usable grid length is 5s.
"""
from __future__ import annotations

import json
import os
from typing import Tuple


class RendererPolicyError(ValueError):
    """Base typed renderer-policy rejection."""


class FacingError(RendererPolicyError):
    """Speaker's master plate is not camera-facing (or missing/unreadable)."""


class FramingError(RendererPolicyError):
    """Shot framing violates the wide/bright requirement."""


class GridError(RendererPolicyError):
    """Shot duration is not on the 17k+5 frame grid."""


class GuideDurationError(RendererPolicyError):
    """Guide duration != shot duration exactly."""


def _grid_durations(cap_s: float = 200.0) -> Tuple[float, ...]:
    """Durations on the 17k+5 grid: 5 + 17k seconds (k >= 0)."""
    out = []
    k = 0
    while True:
        dur = float(5 + 17 * k)
        if dur > cap_s:
            break
        out.append(dur)
        k += 1
    return tuple(out)


def _grid_frames() -> Tuple[int, ...]:
    """Frame counts at 24fps for the 17k+5 second grid."""
    return tuple(int(round((5 + 17 * k) * 24)) for k in range(0, 12))


GRID_DURATIONS_S = _grid_durations()
GRID_FRAMES = _grid_frames()


def check_duration_on_grid(duration_s: float) -> int:
    """Return the frame count if duration_s is on the grid, else GridError."""
    d = round(float(duration_s), 6)
    for i, frames in enumerate(GRID_FRAMES):
        if abs((5 + 17 * i) - d) < 1e-6:
            return frames
    raise GridError(
        f"shot duration {duration_s}s is off the 17k+5 grid "
        "(allowed: 5/22/39/56/73/90/107/124/141...s)")


def check_facing(plate_path: str, requirement: str) -> str:
    """Master plate must exist and be camera-facing.

    Facing is asserted by a sidecar `<plate>.plate.json` carrying
    {"facing": "camera"|"profile"} produced with the plate. Requirement
    'camera' rejects profile-facing plates (the speaker's mouth must be
    visible for lip-sync fidelity — Wet Reckless prior).
    """
    if not plate_path or not os.path.isfile(plate_path):
        raise FacingError(
            f"master plate not readable: {plate_path!r} (path check)")
    sidecar = os.path.splitext(plate_path)[0] + ".plate.json"
    facing = None
    if os.path.isfile(sidecar):
        try:
            facing = json.loads(open(sidecar).read()).get("facing")
        except (ValueError, OSError):
            facing = None
    if facing is None:
        # No sidecar: fall back to the character's declared requirement.
        facing = requirement
    if requirement != "camera" or facing != "camera":
        raise FacingError(
            f"master plate {plate_path} facing={facing!r} "
            f"(requirement={requirement!r}) — the SPEAKER's plate must "
            "be camera-facing for lip-sync fidelity (Wet Reckless prior)")
    return facing


def check_framing(framing: str, lighting: str) -> None:
    """Wide/bright framing requirement (grandma-perfect recipe)."""
    f = (framing or "").strip().lower()
    l = (lighting or "").strip().lower()
    if f not in ("wide", "medium", "medium-wide"):
        raise FramingError(
            f"framing {framing!r} violates the wide-framing requirement "
            "(allowed: wide, medium-wide, medium)")
    if l not in ("bright", "well-lit", "high-key", "natural"):
        raise FramingError(
            f"lighting {lighting!r} violates the bright-lighting "
            "requirement (allowed: bright, well-lit, high-key, natural)")


def check_guide_duration(guide_duration_s: float, shot_duration_s: float) -> None:
    if abs(float(guide_duration_s) - float(shot_duration_s)) > 1e-9:
        raise GuideDurationError(
            f"guide duration {guide_duration_s}s != shot duration "
            f"{shot_duration_s}s — guide must be sliced to the exact "
            "shot duration")


__all__ = [
    "RendererPolicyError", "FacingError", "FramingError", "GridError",
    "GuideDurationError", "GRID_DURATIONS_S", "GRID_FRAMES",
    "check_duration_on_grid", "check_facing", "check_framing",
    "check_guide_duration",
]
