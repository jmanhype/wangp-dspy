"""WD-a1d9/S3 — pure remux policy PLANNER (command GENERATION only).

Deferred-from-S2 execution slice, minus execution: given an
AudioPolicy + AudioGuideProvenance, emit the ffmpeg argv LIST that
discards the render's audio (G4: rendered audio is NEVER trusted) and
remuxes the keeper window from the policy source. Paths never reach a
shell — argv list form only — and the keeper output must live inside
the keeper root (containment, GLM note N1). No ffmpeg is run here.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Tuple

from predict.audio_dataplane import AudioGuideProvenance, AudioPolicy

__all__ = ["RemuxPlannerError", "RemuxPlan", "plan_remux"]


class RemuxPlannerError(ValueError):
    """Typed planner failure (policy violation or containment)."""


@dataclass(frozen=True)
class RemuxPlan:
    # argv is a LIST (never a shell string) — paths never reach a shell
    argv: list
    policy: AudioPolicy
    remux_source_path: str
    rendered_path: str
    keeper_output: str


def plan_remux(policy: AudioPolicy, *, provenance: AudioGuideProvenance,
               rendered_path: str, keeper_output: str,
               keeper_root: Optional[str] = None) -> RemuxPlan:
    # G4: rendered audio is NEVER trusted — a plan that would keep it
    # is a typed rejection, not a silent honor.
    if not policy.discard_rendered_audio:
        raise RemuxPlannerError(
            "discard_rendered_audio=False is rejected by the remux "
            "planner — G4: rendered audio is never trusted")
    src = getattr(provenance, policy.remux_source)
    start, end = float(policy.remux_window[0]), float(policy.remux_window[1])
    # containment: keeper output must resolve inside the keeper root
    out_abs = os.path.realpath(keeper_output)
    if keeper_root is not None:
        root_abs = os.path.realpath(keeper_root)
        if not (out_abs == root_abs or out_abs.startswith(
                root_abs + os.sep)):
            raise RemuxPlannerError(
                f"containment: keeper output {keeper_output!r} resolves "
                f"outside the keeper root {keeper_root!r}")
    # input 0 = the RENDER (video only is kept), input 1 = the policy
    # remux source windowed to the keeper range — same input order as
    # the existing s4 remux_tts convention.
    argv = [
        "ffmpeg", "-y",
        "-i", str(rendered_path),
        "-ss", f"{start:.6f}", "-to", f"{end:.6f}", "-i", str(src),
        "-map", "0:v:0",       # render VIDEO only (discard rendered audio)
        "-map", "1:a:0",       # policy source audio
        "-c:v", "copy", "-c:a", "aac",
        "-shortest",
        str(keeper_output),
    ]
    return RemuxPlan(
        argv=argv, policy=policy, remux_source_path=str(src),
        rendered_path=str(rendered_path), keeper_output=str(keeper_output))
