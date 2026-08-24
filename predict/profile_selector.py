"""ProfileSelector — RenderBrief -> WanGP/H3 render profile (WD-qwb8).

Maps the four brief sections to a structured render decision: model
enum, resolution enum, shot length (HARD FLOOR 96 frames = 4s @24fps,
typed rejection below), seed policy, and a KNOWN WangP profile name.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import FrozenSet

import dspy
from signatures.profile import ProfileSelectorSignature

from predict.prompt_director import RenderBrief

# WanGP profiles actually known at this pin (memory: --profile 3 is the
# H3 keep; extend ONLY with real verified profiles)
KNOWN_WANGP_PROFILES: FrozenSet[str] = frozenset(
    {"profile1", "profile2", "profile3"})

MODELS: FrozenSet[str] = frozenset({"h3", "wan2gp"})
RESOLUTIONS: FrozenSet[str] = frozenset({"720p", "768p"})
SEED_POLICIES: FrozenSet[str] = frozenset(
    {"fixed_per_story", "fixed_per_shot", "derived_from_brief"})

# HARD FLOOR: 96 frames = 4 seconds @ 24fps. Videos are capped, never
# shorter than 4s — shorter requests are a typed rejection.
SHOT_LENGTH_FLOOR_FRAMES = 96
# H3 frame quantization (WD-u4rv, MEASURED on the 3090 pin):
# minimax_h3 renders only 5+17k frames with minimum 107.
H3_FRAMES_MIN = 107
H3_FRAMES_STEP = 17
H3_FRAMES_OFFSET = 5


@dataclass(frozen=True)
class ProfileDecision:
    model: str
    resolution: str
    shot_length_frames: int
    seed_policy: str
    wangp_profile: str

    def __post_init__(self) -> None:
        if self.model not in MODELS:
            raise ValueError(
                f"unknown model {self.model!r}; allowed: {sorted(MODELS)}")
        if self.resolution not in RESOLUTIONS:
            raise ValueError(
                f"unknown resolution {self.resolution!r}; allowed: "
                f"{sorted(RESOLUTIONS)}")
        if (not isinstance(self.shot_length_frames, int)
                or isinstance(self.shot_length_frames, bool)):
            raise ValueError("shot_length_frames must be an int")
        if self.shot_length_frames < SHOT_LENGTH_FLOOR_FRAMES:
            raise ValueError(
                f"shot length {self.shot_length_frames}f is below the "
                f"HARD FLOOR of {SHOT_LENGTH_FLOOR_FRAMES}f "
                "(4s @ 24fps)")
        if self.seed_policy not in SEED_POLICIES:
            raise ValueError(
                f"unknown seed policy {self.seed_policy!r}; allowed: "
                f"{sorted(SEED_POLICIES)}")
        if self.wangp_profile not in KNOWN_WANGP_PROFILES:
            raise ValueError(
                f"unknown WangP profile {self.wangp_profile!r}; known: "
                f"{sorted(KNOWN_WANGP_PROFILES)}")


class ProfileSelector(dspy.ChainOfThought):
    """ChainOfThought module producing validated ProfileDecisions."""

    def __init__(self):
        super().__init__(ProfileSelectorSignature)

    def forward(self, *args, **kwargs):
        out = super().forward(*args, **kwargs)
        decision = _parse_decision(out.decision)
        return dspy.Prediction(decision=decision)

    def from_brief(self, brief: RenderBrief):
        """Convenience: select directly from a RenderBrief instance."""
        return self(subject=brief.subject, motion=brief.motion,
                    camera=brief.camera, style=brief.style)


def _parse_decision(raw: str) -> ProfileDecision:
    try:
        doc = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"LM output is not valid JSON: {raw!r}") from exc
    if not isinstance(doc, dict):
        raise ValueError(f"decision JSON must be an object, got {doc!r}")
    missing = [k for k in ("model", "resolution", "shot_length_frames",
                           "seed_policy", "wangp_profile") if k not in doc]
    if missing:
        raise ValueError(f"decision JSON missing keys: {missing}")
    return ProfileDecision(
        model=str(doc["model"]),
        resolution=str(doc["resolution"]),
        shot_length_frames=int(doc["shot_length_frames"]),
        seed_policy=str(doc["seed_policy"]),
        wangp_profile=str(doc["wangp_profile"]),
    )
