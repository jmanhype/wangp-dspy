"""H3 production recipe — the 2026-09-01 user-eye-verified MiniMax H3
Ref2VA multi-character two-shot render recipe, encoded as code.

Programmatic ONLY: the prompt is assembled here with exact template
structure — never edited by hand after the fact (string surgery caused
two bad renders on the 3090). Speaker and listener are generated
together and consistency is asserted before emit.

Verified recipe (do not deviate):
  image_refs = [two-shot composition anchor, charA identity plate,
                charB identity plate] — Picture 1 is the composition
  anchor, Subject N identities come from Pictures 2/3.
  480x832, 73 frames (3.042s) or 56 (2.333s), seed 904, profile 3,
  sdpa attention (sage crashes), weak audio 'A', audio_guide = user wav
  padded (apad) to the exact grid duration, 20 inference steps,
  skip_steps_cache_type='spectrum', skip_steps_multiplier=0.08.

Banned (hard gates, see _GPT_IMAGE_RE / BANNED_RETENTION_PHRASES /
turbo gate):
  - turbo LoRAs on multi-ref/two-shot renders (breaks composition,
    user-rejected twice); turbo allowed ONLY single-ref closeups.
  - 'fully preserved' / 'continues directly' retention language
    (freezes frames).
  - gpt-image-generated first frames (freeze risk; use original-render
    crops).
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

from services.director.renderers.policy import (
    GridError,
    check_duration_on_grid,
)

__all__ = ["H3RecipeError", "build_render_config"]


class H3RecipeError(ValueError):
    """Typed rejection for any recipe-violating input."""


# ── verified envelope constants ────────────────────────────────────────

WIDTH, HEIGHT = 480, 832
SEED = 904
PROFILE = 3
ATTENTION = "sdpa"        # sage crashes
AUDIO_PROMPT_TYPE = "A"   # weak audio
INFERENCE_STEPS = 20
SKIP_STEPS_CACHE_TYPE = "spectrum"
SKIP_STEPS_MULTIPLIER = 0.08
FPS = 24

ALLOWED_ATTENTION = ("sdpa", "flash", "flash3", "sageattn", "auto")

# gpt-image-generated first frames: freeze risk. Case-insensitive over
# the path/filename; original-render crops are the verified source.
_GPT_IMAGE_RE = re.compile(r"gpt[-_ ]?image", re.IGNORECASE)

# Retention language that freezes frames in the rendered output.
BANNED_RETENTION_PHRASES = (
    "fully preserved",
    "continues directly",
)

# Turbo LoRAs break multi-ref composition (user-rejected twice).
_TURBO_RE = re.compile(r"turbo", re.IGNORECASE)


def _reject_blank(value: str, label: str) -> str:
    v = (value or "").strip()
    if not v:
        raise H3RecipeError(f"{label} must be nonempty")
    return v


def _check_retention_language(*texts: str) -> None:
    for text in texts:
        low = text.lower()
        for phrase in BANNED_RETENTION_PHRASES:
            if phrase in low:
                raise H3RecipeError(
                    f"banned retention language {phrase!r} freezes frames "
                    f"(found in: {text[:80]!r})")


def _check_gpt_image(*paths: str) -> None:
    for path in paths:
        if path and _GPT_IMAGE_RE.search(os.path.basename(path)):
            raise H3RecipeError(
                f"gpt-image-generated asset {path!r} is banned (freeze "
                "risk) — use original-render crops")


def _check_turbo_gate(loras: List[str], multi_ref: bool) -> None:
    for lora in loras:
        if multi_ref and _TURBO_RE.search(lora):
            raise H3RecipeError(
                f"turbo LoRA {lora!r} is banned on multi-ref two-shot "
                "renders (breaks composition; allowed ONLY for "
                "single-ref closeups)")


def _build_prompt(anchor_plate: str,
                  character_plates: List[Dict[str, str]],
                  speaker_index: int,
                  line: str,
                  scene_staging: str,
                  listening_detail: str,
                  ambience: str,
                  continuous_lines: Optional[List[Dict[str, Any]]]) -> str:
    n = len(character_plates)

    # HEAD — Picture 1 anchor + per-subject identity from Pictures 2..N+1
    head_lines = [
        f"<Picture 1> is the two-shot composition anchor: "
        f"{scene_staging}.",
        "",
    ]
    for i, plate in enumerate(character_plates):
        head_lines += [
            f"<Subject {i + 1}> (from <Picture {i + 2}>):",
            plate["description"],
            "",
        ]
    head = "\n".join(head_lines).rstrip("\n")

    # SUMMARY — composition holds, identities retained, speaker animated.
    speaker_name = f"<Subject {speaker_index + 1}>"
    listener_names = [f"<Subject {i + 1}>"
                      for i in range(n) if i != speaker_index]
    summary = (
        "Summary: [reference generation] The composition of <Picture 1> "
        "holds: both characters in their positions. All subjects retain "
        f"their exact identities from their reference pictures. "
        f"{speaker_name} speaks with lively animated mouth movement: "
        f"(S{speaker_index + 1}) says: <d>[English] {line}</d> "
    )
    summary += " ".join(
        f"{name} listens, mouth closed, {listening_detail}."
        for name in listener_names)

    # Continuous multi-line shots: [Shot N] At HH:MM:SSS timestamped
    # speaker attribution per the official guide.
    cont_block = ""
    if continuous_lines:
        cont_parts = []
        for c in continuous_lines:
            c_idx = c["speaker_index"]
            if not isinstance(c_idx, int) or not 0 <= c_idx < n:
                raise H3RecipeError(
                    f"continuous_lines speaker_index {c_idx!r} out of "
                    f"range for {n} character plates")
            c_line = _reject_blank(c.get("line", ""), "continuous line")
            _check_retention_language(c_line)
            cont_parts.append(
                f"[Shot {c.get('shot')}] At {c.get('timestamp')} "
                f"<Subject {c_idx + 1}> (S{c_idx + 1}) says: "
                f"<d>[English] {c_line}</d>")
        cont_block = "\n" + "\n".join(cont_parts)

    footer = f"Non-diegetic music: none. Ambient: {ambience}."

    return f"{head}\n\n{summary}{cont_block}\n\n{footer}"


def build_render_config(
    anchor_plate: str,
    character_plates: List[Dict[str, str]],
    speaker_index: int,
    line: str,
    audio_path: str,
    duration_s: float,
    scene_staging: str,
    listening_detail: str,
    ambience: str,
    continuous_lines: Optional[List[Dict[str, Any]]] = None,
    loras: Optional[List[str]] = None,
    attention: str = ATTENTION,
) -> Dict[str, Any]:
    """Emit the EXACT verified wgp config dict + prompt for one two-shot.

    character_plates: [{"path": str, "description": str}, ...] — Subject
    N takes its identity from <Picture N+1>; Picture 1 is the anchor.
    speaker_index indexes character_plates (0-based) and is asserted to
    match the (S{N}) tag emitted in the prompt.
    """
    loras = list(loras or [])
    if not character_plates:
        raise H3RecipeError("character_plates must be nonempty")
    for plate in character_plates:
        _reject_blank(plate.get("path", ""), "character plate path")
        _reject_blank(plate.get("description", ""),
                      "character plate description")
    if not isinstance(speaker_index, int) or not 0 <= speaker_index < len(
            character_plates):
        raise H3RecipeError(
            f"speaker_index {speaker_index!r} out of range for "
            f"{len(character_plates)} character plates")
    line = _reject_blank(line, "line")
    _reject_blank(anchor_plate, "anchor_plate")
    _reject_blank(audio_path, "audio_path")
    scene_staging = _reject_blank(scene_staging, "scene_staging")
    listening_detail = _reject_blank(listening_detail, "listening_detail")
    ambience = _reject_blank(ambience, "ambience")

    # Banned-language gate over ALL user-supplied text.
    _check_retention_language(line, scene_staging, listening_detail,
                              ambience,
                              *[p["description"] for p in character_plates])

    # Banned-asset gates.
    _check_gpt_image(anchor_plate, audio_path,
                     *[p["path"] for p in character_plates])
    _check_turbo_gate(loras, multi_ref=len(character_plates) > 1)

    # Attention: sage crashes on H3 Ref2VA.
    if attention == "sage":
        raise H3RecipeError(
            "sage attention crashes on H3 Ref2VA — use 'sdpa' "
            "(verified recipe)")

    # Grid: duration_s is SECONDS; frames = round(duration_s * 24).
    try:
        frames = check_duration_on_grid(duration_s, fps=FPS)
    except GridError as e:
        raise H3RecipeError(str(e)) from e

    prompt = _build_prompt(
        anchor_plate, character_plates, speaker_index, line,
        scene_staging, listening_detail, ambience, continuous_lines)

    # Consistency assertion before emit: the (S{N}) tag speaking in the
    # Summary must match speaker_index. (Continuous [Shot N] blocks may
    # legitimately attribute other subjects at other timestamps.)
    summary_seg = prompt.split("\n\n", 1)[1].split("\n[Shot")[0]
    if f"(S{speaker_index + 1}) says:" not in summary_seg:
        raise H3RecipeError(
            f"summary segment does not attribute speech to S{speaker_index + 1}")
    for i in range(len(character_plates)):
        if i != speaker_index and f"(S{i + 1}) says:" in summary_seg:
            raise H3RecipeError(
                f"summary segment wrongly attributes speech to S{i + 1}")
    # No template placeholder leaks.
    for token in ("<line>", "<charA description>", "<charB description>",
                  "<scene staging description>", "<listening detail>",
                  "<ambience>", "PLACEHOLDER", "TODO"):
        if token in prompt:
            raise H3RecipeError(f"placeholder leak in prompt: {token!r}")

    config = {
        "image_refs": [anchor_plate] + [p["path"] for p in character_plates],
        "width": WIDTH,
        "height": HEIGHT,
        "frames": frames,
        "fps": FPS,
        "seed": SEED,
        "profile": PROFILE,
        "attention": attention,
        "audio_prompt_type": AUDIO_PROMPT_TYPE,
        "audio_guide": audio_path,
        "audio_pad": "apad to exact grid duration",
        "inference_steps": INFERENCE_STEPS,
        "skip_steps_cache_type": SKIP_STEPS_CACHE_TYPE,
        "skip_steps_multiplier": SKIP_STEPS_MULTIPLIER,
    }
    if loras:
        config["loras"] = loras
    return {"config": config, "prompt": prompt}
