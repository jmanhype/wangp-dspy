"""Semantic product-mode routing table (PR #62 amendment).

Five product modes, one authority. All enforcement raises BEFORE any
config emits; model_type is DERIVED from mode (+ render_profile) and
never accepted as input — a config carrying a raw model_type is
rejected because model_type is an output of derivation, not an input.

WanGP L2VA ground truth (encoded here like PR #61 did for "SE"):
  models/minimax_h3/minimax_h3_handler.py exposes
  image_prompt_types_allowed = "TSEVL" for the FL2VA family (non
  reference_mode), and shared/deepy/tool_settings.build_generation_task
  derives the image_prompt_type flags from which of image_start /
  image_end / image_refs are actually set:
    - "T" is added when no start image is supplied (text-only path)
    - "S" only when image_start is present
    - "E" only when image_end is present (and dropped when absent)
  So L2VA (end-frame ONLY) is image_end without image_start ->
  image_prompt_type "E" on the FL2VA architecture — there is no
  separate L2VA model; last-frame-only is a flag combination, exactly
  like the keyframes PR's "SE" (start+end -> "SE") finding.
  T2VA -> "T"; START_END -> "SE"; END_ONLY -> "E"; REF2VA
  reference_mode allows only "T" image prompt types plus image_refs
  ("I"-style reference images) and audio guides.
"""
from __future__ import annotations

import enum
from typing import Any, Dict, FrozenSet, Iterable, Mapping, Optional

from predict.model_types import (
    H3_FL2VA_MODEL_TYPE,
    HOST_MODEL_ALLOWLIST,
    REF2VA_MODEL_TYPE,
)

__all__ = [
    "ProductMode", "ModeError",
    "CANONICAL_H3_FOR_MODE", "HOST_MODEL_ALLOWLIST",
    "IMAGE_PROMPT_TYPE_FOR_MODE",
    "derive_model_type", "validate_mode_inputs", "unwrap_continuation",
]


class ModeError(ValueError):
    """Typed rejection for any mode-table violation."""


class ProductMode(enum.Enum):
    FL2VA_TEXT = "FL2VA_TEXT"
    FL2VA_START_END = "FL2VA_START_END"
    FL2VA_END_ONLY = "FL2VA_END_ONLY"
    REF2VA_IDENTITY_AUDIO = "REF2VA_IDENTITY_AUDIO"
    CONTINUATION = "CONTINUATION"


# ── derived model_type (outputs, never inputs) ─────────────────────────
# matches host/wangp_adapter._KNOWN_MODEL_TYPES keys
CANONICAL_H3_FOR_MODE: Dict[ProductMode, str] = {
    ProductMode.FL2VA_TEXT: H3_FL2VA_MODEL_TYPE,
    ProductMode.FL2VA_START_END: H3_FL2VA_MODEL_TYPE,
    ProductMode.FL2VA_END_ONLY: H3_FL2VA_MODEL_TYPE,
    # HOST TRUTH (operator audit 2026-09-01, probed on the 3090
    # Wan2GP checkout): the handler exposes ONLY `minimax_h3_ref2va`
    # and `minimax_h3_ref2va_pruned` — there is NO
    # `minimax_h3_ref2va_lip_sync` handler, so the old derived name
    # would crash at the host. This is the proven production model.
    ProductMode.REF2VA_IDENTITY_AUDIO: REF2VA_MODEL_TYPE,
}


# The REAL WanGP H3 handler names the 3090 host actually serves
# (operator audit 2026-09-01, probed live). derive_model_type fails
# closed (typed ModeError) when a derivation result is not in this
# set — a map entry drifting off host truth is a configuration error
# caught at derivation time, never a crash on the GPU box.
# WanGP image_prompt_type flag per mode (see module docstring).
IMAGE_PROMPT_TYPE_FOR_MODE: Dict[ProductMode, str] = {
    ProductMode.FL2VA_TEXT: "T",
    ProductMode.FL2VA_START_END: "SE",
    ProductMode.FL2VA_END_ONLY: "E",
    ProductMode.REF2VA_IDENTITY_AUDIO: "I",
}

TEMPORAL_STRATEGIES = frozenset({"last_frame_chain", "sliding_window"})

# render_profile sub-object — the not-a-mode list lives HERE and
# nowhere else (pruned/int8/PDD/turbo/attention/steps/cache).
RENDER_PROFILE_KEYS = frozenset({
    "pruned", "int8", "pdd", "turbo", "attention", "steps", "cache"})

