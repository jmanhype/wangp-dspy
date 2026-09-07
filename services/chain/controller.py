"""Chain controller — build Chain Plans and render-order manifests.

Pure config/plan layer: no GPU, no rendering, no ffmpeg. The technique
(last frame of shot N = first frame of shot N+1 via H3's trained
continuation task; reference plates stand down after shot 1) is ported
from joeygambino/MiniMax-H3-Multishot-Workflow; the Chain Plan JSON
shape follows RwGrid/ComfyUI-MiniMaxH3-Contex-Loop's
H3_CHAIN_FORMAT_GUIDE.

Shot 1 renders from the proven 3-image-ref recipe via
renderers/h3_recipe.py::build_render_config (two-shot anchor + character
plates, 20 steps, spectrum cache, 480x832, apad) — its gates (turbo
LoRA ban on multi-ref, banned retention language, gpt-image assets)
are active on the chain path. Shots 2+ are first-frame continuations.
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
from services.chain.keyframes import emit_fl2va_job, emit_r2i_job
from services.director.renderers.h3_recipe import build_render_config
from services.director.renderers.policy import check_duration_on_grid
from predict.continuation_lane import ContinuationExtras

OVERLAP_FRAMES = 22  # upstream H3_CHAIN_FORMAT_GUIDE default; see docs
_FPS = 24
_RECIPE_STEPS = 20

# Chain-side staging defaults for the recipe prompt template. The
# recipe (h3_recipe.py) owns the template; the chain supplies
# neutral staging text and character descriptions from the roster.
_DEFAULT_SCENE_STAGING = (
    "medium two-shot, both characters in frame, eye-level camera")
_DEFAULT_LISTENING_DETAIL = (
    "steady gaze, subtle nod, holding still")
_DEFAULT_AMBIENCE = "quiet room tone, faint machinery hum"


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
    continuation_mode: bool = False,
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
    if not isinstance(continuation_mode, bool):
        raise ChainPlanError("continuation_mode must be bool")
    if overlap_frames < 0:
        raise ChainPlanError(f"overlap_frames must be >= 0: {overlap_frames}")
    if continuation_mode:
        overlap_frames = 0

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
        if continuation_mode:
            if abs(float(duration_s) - 2.0) > 1e-9:
                raise ChainPlanError(
                    f"script line {i}: continuation duration must be "
                    f"exactly 2.0s, got {duration_s!r}")
            full_frames = 48
            frames = 48
        else:
            try:
                full_frames = check_duration_on_grid(duration_s, _FPS)
            except Exception as e:  # GridError from renderer policy
                raise ChainPlanError(
                    f"script line {i}: duration {duration_s}s rejected by "
                    f"grid policy: {e}") from e
            frames = (full_frames if prev_clip is None
                      else full_frames - overlap_frames)
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
        continuation_mode=continuation_mode,
    )
    validate_chain_plan(plan)
    return plan


# ── Shot 1 proven recipe config (inline minimal builder) ────────────

def _shot1_recipe_config(plan: ChainPlan, clip: ChainClip,
                         characters: Sequence[ChainCharacter],
                         plate_paths: Optional[Sequence[str]],
                         loras: Optional[Sequence[str]]) -> Dict[str, Any]:
    """Proven 3-image-ref recipe: two-shot anchor + one plate per character.

    Delegates to renderers/h3_recipe.py::build_render_config so the
    verified prompt template and all hard gates apply to shot 1.
    """
    sn_order = [c.sn_tag for c in characters]
    speaker_index = sn_order.index(clip.speaker_sn)
    # shot_prompt is "{sn} speaks: {line}" — recover the raw line text.
    _, _, line = clip.shot_prompt.partition("speaks: ")

    if plate_paths is not None:
        anchor_plate, char_paths = plate_paths[0], list(plate_paths[1:])
    else:
        anchor_plate = f"plates/{clip.speaker_sn.lower()}-anchor.png"
        char_paths = [f"plates/{c.sn_tag.lower()}-plate.png"
                      for c in characters]
    character_plates = [
        {"path": path, "description": c.description}
        for path, c in zip(char_paths, characters)]

    built = build_render_config(
        anchor_plate=anchor_plate,
        character_plates=character_plates,
        speaker_index=speaker_index,
        line=line,
        audio_path=clip.audio.path,
        duration_s=clip.duration_s,
        scene_staging=_DEFAULT_SCENE_STAGING,
        listening_detail=_DEFAULT_LISTENING_DETAIL,
        ambience=_DEFAULT_AMBIENCE,
        loras=list(loras) if loras is not None else None,
    )
    config, prompt = built["config"], built["prompt"]
    return {
        "clip_index": clip.index,
        "kind": "shot1_three_ref_recipe",
        "prompt": f"{plan.global_prompt}\n\n{prompt}",
        "image_start": None,
        "image_refs": config["image_refs"],
        "recipe": config,  # full verified envelope from h3_recipe
        "steps": config["inference_steps"],
        "spectrum_cache": config["skip_steps_cache_type"] == "spectrum",
        "resolution": [config["width"], config["height"]],
        "frames": clip.frames,
        "force_fps": _FPS,
        "seed": clip.seed,
        "audio": {"path": clip.audio.path, "apad": True,
                  "start_s": clip.audio.start_s,
                  "padded_duration_s": clip.audio.padded_duration_s},
    }


def _continuation_config(
    plan: ChainPlan,
    clip: ChainClip,
    plate_paths: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Ref2Va continuation with typed extras and a resolvable frame ref.

    Before the prior render completes, chain:// is an explicit
    placeholder. advance_chain replaces it with a verified PNG before
    the dependent job is admitted.
    """
    # Preserve the legacy multishot/FL2VA manifest contract.  The stricter
    # Ref2Va extras below are only for the explicit continuation profile.
    if not plan.continuation_mode:
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
            "image_refs": None,
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

    refs = list(plate_paths or [])
    if refs:
        anchor = str(refs[0])
        char_paths = [str(p) for p in refs[1:]]
    else:
        anchor = "plates/anchor.png"
        char_paths = [f"plates/{c.sn_tag.lower()}-plate.png"
                      for c in plan.characters]
    by_sn = {c.sn_tag: char_paths[i] for i, c in
             enumerate(plan.characters) if i < len(char_paths)}
    silent = next((c for c in plan.characters
                   if c.sn_tag != clip.speaker_sn), None)
    silent_ref = (by_sn.get(silent.sn_tag) if silent is not None else anchor)
    ref = clip.previous_clip_end_frame or {}
    if clip.index == 1:
        image_start = anchor
    else:
        image_start = (
            f"chain://clip{int(ref.get('clip_index', clip.index - 1)):04d}/"
            "last_frame")
    image_refs = [image_start, str(silent_ref)]
    extras = ContinuationExtras(
        image_prompt_type="S",
        video_prompt_type="I",
        audio_prompt_type="A",
        image_start=image_start,
        image_refs=image_refs,
        audio_guide=clip.audio.path,
        video_length=48,
        requested_frames=48,
    )
    extra = extras.to_extra()
    provenance = {
        "source_master": clip.audio.path,
        "vocal_stem": clip.audio.path,
        "whisper_map": clip.audio.path,
        "keeper_window_s": [0.0, 2.0],
    }
    return {
        "clip_index": clip.index,
        "kind": "ref2va_render",
        "model_type": "minimax_h3_ref2va_pruned",
        "prompt": f"{plan.global_prompt} {clip.shot_prompt}",
        "image_start": image_start,
        "image_refs": image_refs,
        "image_prompt_type": "S",
        "video_prompt_type": "I",
        "audio_prompt_type": "A",
        "audio_guide": clip.audio.path,
        "audio_provenance": provenance,
        "audio_policy": {"discard_rendered_audio": True},
        "guide_duration_s": 2.0,
        "shot_duration_s": 2.0,
        "audio_length_frames": 48,
        "video_length": 48,
        "requested_frames": 48,
        "continuation_extras": extra,
        "steps": _RECIPE_STEPS,
        "spectrum_cache": True,
        "resolution": [480, 832],
        "frames": 48,
        "force_fps": _FPS,
        "seed": clip.seed,
        "chain": {
            "index": clip.index,
            "previous": ref.get("clip_index"),
            "re_anchor": clip.index == 1,
        },
        "audio": {"path": clip.audio.path, "apad": True,
                  "start_s": clip.audio.start_s,
                  "padded_duration_s": 2.0},
    }


