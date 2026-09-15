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
from predict.continuation_lane import (
    ContinuationExtras, build_picture_n_speaker_prompt,
)
from predict.job_config import (
    CONTINUATION_FRAMES_MIN,
    normalize_continuation_frame_count,
)
from predict.speaker_manifest import SpeakerTurn, build_speaker_manifest
from predict.model_types import REF2VA_MODEL_TYPE

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


def _spatial_anchor_prompt(characters: Sequence[dict]) -> str:
    """Describe the roster's left/right blocking as a hard continuation pin.

    The acceptance roster is ordered left-to-right (grandma, then soul), so
    retain that explicit identity wording where available. Other rosters get
    the same invariant without guessing character semantics.
    """
    if len(characters) < 2:
        return ("Spatial anchor: preserve the subject's exact position, scale, "
                "wardrobe, and framing from <Picture 1>; do not re-stage.")
    names = [str(c.get("name", "")).strip() for c in characters[:2]]
    lowered = [name.casefold() for name in names]
    grandma = next((names[i] for i, name in enumerate(lowered)
                    if "grandma" in name or "grandmother" in name), None)
    soul = next((names[i] for i, name in enumerate(lowered)
                 if "soul" in name), None)
    if grandma and soul:
        return ("Spatial anchor: the grandmother remains on the LEFT and the "
                "soul remains on the RIGHT, exactly as in <Picture 1> — "
                "preserve positions, scale, wardrobe, and framing; do not "
                "swap sides or re-stage the composition.")
    return (f"Spatial anchor: {names[0]} (S1) remains on the LEFT and "
            f"{names[1]} (S2) remains on the RIGHT, exactly as in "
            "<Picture 1> — preserve positions, scale, wardrobe, and "
            "framing; do not swap sides or re-stage the composition.")


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
            f"{pins}. {_spatial_anchor_prompt(characters)}")


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
    seed_override: Optional[int] = None,
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
            requested = int(round(float(duration_s) * _FPS))
            aligned = normalize_continuation_frame_count(requested)
            if requested != aligned:
                raise ChainPlanError(
                    f"script line {i}: continuation duration must be "
                    f"grid-aligned (minimum {CONTINUATION_FRAMES_MIN}f), "
                    f"got {duration_s!r} ({requested}f); use "
                    f"{aligned / _FPS:.3f}s")
            full_frames = aligned
            frames = aligned
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
            seed=(int(seed_override) if seed_override is not None
                  else _seed_for(line, i)),
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
    recipe_name: str = "production",
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
    explicit_silent = None
    if refs:
        anchor = str(refs[0])
        # DirectorRun also accepts the acceptance-run form
        # [anchor, silent_face] per cut. In that form the second ref is
        # already the selected silent character and must not be interpreted
        # as the first roster plate.
        explicit_silent = (str(refs[1]) if len(refs) == 2 else None)
        char_paths = [str(p) for p in refs[1:]]
    else:
        anchor = "plates/anchor.png"
        char_paths = [f"plates/{c.sn_tag.lower()}-plate.png"
                      for c in plan.characters]
    by_sn = {c.sn_tag: char_paths[i] for i, c in
             enumerate(plan.characters) if i < len(char_paths)}
    silent = next((c for c in plan.characters
                   if c.sn_tag != clip.speaker_sn), None)
    silent_ref = (explicit_silent or
                  (by_sn.get(silent.sn_tag) if silent is not None else anchor))
    ref = clip.previous_clip_end_frame or {}
    if clip.index == 1:
        image_start = anchor
    else:
        image_start = (
            f"chain://clip{int(ref.get('clip_index', clip.index - 1)):04d}/"
            "last_frame")
    legacy_v2 = recipe_name == "v2_legacy"
    golden = recipe_name == "golden_v3"
    image_refs = [image_start] if legacy_v2 else [image_start, str(silent_ref)]
    speaker_char = next(c for c in plan.characters
                        if c.sn_tag == clip.speaker_sn)
    speaker_prompt = None
    if not legacy_v2:
        speaker_prompt = build_picture_n_speaker_prompt(
            speaker_sn=clip.speaker_sn,
            silent_sn=(silent.sn_tag if silent is not None else clip.speaker_sn),
            line=clip.shot_prompt.partition("speaks: ")[2],
        )
    if golden:
        from predict.v3_recipe import build_v3_prompt
        if silent is None or len(plan.characters) != 2:
            raise ChainPlanError("golden_v3 requires exactly two character identities")
        speaker_prompt = build_v3_prompt(
            scene=plan.global_prompt.rstrip(". "),
            identities=" and ".join(c.description for c in plan.characters),
            speaker=f"{speaker_char.name}, {speaker_char.description}",
            delivery="speaks natural English",
            silent=f"{silent.name}, {silent.description}",
            silent_noun="character", silent_pronoun="their",
            speaker_noun=speaker_char.name,
            soundscape="scene ambience", first=clip.index == 1)
    speaker_manifest = build_speaker_manifest([SpeakerTurn(
        # Each render job carries its own one-turn manifest.  The film-level
        # run ledger records clip_index separately; per-job manifests must
        # still satisfy the v1 contiguous-from-one schema.
        turn_index=1,
        speaker_id=clip.speaker_sn,
        picture_n=1,
        audio_path=clip.audio.path,
        intended_text=clip.shot_prompt.partition("speaks: ")[2],
    )])
    extras = ContinuationExtras(
        image_prompt_type="S",
        video_prompt_type="I",
        audio_prompt_type="A",
        image_start=image_start,
        image_refs=image_refs,
        audio_guide=clip.audio.path,
        video_length=clip.frames,
        requested_frames=clip.frames,
        legacy_v2_prompt=legacy_v2 or golden,
    )
    extra = extras.to_extra()
    provenance = {
        "source_master": clip.audio.path,
        "vocal_stem": clip.audio.path,
        "whisper_map": clip.audio.path,
        "keeper_window_s": [0.0, clip.duration_s],
    }
    if recipe_name not in {"production", "golden_v3", "v2_legacy"}:
        raise ChainPlanError(
            f"unknown continuation recipe {recipe_name!r}; expected "
            "production, golden_v3, or v2_legacy")
    golden = recipe_name == "golden_v3"
    return {
        "clip_index": clip.index,
        "kind": "ref2va_render",
        "model_type": REF2VA_MODEL_TYPE,
        "speaker": speaker_char.name,
        "speaker_sn": clip.speaker_sn,
        # The visual judge must verify identity, not merely detect a moving
        # mouth. Keep both roster descriptions in the expected-speaker
        # context so an unrelated face cannot pass activity-only QC.
        "speaker_description": (
            f"{speaker_char.sn_tag} ({speaker_char.name}): "
            f"{speaker_char.description}; silent other "
            f"{silent.sn_tag} ({silent.name}): {silent.description}"
            if silent is not None else
            f"{speaker_char.sn_tag} ({speaker_char.name}): "
            f"{speaker_char.description}") + "; " +
            _spatial_anchor_prompt([
                {"name": c.name, "sn_tag": c.sn_tag}
                for c in plan.characters]),
        "dialogue_text": clip.shot_prompt.partition("speaks: ")[2],
        "action": "subtle natural listening and speaking motion",
        "prompt": (speaker_prompt if golden else f"{plan.global_prompt} {speaker_prompt}"
                   if speaker_prompt is not None else
                   f"{plan.global_prompt} {clip.shot_prompt}"),
        "image_start": image_start,
        "image_refs": image_refs,
        "image_prompt_type": "S",
        "video_prompt_type": "I",
        "audio_prompt_type": "A",
        "audio_guide": clip.audio.path,
        "audio_provenance": provenance,
        "speaker_manifest": speaker_manifest,
        "audio_policy": {"discard_rendered_audio": False},
        # Audio duration is unknown until probed. Never claim a WAV has the
        # cut's frame length just because the plan does.
        "guide_duration_s": None,
        "shot_duration_s": clip.duration_s,
        "audio_length_frames": None,
        "video_length": clip.frames,
        "requested_frames": clip.frames,
        "continuation_extras": extra,
        "steps": _RECIPE_STEPS,
        "spectrum_cache": True,
        "resolution": [480, 832],
        # The profile is a CLI-level WanGP selector. It is persisted in the
        # job envelope so the host seam cannot silently substitute profile 3
        # for the operator-validated v3 pair.
        "profile": 2 if golden else 3,
        "recipe_name": recipe_name,
        "frames": clip.frames,
        "force_fps": _FPS,
        "seed": clip.seed,
        "chain": {
            "index": clip.index,
            "previous": ref.get("clip_index"),
            "re_anchor": clip.index == 1,
        },
        "audio": {"path": clip.audio.path, "apad": True,
                  "start_s": clip.audio.start_s,
                  "padded_duration_s": clip.duration_s},
    }


