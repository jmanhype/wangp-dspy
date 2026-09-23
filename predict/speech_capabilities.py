"""Typed speech request normalization without inference or host access."""
from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from host.speech_backends import backend_for, model_id

SCHEMA_VERSION = "wangp-dspy.speech-capability-request/v1"
SAMPLE_RATE_HZ = 24_000
CHANNELS = 1
MAX_TEXT_CHARS = 20_000


class SpeechFamily(str, Enum):
    vibevoice = "vibevoice"
    chatterbox = "chatterbox"


class SpeechPreset(str, Enum):
    vibe_7b = "vibe_7b"
    chatterbox_multilingual = "chatterbox_multilingual"


class SpeechMode(str, Enum):
    speech = "speech"
    voice_clone = "voice_clone"


MODEL_PRESETS: Mapping[SpeechFamily, frozenset[SpeechPreset]] = {
    SpeechFamily.vibevoice: frozenset((SpeechPreset.vibe_7b,)),
    SpeechFamily.chatterbox: frozenset((SpeechPreset.chatterbox_multilingual,)),
}


class SpeechCapabilityError(ValueError):
    """A typed, fail-closed speech planning rejection."""

    def __init__(
        self,
        code: str,
        observed: str,
        remediation: str,
        *,
        next_command: str = "wgp voice plan --request <request> --models <models> --json",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation
        self.next_command = next_command
        self.metadata = dict(metadata or {})


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


def _sha256(value: str) -> str:
    normalized = value.lower()
    if re.fullmatch(r"[0-9a-f]{64}", normalized) is None:
        raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
    return normalized


class SpeechModelRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    family: SpeechFamily
    preset: SpeechPreset
    sha256: str = Field(min_length=64, max_length=64)
    license: str = Field(min_length=1)
    license_accepted: bool
    source: str = Field(min_length=1)
    usage_constraint: str = Field(min_length=1)
    vram_profile: str = Field(min_length=1)

    @field_validator("sha256")
    @classmethod
    def _hash(cls, value: str) -> str:
        return _sha256(value)

    @model_validator(mode="after")
    def _preset_allowed(self) -> "SpeechModelRef":
        if self.preset not in MODEL_PRESETS[self.family]:
            raise ValueError(f"preset {self.preset.value!r} is invalid for {self.family.value}")
        return self


class VoiceReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    role: str = Field(pattern=r"^(primary|secondary)$")
    duration_s: float = Field(ge=2.0, le=30.0)
    source: str = Field(min_length=1)
    license: str = Field(min_length=1)
    consent_ref: str = Field(min_length=1)

    @field_validator("path")
    @classmethod
    def _wav(cls, value: str) -> str:
        if Path(value).suffix.lower() != ".wav":
            raise ValueError("voice reference must be a WAV path")
        return value

    @field_validator("sha256")
    @classmethod
    def _hash(cls, value: str) -> str:
        return _sha256(value)


class AppearanceBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    role: str = "character_appearance"

    @field_validator("path")
    @classmethod
    def _image(cls, value: str) -> str:
        if Path(value).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise ValueError("appearance must be a PNG, JPEG, or WebP path")
        return value

    @field_validator("sha256")
    @classmethod
    def _hash(cls, value: str) -> str:
        return _sha256(value)


class CharacterBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    character_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9 _.-]*$")
    speaker_label: str = Field(min_length=1, max_length=80)
    appearance: AppearanceBinding | None = None
    voice_binding_id: str = Field(min_length=8, max_length=120)


class SegmentPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_segment_chars: int = Field(gt=0)
    max_segment_duration_s: float = Field(gt=0.0)
    silence_s: float = Field(ge=0.0, le=2.0)
    split_on_sentence: bool = True


