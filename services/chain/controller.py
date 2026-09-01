"""Chain controller — build Chain Plans and render-order manifests.

Pure config/plan layer: no GPU, no rendering, no ffmpeg. The technique
(last frame of shot N = first frame of shot N+1 via H3's trained
continuation task; reference plates stand down after shot 1) is ported
from joeygambino/MiniMax-H3-Multishot-Workflow; the Chain Plan JSON
shape follows RwGrid/ComfyUI-MiniMaxH3-Contex-Loop's
H3_CHAIN_FORMAT_GUIDE.

Shot 1 renders from our proven 3-image-ref recipe (two-shot anchor +
character plates, 20 steps, spectrum cache, 480x832, apad). When
renderers/h3_recipe.py (feat/h3-production-recipe) merges, that builder
should be replaced by a reference to it — until then this inline
builder is minimal and recipe-shaped.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Sequence

from services.chain.plan import (
    ChainCharacter,
    ChainClip,
    ChainPlan,
    ClipAudio,
    SchemaError,
    validate_chain_plan,
)
from services.director.renderers.policy import check_duration_on_grid

OVERLAP_FRAMES = 22  # upstream H3_CHAIN_FORMAT_GUIDE default; see docs
_FPS = 24
_RECIPE_STEPS = 20


class ChainPlanError(ValueError):
    """Typed chain-controller rejection (bad inputs, off-grid, etc.)."""


def _sn(characters: Sequence[dict]) -> Dict[str, str]:
    try:
        return {c["name"]: c["sn_tag"] for c in characters}
    except (KeyError, TypeError) as e:
        raise ChainPlanError(
            f"characters entries need name/sn_tag/description: {e}") from e


def _global_prompt(characters: Sequence[dict]) -> str:
    pins = ", ".join(
        f"{c['sn_tag']} ({c['name']}) is {c['description']}"
        for c in characters)
    return ("Throughout every scene identity and wardrobe stay locked: "
            f"{pins}.")


def _speaker_template(speaker_sn: str, text: str) -> str:
    """Programmatic (SN) speaker template style: SN-pinned speaker line."""
    return f"{speaker_sn} speaks: {text}"


def _seed_for(script_line: Dict[str, str], index: int) -> int:
    basis = f"{index}|{script_line.get('speaker', '')}|{script_line.get('text', '')}"
    return int.from_bytes(hashlib.sha256(basis.encode()).digest()[:4], "big")


def build_chain_plan(
    script_lines: Sequence[Dict[str, str]],
    characters: Sequence[dict],
    durations_s: Sequence[float],
    audio_paths: Optional[Sequence[str]] = None,
    overlap_frames: int = OVERLAP_FRAMES,
) -> ChainPlan:
    """Build a validated ChainPlan from script beats + roster + durations."""
    if len(script_lines) != len(durations_s):
        raise ChainPlanError(
            f"script_lines ({len(script_lines)}) and durations_s "
            f"({len(durations_s)}) must be the same length")
    if audio_paths is not None and len(audio_paths) != len(script_lines):
        raise ChainPlanError(
            f"audio_paths ({len(audio_paths)}) must match script length "
            f"({len(script_lines)}) when given")
    if overlap_frames < 0:
        raise ChainPlanError(f"overlap_frames must be >= 0: {overlap_frames}")

    name_to_sn = _sn(characters)
    try:
        chars = tuple(
            ChainCharacter(**c) for c in characters)
    except TypeError as e:
        raise ChainPlanError(f"bad character entry: {e}") from e

    clips: List[ChainClip] = []
    cursor_s = 0.0
    prev_clip: Optional[ChainClip] = None
    for i, (line, duration_s) in enumerate(zip(script_lines, durations_s),
                                            start=1):
        speaker = line.get("speaker", "")
        sn = name_to_sn.get(speaker)
        if sn is None:
            raise ChainPlanError(
                f"script line {i}: unknown speaker {speaker!r} (roster: "
                f"{sorted(name_to_sn)})")
        try:
            full_frames = check_duration_on_grid(duration_s, _FPS)
        except Exception as e:  # GridError from renderer policy
            raise ChainPlanError(
                f"script line {i}: duration {duration_s}s rejected by "
                f"grid policy: {e}") from e
        frames = full_frames if prev_clip is None else full_frames - overlap_frames
        if frames <= 0:
            raise ChainPlanError(
                f"script line {i}: full grid length {full_frames}f minus "
                f"overlap {overlap_frames}f is not a positive clip length")
        path = (audio_paths[i - 1] if audio_paths is not None
                else f"audio/clip{i:04d}.wav")
        clip = ChainClip(
            index=i,
            shot_prompt=_speaker_template(sn, line.get("text", "")),
            speaker_sn=sn,
            duration_s=frames / _FPS,
            frames=frames,
            audio=ClipAudio(path=path, start_s=cursor_s,
                            padded_duration_s=frames / _FPS),
            seed=_seed_for(line, i),
            status="pending",
            previous_clip_end_frame=(
                None if prev_clip is None else {
                    "clip_index": prev_clip.index,
                    "frame": prev_clip.frames - 1,
                }),
        )
        clips.append(clip)
        cursor_s += clip.duration_s
        prev_clip = clip

    plan = ChainPlan(
        global_prompt=_global_prompt(characters),
        characters=chars,
        clips=tuple(clips),
        overlap_frames=overlap_frames,
        fps=_FPS,
    )
    validate_chain_plan(plan)
    return plan


# ── Shot 1 proven recipe config (inline minimal builder) ────────────

def _shot1_recipe_config(plan: ChainPlan, clip: ChainClip,
                         characters: Sequence[ChainCharacter],
                         plate_paths: Optional[Sequence[str]]) -> Dict[str, Any]:
    """Proven 3-image-ref recipe: two-shot anchor + charA + charB plates."""
    refs = list(plate_paths) if plate_paths is not None else [
        f"plates/{c.sn_tag.lower()}-anchor.png" for c in characters[:1]
    ] + [f"plates/{c.sn_tag.lower()}-plate.png" for c in characters]
    return {
        "clip_index": clip.index,
        "kind": "shot1_three_ref_recipe",
        "prompt": f"{plan.global_prompt} {clip.shot_prompt}",
        "image_start": None,
        "image_refs": refs,  # anchor + one plate per character
        "steps": _RECIPE_STEPS,
        "spectrum_cache": True,
        "resolution": [480, 832],
        "frames": clip.frames,
        "force_fps": _FPS,
        "seed": clip.seed,
        "audio": {"path": clip.audio.path, "apad": True,
                  "start_s": clip.audio.start_s,
                  "padded_duration_s": clip.audio.padded_duration_s},
    }


def _continuation_config(plan: ChainPlan, clip: ChainClip) -> Dict[str, Any]:
    """First-frame continuation: previous last frame in, plates stand down."""
    ref = clip.previous_clip_end_frame or {}
    return {
        "clip_index": clip.index,
        "kind": "first_frame_continuation",
        "prompt": f"{plan.global_prompt} {clip.shot_prompt}",
        "image_start": {
            "kind": "last_frame",
            "clip_index": ref.get("clip_index"),
            "frame": ref.get("frame"),
        },
        "image_refs": None,  # reference plates stand down after shot 1
        "steps": _RECIPE_STEPS,
        "spectrum_cache": True,
        "resolution": [480, 832],
        "frames": clip.frames,
        "force_fps": _FPS,
        "seed": clip.seed,
        "audio": {"path": clip.audio.path, "apad": True,
                  "start_s": clip.audio.start_s,
                  "padded_duration_s": clip.audio.padded_duration_s},
    }


def emit_render_manifest(
    plan: ChainPlan,
    plate_paths: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    """Render-order manifest: shot 1 = 3-ref recipe, shots 2+ = continuations."""
    validate_chain_plan(plan)
    manifest: List[Dict[str, Any]] = []
    for clip in plan.clips:
        if clip.index == 1:
            manifest.append(_shot1_recipe_config(
                plan, clip, plan.characters, plate_paths))
        else:
            manifest.append(_continuation_config(plan, clip))
    return manifest


__all__ = [
    "OVERLAP_FRAMES", "ChainPlanError", "build_chain_plan",
    "emit_render_manifest",
]
