"""WD-a1d9 — Ref2VA audio_guide data plane (provenance + audio policy
+ QC fields). Spec: docs/specs/s2-ref2va-audio-dataplane.md.

Code + tests only — NO remote GPU/render, no ffmpeg execution (policy
is data, execution is a later slice), no critic model runs (schema
fields only). Zero-model, deterministic.
"""
from __future__ import annotations

import dataclasses
import os
from dataclasses import dataclass, field
from typing import Optional, Tuple

__all__ = [
    "AudioDataPlaneError", "AudioGuideProvenance", "AudioPolicy",
    "Ref2VAAudioQC",
]


class AudioDataPlaneError(ValueError):
    """Typed rejection. Messages name the offending field."""


@dataclass(frozen=True)
class AudioGuideProvenance:
    """Full provenance for one audio_guide asset.

    All paths must exist and be readable at submit time (same
    treatment as image_refs). keeper_window_s = (start, end) with
    end > start and start >= 0. Master DURATION is not checkable
    offline — we validate start >= 0 only (documented; the window is
    clamped at remux time in a later slice).
    """
    source_master: str
    vocal_stem: str
    whisper_map: str
    keeper_window_s: Tuple[float, float]

    def __post_init__(self):
        for name in ("source_master", "vocal_stem", "whisper_map"):
            p = getattr(self, name)
            if not isinstance(p, str) or not p:
                raise AudioDataPlaneError(
                    f"{name}: must be a non-empty path string")
            if not os.path.isfile(p):
                raise AudioDataPlaneError(
                    f"{name}: not readable at submit: {p}")
        w = self.keeper_window_s
        if (not isinstance(w, tuple) or len(w) != 2
                or not all(isinstance(v, (int, float))
                           for v in w)):
            raise AudioDataPlaneError(
                f"keeper_window_s: must be (start, end) numbers, got {w!r}")
        start, end = float(w[0]), float(w[1])
        if start < 0:
            raise AudioDataPlaneError(
                f"keeper_window_s: start must be >= 0, got {start}")
        if end <= start:
            raise AudioDataPlaneError(
                f"keeper_window_s: end ({end}) must be > start ({start})")

    def to_dict(self) -> dict:
        return {
            "source_master": self.source_master,
            "vocal_stem": self.vocal_stem,
            "whisper_map": self.whisper_map,
            "keeper_window_s": [float(self.keeper_window_s[0]),
                                float(self.keeper_window_s[1])],
        }


_REMUX_SOURCES = frozenset(("source_master", "vocal_stem"))


@dataclass(frozen=True)
class AudioPolicy:
    """Explicit H3/Ref2VA audio discard/remux policy (G4 tie-in:
    rendered audio is NEVER trusted — discard default True)."""
    discard_rendered_audio: bool = True
    remux_source: str = "source_master"
    remux_window: Tuple[float, float] = (0.0, 0.0)

    def __post_init__(self):
        if self.remux_source not in _REMUX_SOURCES:
            raise AudioDataPlaneError(
                f"remux_source: must be one of {sorted(_REMUX_SOURCES)}, "
                f"got {self.remux_source!r}")
        w = self.remux_window
        if (not isinstance(w, tuple) or len(w) != 2):
            raise AudioDataPlaneError(
                f"remux_window: must be (start, end), got {w!r}")
        start, end = float(w[0]), float(w[1])
        if start < 0 or end <= start:
            raise AudioDataPlaneError(
                f"remux_window: need start >= 0 and end > start, got "
                f"({start}, {end})")

    def to_dict(self) -> dict:
        return {
            "discard_rendered_audio": self.discard_rendered_audio,
            "remux_source": self.remux_source,
            "remux_window": [float(self.remux_window[0]),
                             float(self.remux_window[1])],
        }


_QC_SCORE_FIELDS = ("mouth_sync", "audio_fidelity",
                    "visual_motion_match", "audio_artifacts")


@dataclass(frozen=True)
class Ref2VAAudioQC:
    """QC schema for audio-bearing Ref2VA jobs.

    Critic fields: critic_model (default "Qwen2-Audio-7B"),
    critic_version. Score fields are 0-10 floats, None = not yet
    judged. notes = free text. to_dict()/from_dict() round-trip.
    """
    critic_model: str = "Qwen2-Audio-7B"
    critic_version: Optional[str] = None
    mouth_sync: Optional[float] = None
    audio_fidelity: Optional[float] = None
    visual_motion_match: Optional[float] = None
    audio_artifacts: Optional[float] = None
    notes: str = ""
    whisper_gates: Optional[dict] = None
    vision_judge: Optional[dict] = None

    def __post_init__(self):
        for name in _QC_SCORE_FIELDS:
            v = getattr(self, name)
            if v is not None and not (0.0 <= float(v) <= 10.0):
                raise AudioDataPlaneError(
                    f"{name}: must be 0-10 or None, got {v}")
        if not isinstance(self.notes, str):
            raise AudioDataPlaneError(
                f"notes: must be a string, got {type(self.notes).__name__}")
        if self.whisper_gates is not None and not isinstance(self.whisper_gates,
                                                             dict):
            raise AudioDataPlaneError(
                f"whisper_gates: must be a dict or None, got "
                f"{type(self.whisper_gates).__name__}")
        if self.vision_judge is not None and not isinstance(self.vision_judge, dict):
            raise AudioDataPlaneError(
                f"vision_judge: must be a dict or None, got "
                f"{type(self.vision_judge).__name__}")

    @classmethod
    def empty(cls) -> "Ref2VAAudioQC":
        return cls()

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Ref2VAAudioQC":
        return cls(**{f: d[f] for f in
                      (f.name for f in dataclasses.fields(cls)) if f in d})