def emit_render_manifest(
    plan: ChainPlan,
    plate_paths: Optional[Sequence[str]] = None,
    loras: Optional[Sequence[str]] = None,
    recipe_name: str = "production",
) -> List[Dict[str, Any]]:
    """Render-order manifest: shot 1 = 3-ref recipe, shots 2+ = continuations.

    loras (optional) apply to the shot-1 recipe call and pass through its
    gates (turbo LoRAs on multi-ref two-shots raise H3RecipeError).
    """
    validate_chain_plan(plan)
    manifest: List[Dict[str, Any]] = []
    for clip in plan.clips:
        if plan.continuation_mode:
            cut_plates = plate_paths
            if (plate_paths and isinstance(plate_paths[0], (list, tuple))):
                if len(plate_paths) != len(plan.clips):
                    raise ChainPlanError(
                        "per-cut plate_paths must contain one [anchor, silent_face] "
                        "pair for every continuation clip")
                cut_plates = plate_paths[clip.index - 1]
            manifest.append(_continuation_config(
                plan, clip, plate_paths=cut_plates,
                recipe_name=recipe_name))
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
                plan, clip, plate_paths=plate_paths,
                recipe_name=recipe_name))
    return manifest


__all__ = [
    "OVERLAP_FRAMES", "ChainPlanError", "build_chain_plan",
    "emit_render_manifest",
]
