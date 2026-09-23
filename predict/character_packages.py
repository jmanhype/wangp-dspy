"""Typed portable character packages for cross-mode continuity planning."""
from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator


PACKAGE_SCHEMA_VERSION = "wangp-dspy.character-package/v1"
PACKAGE_SUFFIX = ".wgpcharacter"
VOICE_MEMBER = "voice/character.wgpvoice"
MAX_PACKAGE_MEMBERS = 12
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]*$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


class CharacterPackageError(ValueError):
    """A typed, fail-closed portable-character rejection."""

    def __init__(
        self,
        code: str,
        observed: str,
        remediation: str,
        *,
        next_command: str = "wgp character show --package <character.wgpcharacter> --json",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation
        self.next_command = next_command
        self.metadata = dict(metadata or {})


class AppearanceRole(str, Enum):
    native = "native"
    portrait = "portrait"
    action = "action"
    wardrobe = "wardrobe"


class ContinuityMode(str, Enum):
    image = "image"
    video = "video"


class IdentityMetric(str, Enum):
    face_embedding_cosine = "face_embedding_cosine"
    cross_mode_binding = "cross_mode_binding"


def _hash(value: str, *, label: str = "sha256") -> str:
    normalized = value.lower()
    if _HASH_RE.fullmatch(normalized) is None:
        raise ValueError(f"{label} must be 64 lowercase hexadecimal characters")
    return normalized


class AppearanceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    role: AppearanceRole
    width: int = Field(gt=0, le=8192)
    height: int = Field(gt=0, le=8192)
    source_path: str = Field(min_length=1)
    license: str = Field(min_length=1)
    consent_ref: str = Field(min_length=1)

    @field_validator("sha256")
    @classmethod
    def _normalize_hash(cls, value: str) -> str:
        return _hash(value)


class AppearanceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    member: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    role: AppearanceRole
    width: int = Field(gt=0, le=8192)
    height: int = Field(gt=0, le=8192)
    source_path: str = Field(min_length=1)
    license: str = Field(min_length=1)
    consent_ref: str = Field(min_length=1)

    @field_validator("sha256")
    @classmethod
    def _normalize_hash(cls, value: str) -> str:
        return _hash(value)


class SavedVoiceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    voice_binding_id: str = Field(min_length=8, max_length=120)

    @field_validator("path")
    @classmethod
    def _voice_package(cls, value: str) -> str:
        if Path(value).suffix.lower() != ".wgpvoice":
            raise ValueError("saved voice must be a .wgpvoice package path")
        return value


class VoiceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    member: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    character_id: str = Field(min_length=1, max_length=80, pattern=_ID_RE.pattern)
    speaker_label: str = Field(min_length=1, max_length=80)
    voice_binding_id: str = Field(min_length=8, max_length=120)
    engine_compatibility: tuple[str, ...] = Field(min_length=1)
    source_path: str = Field(min_length=1)

    @field_validator("sha256")
    @classmethod
    def _normalize_hash(cls, value: str) -> str:
        return _hash(value)


class ContinuityConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metric: IdentityMetric
    threshold: float = Field(gt=0.0, le=1.0)


class ContinuityContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    modes: tuple[ContinuityMode, ...] = Field(min_length=1)
    constraints: tuple[ContinuityConstraint, ...] = Field(min_length=1)

    @field_validator("modes")
    @classmethod
    def _unique_modes(cls, value: tuple[ContinuityMode, ...]) -> tuple[ContinuityMode, ...]:
        if len(set(value)) != len(value):
            raise ValueError("continuity modes must be unique")
        return value


class CharacterDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = PACKAGE_SCHEMA_VERSION
    character_id: str = Field(min_length=1, max_length=80, pattern=_ID_RE.pattern)
    speaker_label: str = Field(min_length=1, max_length=80)
    version: int = Field(ge=1, le=999)
    description: str = Field(min_length=1, max_length=2000)
    appearance: tuple[AppearanceInput, ...] = Field(min_length=1)
    voice: SavedVoiceInput | None = None
    continuity: ContinuityContract
    recipe_seed: int = Field(ge=0, le=2_147_483_647)

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != PACKAGE_SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version {value!r}; expected {PACKAGE_SCHEMA_VERSION}")
        return value

    @field_validator("character_id")
    @classmethod
    def _identifier(cls, value: str) -> str:
        if _ID_RE.fullmatch(value) is None:
            raise ValueError("character_id must begin with an alphanumeric character")
        return value


class CharacterPackageManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = PACKAGE_SCHEMA_VERSION
    character_id: str = Field(min_length=1, max_length=80, pattern=_ID_RE.pattern)
    speaker_label: str = Field(min_length=1, max_length=80)
    version: int = Field(ge=1, le=999)
    description: str = Field(min_length=1, max_length=2000)
    appearance: tuple[AppearanceRecord, ...] = Field(min_length=1)
    voice: VoiceRecord | None = None
    continuity: ContinuityContract
    recipe_seed: int = Field(ge=0, le=2_147_483_647)
    generation_claimed: bool = False
    host_contact: bool = False
    execution_status: str = "planned"

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != PACKAGE_SCHEMA_VERSION:
            raise ValueError(f"unsupported character package schema {value!r}")
        return value


class CharacterReference(BaseModel):
    """The explicit appearance-and-voice binding carried by image/video plans."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    package_path: str = Field(min_length=1)
    package_sha256: str = Field(min_length=64, max_length=64)
    character_id: str = Field(min_length=1, max_length=80, pattern=_ID_RE.pattern)
    appearance_member: str = Field(min_length=1)
    appearance_sha256: str = Field(min_length=64, max_length=64)
    voice_member: str = VOICE_MEMBER
    voice_binding_id: str = Field(min_length=8, max_length=120)
    voice_sha256: str = Field(min_length=64, max_length=64)
    modes: tuple[ContinuityMode, ...] = Field(min_length=1)

    @field_validator("package_sha256", "appearance_sha256", "voice_sha256")
    @classmethod
    def _normalize_hash(cls, value: str, info) -> str:
        return _hash(value, label=info.field_name)

    @field_validator("modes")
    @classmethod
    def _unique_modes(cls, value: tuple[ContinuityMode, ...]) -> tuple[ContinuityMode, ...]:
        if len(set(value)) != len(value):
            raise ValueError("character reference modes must be unique")
        return value


__all__ = [
    "PACKAGE_SCHEMA_VERSION",
    "PACKAGE_SUFFIX",
    "VOICE_MEMBER",
    "AppearanceInput",
    "AppearanceRecord",
    "AppearanceRole",
    "CharacterDefinition",
    "CharacterPackageError",
    "CharacterPackageManifest",
    "CharacterReference",
    "ContinuityConstraint",
    "ContinuityContract",
    "ContinuityMode",
    "IdentityMetric",
    "SavedVoiceInput",
    "VoiceRecord",
]
