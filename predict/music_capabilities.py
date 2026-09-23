"""Typed music planning without inference, host access, or audio claims."""
from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from host.music_backends import backend_for, model_id

SCHEMA_VERSION = "wangp-dspy.music-capability-request/v1"
SAMPLE_RATE_HZ = 48_000
CHANNELS = 2
MAX_DURATION_S = 3_600


class MusicFamily(str, Enum):
    ace_step = "ace_step"
    stable_audio = "stable_audio"


class MusicPreset(str, Enum):
    instrumental = "instrumental"
    song = "song"


class MusicMode(str, Enum):
    generate = "generate"
    style_adaptation = "style_adaptation"


MusicOperation = MusicMode
MODEL_PRESETS: Mapping[MusicFamily, frozenset[MusicPreset]] = {
    family: frozenset((MusicPreset.instrumental, MusicPreset.song))
    for family in MusicFamily
}


class MusicCapabilityError(ValueError):
    """A typed, fail-closed music planning rejection."""

    def __init__(
        self,
        code: str,
        observed: str,
        remediation: str,
        *,
        next_command: str = "wgp music plan --request <request> --models <models> --json",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation
        self.next_command = next_command
        self.metadata = dict(metadata or {})


class MusicModelRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    family: MusicFamily
    preset: MusicPreset
    sha256: str = Field(min_length=64, max_length=64)
    license: str = Field(min_length=1)
    license_accepted: bool
    source: str = Field(min_length=1)
    usage_constraint: str = Field(min_length=1)
    vram_profile: str = Field(min_length=1)

    @field_validator("sha256")
    @classmethod
    def _lower_hash(cls, value: str) -> str:
        normalized = value.lower()
        if re.fullmatch(r"[0-9a-f]{64}", normalized) is None:
            raise ValueError("model sha256 must be 64 lowercase hexadecimal characters")
        return normalized

    @model_validator(mode="after")
    def _preset_allowed(self) -> "MusicModelRef":
        if self.preset not in MODEL_PRESETS[self.family]:
            raise ValueError(f"preset {self.preset.value!r} is invalid for {self.family.value}")
        return self


class OutputFormat(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sample_rate_hz: int = SAMPLE_RATE_HZ
    channels: int = CHANNELS

    @model_validator(mode="after")
    def _governed_target(self) -> "OutputFormat":
        if (self.sample_rate_hz, self.channels) != (SAMPLE_RATE_HZ, CHANNELS):
            raise ValueError(
                f"music output must be {SAMPLE_RATE_HZ} Hz / {CHANNELS} channels; "
                f"got {self.sample_rate_hz} Hz / {self.channels}"
            )
        return self


class MusicSection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9][A-Za-z0-9 _-]*$")
    duration_s: float = Field(gt=0.0, le=600.0)
    melody_abc: str = Field(min_length=7)
    chords: Sequence[str] = Field(min_length=1)


class AudioEvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)


class StyleReference(AudioEvidenceRef):
    source: str = Field(min_length=1)
    rights: str = Field(min_length=1)


class AudibleComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: str = "audible_ab"
    before: AudioEvidenceRef
    after_path_planned: str = Field(min_length=1)

    @model_validator(mode="after")
    def _mode(self) -> "AudibleComparison":
        if self.mode != "audible_ab":
            raise ValueError("comparison mode must be audible_ab")
        return self


class StyleAdaptation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    references: Sequence[StyleReference] = Field(min_length=1)
    comparison: AudibleComparison
    command_planned: str = Field(min_length=1)


class MusicCapabilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SCHEMA_VERSION
    model: MusicModelRef
    mode: MusicMode
    title: str = Field(min_length=1, max_length=160)
    style: str = Field(min_length=1, max_length=500)
    lyrics: str | None = None
    tempo_bpm: int = Field(ge=20, le=300)
    meter: str = Field(pattern=r"^[2-9]/[248]$")
    key: str = Field(pattern=r"^[A-G][b#]?m?$")
    sections: Sequence[MusicSection] = Field(min_length=1)
    duration_s: float = Field(gt=0.0, le=MAX_DURATION_S)
    output_format: OutputFormat = OutputFormat()
    style_adaptation: StyleAdaptation | None = None
    recipe_seed: int = Field(ge=0, le=2_147_483_647)

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version {value!r}; expected {SCHEMA_VERSION}")
        return value

    @model_validator(mode="after")
    def _shape(self) -> "MusicCapabilityRequest":
        names = [section.name.lower() for section in self.sections]
        if len(names) != len(set(names)):
            raise ValueError("section names must be unique")
        if abs(sum(item.duration_s for item in self.sections) - self.duration_s) > 1e-9:
            raise ValueError("section durations must sum exactly to duration_s")
        if self.model.preset is MusicPreset.instrumental and self.lyrics:
            raise ValueError("instrumental preset cannot carry lyrics")
        if self.model.preset is MusicPreset.song and not (self.lyrics or "").strip():
            raise ValueError("song preset requires lyrics")
        if self.mode is MusicMode.style_adaptation and self.style_adaptation is None:
            raise ValueError("style_adaptation mode requires style_adaptation inputs")
        if self.mode is MusicMode.generate and self.style_adaptation is not None:
            raise ValueError("generate mode cannot carry style_adaptation inputs")
        backend_for(self.model.family).validate(
            self.model, self.mode, failure=MusicCapabilityError
        )
        return self


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


def _entries(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("models"), list):
        payload = payload["models"]
    if not isinstance(payload, list) or not payload or not all(isinstance(item, dict) for item in payload):
        raise MusicCapabilityError(
            "MODEL_MANIFEST_INVALID",
            "music model manifest is absent or contains no object entries",
            "Supply a nonempty models array with immutable provenance for each model.",
        )
    return payload


def load_music_model_manifest(path: str | Path) -> dict[str, MusicModelRef]:
    source = Path(path).expanduser()
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MusicCapabilityError(
            "MODEL_MANIFEST_MISSING", f"model manifest does not exist: {source}",
            "Create an operator-supplied manifest; Wangp does not download models.",
            metadata={"path": str(source)},
        ) from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MusicCapabilityError(
            "MODEL_MANIFEST_INVALID", f"cannot read model manifest {source}: {exc}",
            "Fix the JSON manifest, then rerun the no-GPU music plan.", metadata={"path": str(source)},
        ) from exc
    models: dict[str, MusicModelRef] = {}
    for index, item in enumerate(_entries(payload), start=1):
        try:
            family, preset = MusicFamily(item.get("family")), MusicPreset(item.get("preset"))
            key = model_id(family, preset)
            digest = item.get("sha256")
            if not isinstance(digest, str) or re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None:
                raise MusicCapabilityError(
                    "MODEL_HASH_MISSING", f"model manifest entry {key} has no valid sha256",
                    "Record the operator-provided model hash; Wangp will not download a model.",
                    metadata={"model": key},
                )
            model = MusicModelRef.model_validate({**item, "sha256": digest})
            backend_for(family).validate(model, MusicMode.generate, failure=MusicCapabilityError)
        except MusicCapabilityError:
            raise
        except (ValueError, ValidationError) as exc:
            raise MusicCapabilityError(
                "MUSIC_BACKEND_INCOMPLETE", f"model manifest entry {index} is incomplete: {exc}",
                "Record family, preset, hash, license/acceptance, source, usage constraint, and VRAM.",
                metadata={"entry": index},
            ) from exc
        if key in models:
            raise MusicCapabilityError(
                "MODEL_MANIFEST_INVALID", f"model manifest contains duplicate {key}",
                "Keep exactly one immutable entry per family/preset.",
            )
        models[key] = model
    return models