def emit_render_manifest(
    plan: ChainPlan,
    plate_paths: Optional[Sequence[str]] = None,
    loras: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    """Render-order manifest: shot 1 = 3-ref recipe, shots 2+ = continuations.

    loras (optional) apply to the shot-1 recipe call and pass through its
    gates (turbo LoRAs on multi-ref two-shots raise H3RecipeError).
    """
    validate_chain_plan(plan)
    manifest: List[Dict[str, Any]] = []
    for clip in plan.clips:
        if plan.continuation_mode:
            manifest.append(_continuation_config(
                plan, clip, plate_paths=plate_paths))
        elif clip.index == 1:
            manifest.append(_shot1_recipe_config(
                plan, clip, plan.characters, plate_paths, loras))
        elif clip.end_pose:
            # FL2VA keyframe-target path: R2I pose-target render first,
            # then the first+last job consuming its final frame
            # (fl2va.needs = r2i job id).
            r2i = emit_r2i_job(clip, plan, plate_paths=plate_paths)
            manifest.append(r2i)
            manifest.append(emit_fl2va_job(
                clip, plan,
                f"render/clip{clip.index:04d}/{r2i['job_id']}"
                "_last_frame.png",
                needs=r2i["job_id"]))
        else:
            manifest.append(_continuation_config(
                plan, clip, plate_paths=plate_paths))
    return manifest


__all__ = [
    "OVERLAP_FRAMES", "ChainPlanError", "build_chain_plan",
    "emit_render_manifest",
]
