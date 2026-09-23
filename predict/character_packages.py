"""Typed portable character packages for cross-mode continuity planning."""
from __future__ import annotations

import re
import hashlib
import json
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


PACKAGE_SCHEMA_VERSION = "wangp-dspy.character-package/v1"
CONTINUITY_SCHEMA_VERSION = "wangp-dspy.character-continuity-request/v1"
PACKAGE_SUFFIX = ".wgpcharacter"
VOICE_MEMBER = "voice/character.wgpvoice"
MAX_PACKAGE_MEMBERS = 12
IMAGE_OPERATIONS = frozenset({"generate", "edit", "upscale", "outpaint", "identity_edit"})
VIDEO_OPERATIONS = frozenset({"create", "extend", "blend", "retake", "edit", "outpaint", "repaint", "recast", "upscale"})
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

    @model_validator(mode="after")
    def _portable_shape(self) -> "CharacterDefinition":
        roles = [appearance.role for appearance in self.appearance]
        if len(roles) != len(set(roles)):
            raise ValueError("appearance roles must be unique")
        if AppearanceRole.native not in roles:
            raise ValueError("portable character requires a native appearance")
        if self.voice is None:
            raise ValueError("portable character requires a saved .wgpvoice binding")
        metrics = {constraint.metric for constraint in self.continuity.constraints}
        required = {IdentityMetric.face_embedding_cosine, IdentityMetric.cross_mode_binding}
        if not required.issubset(metrics):
            raise ValueError("continuity requires face_embedding_cosine and cross_mode_binding constraints")
        return self


class CharacterPackageManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = PACKAGE_SCHEMA_VERSION
    character_id: str = Field(min_length=1, max_length=80, pattern=_ID_RE.pattern)
    speaker_label: str = Field(min_length=1, max_length=80)
    version: int = Field(ge=1, le=999)
    description: str = Field(min_length=1, max_length=2000)
    identity_sha256: str = Field(min_length=64, max_length=64)
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

    @field_validator("identity_sha256")
    @classmethod
    def _identity_hash(cls, value: str) -> str:
        return _hash(value, label="identity_sha256")

    @model_validator(mode="after")
    def _portable_shape(self) -> "CharacterPackageManifest":
        roles = [appearance.role for appearance in self.appearance]
        if len(roles) != len(set(roles)) or AppearanceRole.native not in roles:
            raise ValueError("package appearance requires unique roles including native")
        if self.voice is None:
            raise ValueError("package requires a saved .wgpvoice binding")
        return self


class CharacterReference(BaseModel):
    """The explicit appearance-and-voice binding carried by image/video plans."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    package_path: str = Field(min_length=1)
    package_sha256: str = Field(min_length=64, max_length=64)
    character_id: str = Field(min_length=1, max_length=80, pattern=_ID_RE.pattern)
    speaker_label: str = Field(min_length=1, max_length=80)
    appearance_member: str = Field(min_length=1)
    appearance_sha256: str = Field(min_length=64, max_length=64)
    voice_member: str = VOICE_MEMBER
    voice_binding_id: str = Field(min_length=8, max_length=120)
    voice_sha256: str = Field(min_length=64, max_length=64)
    modes: tuple[ContinuityMode, ...] = Field(min_length=1)

    @field_validator("package_path")
    @classmethod
    def _package_suffix(cls, value: str) -> str:
        if Path(value).suffix.lower() != PACKAGE_SUFFIX:
            raise ValueError(f"package_path must end in {PACKAGE_SUFFIX}")
        return value

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


class CharacterContinuityRequest(BaseModel):
    """An image or video plan explicitly bound to one portable character."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = CONTINUITY_SCHEMA_VERSION
    mode: ContinuityMode
    operation: str = Field(min_length=1, max_length=40)
    prompt: str = Field(min_length=1, max_length=4000)
    character: CharacterReference
    recipe_seed: int = Field(ge=0, le=2_147_483_647)

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != CONTINUITY_SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version {value!r}; expected {CONTINUETY_SCHEMA_VERSION}")
        return value

    @model_validator(mode="after")
    def _mode_shape(self) -> "CharacterContinuityRequest":
        allowed = IMAGE_OPERATIONS if self.mode is ContinuityMode.image else VIDEO_OPERATIONS
        if self.operation not in allowed:
            raise ValueError(f"{self.mode.value} does not support operation {self.operation!r}")
        if self.mode not in self.character.modes:
            raise ValueError("character reference modes must include the request mode")
        return self


def canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def identity_digest(character_id: str, speaker_label: str, voice_binding_id: str) -> tuple[str, str]:
    canonical = {
        "character_id": character_id,
        "speaker_label": speaker_label,
        "voice_binding_id": voice_binding_id,
    }
    return canonical_json(canonical), canonical_sha256(canonical)


__all__ = [
    "PACKAGE_SCHEMA_VERSION",
    "PACKAGE_SUFFIX",
    "VOICE_MEMBER",
    "AppearanceInput",
    "AppearanceRecord",
    "AppearanceRole",
    "CONTINUITY_SCHEMA_VERSION",
    "CharacterContinuityRequest",
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
    "canonical_json",
    "canonical_sha256",
    "identity_digest",
]
