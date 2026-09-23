"""Typed request models for governed no-GPU director composition."""
from __future__ import annotations

import hashlib
import json
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


REQUEST_SCHEMA = "wangp-dspy.director-request/v1"
ENHANCEMENT_SCHEMA = "wangp-dspy.director-enhancement-request/v1"
MAX_PROGRAMME_S = 60 * 60


class DirectorError(ValueError):
    """A typed, fail-closed director planning rejection."""

    def __init__(
        self,
        code: str,
        observed: str,
        remediation: str,
        *,
        next_command: str = "wgp director plan --request <request> --json",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation
        self.next_command = next_command
        self.metadata = dict(metadata or {})


class DirectorMode(str, Enum):
    prompt = "prompt"
    audio = "audio"
    music_video = "music_video"
    screenplay = "screenplay"


class ReviewMode(str, Enum):
    auto = "auto"
    manual = "manual"


class AudioBeat(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    time_s: float = Field(ge=0.0)
    confidence: float = Field(gt=0.0, le=1.0)
    measurement: str = Field(min_length=1)


class AudioEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    duration_s: float = Field(gt=0.0, le=MAX_PROGRAMME_S)
    beats: tuple[AudioBeat, ...] = Field(default_factory=tuple)

    @field_validator("sha256")
    @classmethod
    def _lower_hex(cls, value: str) -> str:
        normalized = value.lower()
        if any(character not in "0123456789abcdef" for character in normalized):
            raise ValueError("audio sha256 must be 64 lowercase hexadecimal characters")
        return normalized


class CharacterState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    appearance: str = Field(min_length=1)
    voice: str = Field(min_length=1)


class ScreenplayScene(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scene_index: int = Field(ge=1)
    slugline: str = Field(min_length=1)
    duration_s: float = Field(gt=0.0, le=MAX_PROGRAMME_S)
    characters: tuple[str, ...] = Field(min_length=1)
    location: str = Field(min_length=1)
    states: tuple[CharacterState, ...] = Field(min_length=1)
    action: str = Field(min_length=1)

    @model_validator(mode="after")
    def _states_match_characters(self) -> "ScreenplayScene":
        state_names = {state.name for state in self.states}
        if state_names != set(self.characters):
            raise ValueError("each scene character must have exactly one explicit state")
        return self


class Screenplay(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str = Field(min_length=1)
    characters: tuple[CharacterState, ...] = Field(min_length=1)
    scenes: tuple[ScreenplayScene, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _ordered_scenes(self) -> "Screenplay":
        indices = [scene.scene_index for scene in self.scenes]
        if indices != list(range(1, len(indices) + 1)):
            raise ValueError("scene_index values must be consecutive from 1")
        roster = {character.name for character in self.characters}
        for scene in self.scenes:
            unknown = set(scene.characters) - roster
            if unknown:
                raise ValueError(f"scene {scene.scene_index} references unknown characters {sorted(unknown)}")
        return self


class PacingControl(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    strategy: str = Field(min_length=1)
    target_duration_s: float = Field(gt=0.0, le=MAX_PROGRAMME_S)
    clip_count: int | None = Field(default=None, ge=1, le=240)
    exact_start_s: float | None = Field(default=None, ge=0.0)
    exact_end_s: float | None = Field(default=None, gt=0.0)
    max_clip_s: float = Field(default=60.0, gt=0.0, le=MAX_PROGRAMME_S)

    @model_validator(mode="after")
    def _control_shape(self) -> "PacingControl":
        selected = sum(value is not None for value in (self.clip_count, self.exact_start_s, self.exact_end_s))
        if self.strategy == "even" and selected not in (0, 1):
            raise ValueError("even pacing may set clip_count but not timecode fields")
        if self.strategy == "window_count" and self.clip_count is None:
            raise ValueError("window_count pacing requires clip_count")
        if self.strategy == "window_count" and selected != 1:
            raise ValueError("window_count pacing accepts clip_count only")
        if self.strategy == "exact_timecode":
            if self.exact_start_s is None or self.exact_end_s is None or self.clip_count is not None:
                raise ValueError("exact_timecode pacing requires exact_start_s and exact_end_s only")
            if self.exact_end_s <= self.exact_start_s:
                raise ValueError("exact_timecode end must be after start")
        if self.strategy == "beat" and selected != 0:
            raise ValueError("beat pacing derives windows from measured beats and accepts no manual control")
        return self


class ReviewControl(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: ReviewMode
    manual_checkpoint_required: bool = False
    reviewer: str = Field(min_length=1)


class QueueEnhancementIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent: str = Field(min_length=1)
    allowed_fields: tuple[str, ...] = Field(min_length=1)
    reason: str = Field(min_length=1)


class DirectorRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str
    mode: DirectorMode
    title: str = Field(min_length=1)
    prompt: str | None = None
    audio: AudioEvidence | None = None
    screenplay: Screenplay | None = None
    pacing: PacingControl
    review: ReviewControl
    recipe_seed: int = Field(ge=0, le=2_147_483_647)
    queue_enhancement: QueueEnhancementIntent | None = None

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != REQUEST_SCHEMA:
            raise ValueError(f"schema_version must be {REQUEST_SCHEMA!r}")
        return value

    @model_validator(mode="after")
    def _one_source(self) -> "DirectorRequest":
        supplied = {
            DirectorMode.prompt: self.prompt is not None,
            DirectorMode.audio: self.audio is not None,
            DirectorMode.music_video: self.audio is not None,
            DirectorMode.screenplay: self.screenplay is not None,
        }
        expected = supplied[self.mode]
        extras = [name for name, value in (
            ("prompt", self.prompt), ("audio", self.audio), ("screenplay", self.screenplay)
        ) if value is not None]
        if not expected or len(extras) != 1:
            raise ValueError(f"mode {self.mode.value} requires exactly one matching source field")
        return self


class EnhancementChanges(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    prompt: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _nonempty(self) -> "EnhancementChanges":
        if self.prompt is None:
            raise ValueError("enhancement must change at least one allowed field")
        return self


class DirectorEnhancementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str
    source_db: str = Field(min_length=1)
    changes: EnhancementChanges
    provenance_reason: str = Field(min_length=1)

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != ENHANCEMENT_SCHEMA:
            raise ValueError(f"schema_version must be {ENHANCEMENT_SCHEMA!r}")
        return value


def canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = [
    "AudioBeat", "AudioEvidence", "CharacterState", "DirectorEnhancementRequest",
    "DirectorError", "DirectorMode", "DirectorRequest", "EnhancementChanges",
    "ENHANCEMENT_SCHEMA", "MAX_PROGRAMME_S", "PacingControl",
    "QueueEnhancementIntent", "REQUEST_SCHEMA", "ReviewControl", "ReviewMode",
    "Screenplay", "ScreenplayScene", "canonical_json", "canonical_sha256",
    "file_sha256",
]