class OutputFormat(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sample_rate_hz: int = SAMPLE_RATE_HZ
    channels: int = CHANNELS

    @model_validator(mode="after")
    def _target(self) -> "OutputFormat":
        if (self.sample_rate_hz, self.channels) != (SAMPLE_RATE_HZ, CHANNELS):
            raise ValueError(f"speech target must be {SAMPLE_RATE_HZ} Hz / {CHANNELS} channel")
        return self


class SpeechCapabilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SCHEMA_VERSION
    model: SpeechModelRef
    mode: SpeechMode
    text: str = Field(min_length=1, max_length=MAX_TEXT_CHARS)
    language: str = Field(pattern=r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$")
    style: str = Field(min_length=1, max_length=500)
    references: tuple[VoiceReference, ...] = Field(default=(), max_length=2)
    character: CharacterBinding | None = None
    segment_policy: SegmentPolicy
    output_format: OutputFormat = OutputFormat()
    output_path_planned: str = Field(min_length=1)
    recipe_seed: int = Field(ge=0, le=2_147_483_647)

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version {value!r}; expected {SCHEMA_VERSION}")
        return value

    @model_validator(mode="after")
    def _shape(self) -> "SpeechCapabilityRequest":
        adapter = backend_for(self.model.family)
        adapter.validate(self.model, self.mode, failure=SpeechCapabilityError)
        if self.mode is SpeechMode.speech and self.references:
            raise ValueError("speech mode cannot carry cloning references")
        if self.mode is SpeechMode.voice_clone and not 1 <= len(self.references) <= 2:
            raise ValueError("voice_clone requires exactly one or two ordered references")
        if len({reference.role for reference in self.references}) != len(self.references):
            raise ValueError("voice reference roles must be primary then secondary without duplication")
        if self.references and self.references[0].role != "primary":
            raise ValueError("the first voice reference must be primary")
        if len(self.references) == 2 and self.references[1].role != "secondary":
            raise ValueError("the second voice reference must be secondary")
        if self.character is not None and self.character.appearance is None:
            raise ValueError("a character binding requires appearance/voice binding fields")
        adapter.validate_shape(self, failure=SpeechCapabilityError)
        return self


def _entries(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("models"), list):
        payload = payload["models"]
    if not isinstance(payload, list) or not payload or not all(isinstance(item, dict) for item in payload):
        raise SpeechCapabilityError(
            "MODEL_MANIFEST_INVALID",
            "speech model manifest is absent or contains no object entries",
            "Supply a nonempty models array with immutable provenance for each engine.",
        )
    return payload


def load_speech_model_manifest(path: str | Path) -> dict[str, SpeechModelRef]:
    source = Path(path).expanduser()
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SpeechCapabilityError(
            "MODEL_MANIFEST_MISSING",
            f"model manifest does not exist: {source}",
            "Create an operator-supplied manifest; Wangp does not download models.",
            metadata={"path": str(source)},
        ) from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SpeechCapabilityError(
            "MODEL_MANIFEST_INVALID",
            f"cannot read model manifest {source}: {exc}",
            "Fix the JSON manifest, then rerun the deterministic speech plan.",
            metadata={"path": str(source)},
        ) from exc
    models: dict[str, SpeechModelRef] = {}
    for index, item in enumerate(_entries(payload), start=1):
        try:
            family = SpeechFamily(item.get("family"))
            preset = SpeechPreset(item.get("preset"))
            key = model_id(family, preset)
            digest = item.get("sha256")
            if not isinstance(digest, str) or re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None:
                raise SpeechCapabilityError(
                    "MODEL_HASH_MISSING",
                    f"model manifest entry {key} has no valid sha256",
                    "Record the operator-provided model hash; Wangp will not download a model.",
                    metadata={"model": key},
                )
            model = SpeechModelRef.model_validate({**item, "sha256": digest})
            backend_for(family).validate(model, SpeechMode.speech, failure=SpeechCapabilityError)
        except SpeechCapabilityError:
            raise
        except (ValueError, ValidationError) as exc:
            raise SpeechCapabilityError(
                "SPEECH_BACKEND_INCOMPLETE",
                f"model manifest entry {index} is incomplete: {exc}",
                "Record family, preset, hash, license/acceptance, source, usage constraint, and VRAM.",
                metadata={"entry": index},
            ) from exc
        if key in models:
            raise SpeechCapabilityError(
                "MODEL_MANIFEST_INVALID",
                f"model manifest contains duplicate {key}",
                "Keep exactly one immutable entry per family/preset.",
            )
        models[key] = model
    return models


def attach_manifest_model(
    payload: Mapping[str, Any], manifest: Mapping[str, SpeechModelRef]
) -> SpeechCapabilityRequest:
    document = dict(payload)
    requested = document.get("model")
    if not isinstance(requested, dict):
        raise SpeechCapabilityError(
            "SPEECH_REQUEST_INVALID",
            "request is missing the model object",
            "Supply model.family and model.preset; the manifest supplies immutable provenance.",
        )
    try:
        key = model_id(SpeechFamily(requested.get("family")), SpeechPreset(requested.get("preset")))
    except ValueError as exc:
        raise SpeechCapabilityError(
            "SPEECH_REQUEST_INVALID",
            f"unknown speech family/preset {requested.get('family')!r}/{requested.get('preset')!r}",
            "Use vibevoice/vibe_7b or chatterbox/chatterbox_multilingual.",
        ) from exc
    model = manifest.get(key)
    if model is None:
        raise SpeechCapabilityError(
            "MODEL_MANIFEST_MISSING",
            f"manifest has no entry for {key}",
            "Add immutable model provenance; Wangp will not download the model.",
        )
    document["model"] = model.model_dump(mode="json")
    try:
        return SpeechCapabilityRequest.model_validate(document)
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        lowered = details.lower()
        if "does not plan" in lowered or "reference counts" in lowered:
            code = "SPEECH_ENGINE_MODE_UNSUPPORTED"
        elif "reference" in lowered:
            code = "SPEECH_REFERENCE_COUNT_INVALID"
        elif "duration_s" in lowered or "segment" in lowered:
            code = "SPEECH_SEGMENT_INVALID"
        elif "appearance" in lowered or "character" in lowered:
            code = "SPEECH_CHARACTER_BINDING_INVALID"
        elif (
            "sample_rate" in lowered
            or "channels" in lowered
            or "output_format" in lowered
            or "speech target" in lowered
        ):
            code = "SPEECH_FORMAT_UNSUPPORTED"
        else:
            code = "SPEECH_REQUEST_INVALID"
        raise SpeechCapabilityError(
            code,
            details,
            "Fix the typed request fields, then rerun the deterministic no-GPU speech plan.",
        ) from exc


def backend_settings(request: SpeechCapabilityRequest) -> dict[str, Any]:
    adapter = backend_for(request.model.family)
    adapter.validate(request.model, request.mode, failure=SpeechCapabilityError)
    return {
        "normalization_version": "wangp-dspy.speech-backend-settings/v1",
        "backend": adapter.backend_id,
        "model_type": adapter.model_type,
        "model_sha256": request.model.sha256,
        "preset": request.model.preset.value,
        "mode": request.mode.value,
        "text_sha256": hashlib.sha256(request.text.encode("utf-8")).hexdigest(),
        "language": request.language,
        "style": request.style,
        "reference_hashes": [reference.sha256 for reference in request.references],
        "segment_policy": request.segment_policy.model_dump(mode="json"),
        "sample_rate_hz": request.output_format.sample_rate_hz,
        "channels": request.output_format.channels,
        "recipe_seed": request.recipe_seed,
        "host_contact": False,
    }


def request_digest(request: SpeechCapabilityRequest) -> str:
    return canonical_sha256(request.model_dump(mode="json"))


def capability_matrix() -> list[dict[str, str]]:
    return [
        {
            "family": family.value,
            "mode": mode.value,
            "status": "planned",
            "supported_for_planning": str(backend_for(family).supports(mode)).lower(),
            "generation_evidence": "none",
        }
        for family in SpeechFamily
        for mode in SpeechMode
    ]


__all__ = [
    "CHANNELS", "MAX_TEXT_CHARS", "MODEL_PRESETS", "SAMPLE_RATE_HZ", "SCHEMA_VERSION",
    "AppearanceBinding", "CharacterBinding", "OutputFormat", "SegmentPolicy",
    "SpeechCapabilityError", "SpeechCapabilityRequest", "SpeechFamily", "SpeechMode",
    "SpeechModelRef", "SpeechPreset", "VoiceReference", "attach_manifest_model",
    "backend_for", "backend_settings", "capability_matrix", "canonical_json",
    "canonical_sha256", "file_sha256", "load_speech_model_manifest", "model_id",
    "request_digest",
]