# input keys a mode spec may carry (model_type deliberately absent:
# it is derived, rule 3)
_ALLOWED_SPEC_KEYS = frozenset({
    "mode", "prompt",
    "image_start", "image_end", "image_refs", "audio_guide",
    "render_profile",
    "continuation_mode", "temporal_strategy", "prior_clip",
})

# keys that count as "frame refs" for the FL2VA_TEXT prohibition
_FRAME_REF_KEYS = ("image_start", "image_end", "image_refs")


def _coerce_mode(mode: Any) -> ProductMode:
    try:
        return ProductMode(str(mode))
    except ValueError:
        raise ModeError(
            f"mode {mode!r} is not one of the five product modes "
            f"{[m.value for m in ProductMode]}") from None


def _refs(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [v for v in value if v]
    return [value]


def _check_render_profile(profile: Any) -> None:
    if profile is None:
        return
    if not isinstance(profile, Mapping):
        raise ModeError(
            f"render_profile must be a sub-object (dict), got "
            f"{type(profile).__name__!r} — the not-a-mode list "
            "(pruned/int8/PDD/turbo/attention/steps/cache) lives here "
            "and nowhere else")
    bad = set(profile) - RENDER_PROFILE_KEYS
    if bad:
        raise ModeError(
            f"render_profile keys {sorted(bad)} are not render-profile "
            f"knobs (allowed, sorted: {sorted(RENDER_PROFILE_KEYS)}) — "
            "modes are not selected here")


def _check_turbo(mode: ProductMode, spec: Mapping) -> None:
    # rule 5: reuse/extend the #57 gate — turbo breaks multi-ref
    # composition; banned on multi-reference REF2VA_IDENTITY_AUDIO.
    profile = spec.get("render_profile") or {}
    if not (profile.get("turbo") if isinstance(profile, Mapping) else False):
        return
    if mode is ProductMode.REF2VA_IDENTITY_AUDIO and len(
            _refs(spec.get("image_refs"))) > 1:
        raise ModeError(
            "turbo is banned on multi-reference REF2VA_IDENTITY_AUDIO "
            "(breaks composition — #57 gate: turbo allowed ONLY "
            "single-ref)")


def derive_model_type(mode: Any, *, detail: bool = False,
                      render_profile: Optional[Mapping] = None) -> Any:
    """DERIVED model_type for a product mode — never user-entered.

    detail=True returns the derivation record including the WanGP
    image_prompt_type flag (T / SE / E / I — see module docstring).
    """
    m = _coerce_mode(mode)
    if m is ProductMode.CONTINUATION:
        raise ModeError(
            "CONTINUATION is orchestration, not a model mode — unwrap "
            "it to the underlying I2VA/FL2VA-style job first "
            "(unwrap_continuation)")
    model_type = CANONICAL_H3_FOR_MODE[m]
    # fail closed against host truth: a derivation result that is not
    # a REAL WanGP handler name is a configuration error — catch it
    # here, never on the GPU box.
    if model_type not in HOST_MODEL_ALLOWLIST:
        raise ModeError(
            f"derived model_type {model_type!r} for mode {m.value} is "
            f"not in HOST_MODEL_ALLOWLIST {sorted(HOST_MODEL_ALLOWLIST)} "
            "— the mode table drifted off host truth; refusing to "
            "emit a config the host would crash on")
    out: Dict[str, Any] = {
        "model_type": model_type,
        "image_prompt_type": IMAGE_PROMPT_TYPE_FOR_MODE[m],
    }
    return out if detail else out["model_type"]


def _check_continuation(spec: Mapping,
                        verified_artifacts: FrozenSet[str]) -> None:
    strategy = spec.get("temporal_strategy")
    if strategy not in TEMPORAL_STRATEGIES:
        raise ModeError(
            f"CONTINUATION requires temporal_strategy in "
            f"{sorted(TEMPORAL_STRATEGIES)} — got {strategy!r}")
    prior = spec.get("prior_clip")
    if not (isinstance(prior, Mapping) and prior.get("path")):
        raise ModeError(
            "CONTINUATION requires a prior-clip artifact "
            "({'path': ...} with an optionally verified last_frame) — "
            f"got {prior!r}")
    if prior["path"] not in verified_artifacts:
        raise ModeError(
            f"prior clip {prior['path']!r} is not a VERIFIED artifact "
            "(path exists in job records / manifest, verify-before-"
            "trust result) — an unverified prior cannot seed a "
            "continuation")
    frame = prior.get("last_frame")
    if frame and frame not in verified_artifacts:
        raise ModeError(
            f"prior-clip last frame {frame!r} is not a VERIFIED "
            "artifact — cannot fabricate a frame path")


def validate_mode_inputs(spec: Mapping, *,
                         verified_artifacts: Iterable[str] = frozenset()
                         ) -> ProductMode:
    """Enforce rules 1-6 BEFORE any config emits. Returns the mode."""
    if not isinstance(spec, Mapping):
        raise ModeError(f"mode spec must be a mapping, got {spec!r}")
    if "mode" not in spec or spec.get("mode") is None:
        raise ModeError(
            f"mode is required (one of {[m.value for m in ProductMode]})"
            ) from None
    mode = _coerce_mode(spec["mode"])

    # rule 3: model_type is derived — a raw one as input is rejected
    if spec.get("model_type") is not None:
        raise ModeError(
            "model_type is DERIVED from mode + render_profile and must "
            "not be supplied as input — remove it; derivation happens "
            f"in derive_model_type (would be {CANONICAL_H3_FOR_MODE.get(mode)!r})")

    # rule 4: render_profile sub-object is the only not-a-mode home
    _check_render_profile(spec.get("render_profile"))

    image_start = spec.get("image_start")
    image_end = _refs(spec.get("image_end"))
    image_refs = _refs(spec.get("image_refs"))
    audio_guide = spec.get("audio_guide")

    # rule 2: required/forbidden inputs per mode
    if mode is ProductMode.FL2VA_TEXT:
        for key in _FRAME_REF_KEYS:
            if spec.get(key):
                raise ModeError(
                    "FL2VA_TEXT (T2VA) takes text only — frame refs "
                    f"({key}) are forbidden in this mode")
        if audio_guide:
            raise ModeError(
                "FL2VA_TEXT (T2VA) takes text only — audio_guide is "
                "forbidden in this mode")
    elif mode is ProductMode.FL2VA_START_END:
        if not image_start or not image_end:
            raise ModeError(
                "FL2VA_START_END requires BOTH a start frame and an "
                "end frame (image_prompt_type 'SE')")
    elif mode is ProductMode.FL2VA_END_ONLY:
        if image_start:
            raise ModeError(
                "FL2VA_END_ONLY (L2VA) forbids a start frame — WanGP "
                "adds the 'S' flag only when image_start is present")
        if len(image_end) != 1:
            raise ModeError(
                "FL2VA_END_ONLY (L2VA) requires EXACTLY ONE end-frame "
                f"ref — got {len(image_end)}")
    elif mode is ProductMode.REF2VA_IDENTITY_AUDIO:
        if not image_refs:
            raise ModeError(
                "REF2VA_IDENTITY_AUDIO requires >=1 image refs "
                "(identity plates / composition anchors)")
        if not audio_guide:
            raise ModeError(
                "REF2VA_IDENTITY_AUDIO requires an audio_guide")
    elif mode is ProductMode.CONTINUATION:
        # rule 6: verified prior artifact, cannot be fabricated
        _check_continuation(spec, frozenset(verified_artifacts))

    # rule 5: turbo gate (after inputs resolve)
    _check_turbo(mode, spec)
    return mode


def unwrap_continuation(spec: Mapping, *,
                        verified_artifacts: Iterable[str] = frozenset()
                        ) -> Dict[str, Any]:
    """Resolve CONTINUATION to the underlying model-mode job BEFORE
    render: validates (rule 6), then returns a concrete job spec with
    the real mode plus a temporal_strategy field. last_frame_chain
    seeds image_start from the prior clip's VERIFIED last frame.
    """
    validate_mode_inputs(spec, verified_artifacts=verified_artifacts)
    assert spec["mode"] == ProductMode.CONTINUATION.value  # noqa: S101
    inner = _coerce_mode(spec.get("continuation_mode",
                                  "FL2VA_START_END"))
    if inner is ProductMode.CONTINUATION:
        raise ModeError(
            "CONTINUATION cannot wrap CONTINUATION — unwrap to a "
            "concrete I2VA/FL2VA-style mode")
    out: Dict[str, Any] = dict(spec)
    out["mode"] = inner.value
    out["derived_from"] = ProductMode.CONTINUATION.value
    prior = spec.get("prior_clip") or {}
    if spec.get("temporal_strategy") == "last_frame_chain":
        # the prior's VERIFIED last frame becomes the start frame
        out["image_start"] = prior.get("last_frame")
    return out
