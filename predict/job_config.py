r"""WanGPJobConfig — the SINGLE authority for WanGP job settings rules.

WD-l5bx: absorbs every scattered adapter assert (move-per-rule; the
adapter-side copies were deleted in the same commit that landed each
authority here):
1. force_fps STR typing — wgp's get_computed_fps len()s the field
   (measured against real pinned settings files).
2. frames floor >= 56 (WanGP handler frames_minimum: 56).
3. 5+17k frame-grid snap — normalize_frame_count lives HERE
   (measured: H3 renders 107/124/141... = 5+17k, min 107;
   WD-u4rv).
4. flat settings JSON — no nested lists/dicts (wgp reads a flat
   schema).
5. multi-shot separator: line-anchored '\n---\n' (WD-izly: wgp
   parse_script splits on the (?m)^---\s*$ regex — inline joins
   collapse shots).

Zero-model: deterministic validation only.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict, field
from typing import List, Optional

SCRIPT_SEPARATOR = "\n---\n"

# FLOOR TRUTH: WanGP's own handler config declares frames_minimum: 56
# for MiniMax H3 (verified live on the 3090). 56f (2.33s @ 24fps)
# rendered in the manual era with user-approved output. The previous
# 96f value was a SAFETY choice, not a model limit — it blocked
# legitimate 2s-class cuts.
SHOT_LENGTH_FLOOR_FRAMES = 56     # WanGP handler minimum (Selector layer)
H3_FRAMES_MIN = 107               # measured H3 grid minimum (5+17k)
H3_FRAMES_STEP = 17
H3_FRAMES_OFFSET = 5
# Ref2VA's per-cut continuation task is a distinct handler path, but H3
# still emits frames on its 5+17k latent grid. The smallest grid-aligned
# continuation cut is 56 frames (2.333s @ 24fps); 48-frame requests have
# been observed to return 45 frames and are not an admissible contract.
CONTINUATION_FRAMES_MIN = 56
CONTINUATION_FRAMES_STEP = H3_FRAMES_STEP
CONTINUATION_FRAMES_OFFSET = H3_FRAMES_OFFSET

# WD-l5bx review ruling: profile_selector re-exports these SAME
# constants (below) as its selection-time hints. job_config is the
# single DEFINITION site; the Selector's frame floor is a DISTINCT
# semantic layer — a selection-time hint fed to the LM (choose a shot
# length >= the semantic floor) — while job_config construction is the
# SUBMIT-TIME enforcement authority (typed rejection). Both layers
# intentionally read one definition (this module); the Selector adds
# no independent numeric bound.


class JobConfigError(ValueError):
    """Typed job-config validation failure."""


def normalize_frame_count(frame_count: int, minimum: int = H3_FRAMES_MIN,
                          step: int = H3_FRAMES_STEP,
                          offset: int = H3_FRAMES_OFFSET) -> int:
    """EXACT wgp semantics (clamp-then-ceil onto offset+k*step)."""
    frame_count = max(minimum, frame_count)
    step = max(1, step)
    offset = max(0, offset)
    if step <= 1:
        return frame_count
    return math.ceil(max(0, frame_count - offset) / step) * step + offset


def normalize_continuation_frame_count(frame_count: int) -> int:
    """Normalize a continuation request onto H3's 5+17k grid.

    Continuation cuts use the lower 56-frame handler floor (rather than the
    generic multishot 107-frame floor), while retaining the same latent-grid
    math. Snapping upward prevents a short render from truncating dialogue.
    """
    return normalize_frame_count(
        frame_count, minimum=CONTINUATION_FRAMES_MIN,
        step=CONTINUATION_FRAMES_STEP, offset=CONTINUATION_FRAMES_OFFSET)


@dataclass(frozen=True)
class WanGPJobConfig:
    model_type: str
    script: str
    prompt: str = "multishot"   # profile tag (shape-compat)
    width: int = 480
    height: int = 832
    frames_per_shot: int = 107
    num_inference_steps: int = 20
    guidance_scale: float = 1.0
    embedded_guidance_scale: float = 6.0
    force_fps: str = "24"
    seed: int = 42
    # Explicit policy knobs are kept out of persisted settings.  The
    # generic H3 lane retains the 56f floor + 5+17k snap; the continuation
    # lane opts into the validated 56f grid-aligned profile.
    snap_frames: bool = field(default=True, repr=False, compare=False)
    frames_floor: int = field(default=SHOT_LENGTH_FLOOR_FRAMES,
                               repr=False, compare=False)

    def __post_init__(self) -> None:
        # construction IS validation (adapter-assert parity: the old
        # inline checks raised at build_settings time)
        validate_job_config(self)
        # rule 3 applied HERE for the generic H3 lane.  Continuation jobs
        # deliberately opt out because their Ref2Va recipe owns the grid count.
        if self.snap_frames:
            object.__setattr__(self, "frames_per_shot",
                               normalize_frame_count(self.frames_per_shot))

    def to_settings_doc(self, *, flat: bool = True,
                        extra: Optional[dict] = None) -> dict:
        """Flat JSON settings document (rule 4).

        ``extra`` fields (Ref2VA lane: image_refs list, audio_prompt_type)
        are added BEFORE the flat-JSON walk, so the final shape —
        including the exceptions — is the shape that gets validated.

        ``flat=False`` explicitly scopes rule 4 to the GENERIC lane: the
        profile declares that its appended fields are sanctioned
        non-scalar extensions of the wgp settings schema (the Ref2VA
        reader consumes a list of image paths), not a violation.
        """
        doc = dict(asdict(self))
        # Internal validation policy is not part of the wgp settings schema.
        doc.pop("snap_frames", None)
        doc.pop("frames_floor", None)
        if extra:
            doc.update(extra)
        if not flat:
            # rule 4 explicitly scoped to the generic lane (WD-l5bx
            # review strong-rec: restructure so appended fields are
            # part of the validated shape OR the rule scopes to the
            # generic lane — this is the scoping branch)
            return doc
        for k, v in doc.items():
            if isinstance(v, (list, dict)):
                raise JobConfigError(
                    f"settings field {k!r} is nested ({type(v).__name__}) "
                    "— wgp settings are FLAT JSON only")
        return doc


def validate_job_config(cfg: WanGPJobConfig, *,
                        snap_frames: bool = True) -> List[str]:
    """Validate all five rules; returns violation strings, raises
    typed JobConfigError on the first hard failure (adapter assert
    parity: these were hard raises before, they stay hard)."""
    # rule 1: force_fps string typing
    if not isinstance(cfg.force_fps, str) or not cfg.force_fps.strip():
        raise JobConfigError(
            f"force_fps must be a nonempty STRING (wgp's "
            f"get_computed_fps len()s it), got {cfg.force_fps!r}")
    # rule 2: semantic floor
    if isinstance(cfg.frames_per_shot, bool) \
            or not isinstance(cfg.frames_per_shot, int):
        raise JobConfigError(
            "frames_per_shot must be an int (below the HARD floor "
            "it is a typed rejection)")
    if isinstance(cfg.frames_floor, bool) or not isinstance(
            cfg.frames_floor, int) or cfg.frames_floor <= 0:
        raise JobConfigError(
            f"frames_floor must be a positive int, got {cfg.frames_floor!r}")
    if cfg.frames_per_shot < cfg.frames_floor:
        raise JobConfigError(
            f"frames_per_shot {cfg.frames_per_shot}f is below the HARD "
            f"floor of {cfg.frames_floor}f (WanGP handler "
            f"frames_minimum; the "
            f"H3 minimum floor is {H3_FRAMES_MIN}f)")
    # rule 3: grid snap (single authority — normalize_frame_count)
    if snap_frames and cfg.frames_per_shot < H3_FRAMES_MIN:
        # accepted at the floor; H3 will render the snapped count —
        # the effective count is normalize_frame_count(...). The
        # adapter surfaces this to the caller (WD-u4rv effective
        # frames); validation passes.
        pass
    # rule 4: flat JSON
    cfg.to_settings_doc()
    # rule 5: line-anchored separators
    if SCRIPT_SEPARATOR not in cfg.script and "---" in cfg.script:
        # inline '---' without the line-anchored form collapses shots
        import re
        if re.search(r"(?m)^(---\s*)$", cfg.script):
            pass    # has own-line separators (valid form)
        else:
            raise JobConfigError(
                "script contains an INLINE '---' separator — wgp "
                "parse_script splits on line-anchored --- only; use "
                f"{SCRIPT_SEPARATOR!r} between shots")
    if not cfg.script or not cfg.script.strip():
        raise JobConfigError("script must be a nonempty string")
    return []