def attach_manifest_model(
    payload: Mapping[str, Any], manifest: Mapping[str, MusicModelRef]
) -> MusicCapabilityRequest:
    document = dict(payload)
    requested = document.get("model")
    if not isinstance(requested, dict):
        raise MusicCapabilityError(
            "MUSIC_REQUEST_INVALID", "request is missing the model object",
            "Supply model.family and model.preset; the manifest supplies provenance.",
        )
    try:
        key = model_id(MusicFamily(requested.get("family")), MusicPreset(requested.get("preset")))
    except ValueError as exc:
        raise MusicCapabilityError(
            "MUSIC_REQUEST_INVALID",
            f"unknown music family/preset {requested.get('family')!r}/{requested.get('preset')!r}",
            "Use ace_step or stable_audio with instrumental or song.",
        ) from exc
    model = manifest.get(key)
    if model is None:
        raise MusicCapabilityError(
            "MODEL_MANIFEST_MISSING", f"manifest has no entry for {key}",
            "Add immutable model provenance; Wangp will not download the model.",
        )
    document["model"] = model.model_dump(mode="json")
    try:
        return MusicCapabilityRequest.model_validate(document)
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        lowered = details.lower()
        if "does not plan" in lowered:
            code = "MUSIC_OPERATION_UNSUPPORTED"
        elif "sample_rate" in lowered or "channels" in lowered:
            code = "MUSIC_FORMAT_UNSUPPORTED"
        elif "section durations" in lowered or "section names" in lowered:
            code = "MUSIC_SECTION_INVALID"
        elif "style_adaptation" in lowered:
            code = "MUSIC_STYLE_INPUT_INVALID"
        else:
            code = "MUSIC_REQUEST_INVALID"
        raise MusicCapabilityError(
            code, details, "Fix the typed request fields, then rerun the deterministic no-GPU music plan."
        ) from exc


def backend_settings(
    request: MusicCapabilityRequest, *, score_abc: str
) -> dict[str, Any]:
    """Normalize immutable per-track settings without invoking a backend."""

    adapter = backend_for(request.model.family)
    adapter.validate(request.model, request.mode, failure=MusicCapabilityError)
    settings: dict[str, Any] = {
        "backend": adapter.backend_id,
        "model_type": adapter.model_type,
        "model_sha256": request.model.sha256,
        "preset": request.model.preset.value,
        "operation": request.mode.value,
        "title": request.title,
        "style": request.style,
        "lyrics": request.lyrics,
        "tempo_bpm": request.tempo_bpm,
        "meter": request.meter,
        "key": request.key,
        "score_sha256": hashlib.sha256(score_abc.encode("utf-8")).hexdigest(),
        "sample_rate_hz": request.output_format.sample_rate_hz,
        "channels": request.output_format.channels,
        "recipe_seed": request.recipe_seed,
    }
    if request.style_adaptation is not None:
        adaptation = request.style_adaptation
        settings["style_adaptation"] = {
            "mode": "structural_plan_only",
            "reference_hashes": [item.sha256 for item in adaptation.references],
            "before_sha256": adaptation.comparison.before.sha256,
            "after_path_planned": adaptation.comparison.after_path_planned,
            "comparison_mode": adaptation.comparison.mode,
            "command_planned": adaptation.command_planned,
        }
    return settings


def request_digest(request: MusicCapabilityRequest) -> str:
    return canonical_sha256(request.model_dump(mode="json"))


def capability_matrix() -> list[dict[str, str]]:
    return [
        {
            "family": family.value,
            "operation": operation.value,
            "status": "planned",
            "supported_for_planning": str(backend_for(family).supports(operation)).lower(),
            "generation_evidence": "none",
        }
        for family in MusicFamily
        for operation in MusicMode
    ]


__all__ = [
    "CHANNELS", "MAX_DURATION_S", "MODEL_PRESETS", "SAMPLE_RATE_HZ", "SCHEMA_VERSION",
    "AudibleComparison", "MusicCapabilityError", "MusicCapabilityRequest", "MusicFamily",
    "MusicMode", "MusicModelRef", "MusicOperation", "MusicPreset", "MusicSection",
    "OutputFormat", "StyleAdaptation", "StyleReference", "attach_manifest_model",
    "backend_settings", "capability_matrix", "canonical_json", "canonical_sha256",
    "file_sha256", "load_music_model_manifest", "request_digest",
]
