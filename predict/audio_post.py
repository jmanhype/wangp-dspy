"""Typed audio-post request normalization without GPU or host work."""
from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from host.audio_post_backends import backend_for, model_id

SCHEMA_VERSION = "wangp-dspy.audio-post-request/v1"
SAMPLE_RATE_HZ = 48_000
CHANNELS = 2
MAX_DURATION_S = 3_600


class AudioPostFamily(str, Enum):
    stable_audio = "stable_audio"
    vibevoice = "vibevoice"
    deepfilternet = "deepfilternet"


class AudioPostPreset(str, Enum):
    sound_effect = "sound_effect"
    revoice = "revoice"
    refinement = "refinement"


class AudioPostOperation(str, Enum):
    sfx = "sfx"
    revoice = "revoice"
    refine = "refine"


MODEL_PRESETS: Mapping[AudioPostFamily, frozenset[AudioPostPreset]] = {
    AudioPostFamily.stable_audio: frozenset((AudioPostPreset.sound_effect,)),
    AudioPostFamily.vibevoice: frozenset((AudioPostPreset.revoice,)),
    AudioPostFamily.deepfilternet: frozenset((AudioPostPreset.refinement,)),
}


class AudioPostCapabilityError(ValueError):
    """A typed, fail-closed audio-post planning rejection."""

    def __init__(
        self,
        code: str,
        observed: str,
        remediation: str,
        *,
        next_command: str = "wgp audio sfx --request <request> --models <models> --json",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation
        self.next_command = next_command
        self.metadata = dict(metadata or {})


def _lower_hash(value: str) -> str:
    normalized = value.lower()
    if re.fullmatch(r"[0-9a-f]{64}", normalized) is None:
        raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
    return normalized


class AudioPostModelRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    family: AudioPostFamily
    preset: AudioPostPreset
    sha256: str = Field(min_length=64, max_length=64)
    license: str = Field(min_length=1)
    license_accepted: bool
    source: str = Field(min_length=1)
    usage_constraint: str = Field(min_length=1)
    vram_profile: str = Field(min_length=1)

    _hash = field_validator("sha256", mode="before")(_lower_hash)

    @model_validator(mode="after")
    def _preset_allowed(self) -> "AudioPostModelRef":
        if self.preset not in MODEL_PRESETS[self.family]:
            raise ValueError(f"preset {self.preset.value!r} is invalid for {self.family.value}")
        return self


class StreamDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    index: int = Field(ge=0)
    codec_type: str
    duration_s: float = Field(gt=0.0, le=MAX_DURATION_S)


class SourceDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    video: StreamDeclaration
    audio: StreamDeclaration
    immutable: bool = True

    _hash = field_validator("sha256", mode="before")(_lower_hash)

    @model_validator(mode="after")
    def _video_fixed(self) -> "SourceDeclaration":
        if self.video.codec_type != "video" or self.audio.codec_type != "audio":
            raise ValueError("source.video must be a video stream and source.audio an audio stream")
        if self.immutable is not True:
            raise ValueError("source video must be declared immutable")
        if self.video.index == self.audio.index:
            raise ValueError("video and audio stream indexes must differ")
        return self


class VoiceBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    role: str = Field(pattern="^(primary|secondary)$")
    duration_s: float = Field(ge=2.0, le=600.0)
    source: str = Field(min_length=1)
    license: str = Field(min_length=1)
    consent_ref: str = Field(min_length=1)

    _hash = field_validator("sha256", mode="before")(_lower_hash)


class OutputFormat(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    container: str = Field(pattern="^(wav|mp4)$")
    codec: str = Field(pattern="^(pcm_s16le|aac)$")
    sample_rate_hz: int = SAMPLE_RATE_HZ
    channels: int = CHANNELS

    @model_validator(mode="after")
    def _governed_target(self) -> "OutputFormat":
        expected = "pcm_s16le" if self.container == "wav" else "aac"
        if (self.sample_rate_hz, self.channels) != (SAMPLE_RATE_HZ, CHANNELS):
            raise ValueError(
                f"audio-post output must be {SAMPLE_RATE_HZ} Hz / {CHANNELS} channels; "
                f"got {self.sample_rate_hz} Hz / {self.channels}"
            )
        if self.codec != expected:
            raise ValueError(f"container {self.container} requires codec {expected}")
        return self


class RefinementControls(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: str = Field(pattern="^(denoise_and_loudness)$")
    noise_reduction_db: float = Field(ge=0.0, le=24.0)
    target_lufs: float = Field(ge=-32.0, le=-8.0)


class VideoTransform(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation: str = Field(pattern="^(crop|scale|retime|reencode_video)$")
    value: str = Field(min_length=1)


class VideoFixedContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    immutable: bool = True
    transformations: tuple[VideoTransform, ...] = ()


class AudioPostRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SCHEMA_VERSION
    model: AudioPostModelRef
    operation: AudioPostOperation
    prompt: str | None = Field(default=None, min_length=1, max_length=2_000)
    duration_s: float | None = Field(default=None, gt=0.0, le=MAX_DURATION_S)
    source: SourceDeclaration
    voice: VoiceBinding | None = None
    refinement: RefinementControls | None = None
    video: VideoFixedContract = VideoFixedContract()
    output: OutputFormat
    output_path_planned: str = Field(min_length=1)
    recipe_seed: int = Field(ge=0, le=2_147_483_647)

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version {value!r}; expected {SCHEMA_VERSION}")
        return value

    @model_validator(mode="after")
    def _shape(self) -> "AudioPostRequest":
        if self.operation is AudioPostOperation.sfx:
            if not self.prompt or self.duration_s is None:
                raise ValueError("sfx requires prompt and duration_s")
            if self.voice is not None or self.refinement is not None:
                raise ValueError("sfx cannot carry voice or refinement controls")
            if self.output.container != "wav":
                raise ValueError("sfx output must be wav")
        elif self.operation is AudioPostOperation.revoice:
            if self.voice is None:
                raise ValueError("revoice requires a target voice binding")
            if self.refinement is not None or self.duration_s is not None:
                raise ValueError("revoice cannot carry refinement controls or a new duration")
            if self.output.container != "mp4":
                raise ValueError("revoice output must be mp4")
        else:
            if self.refinement is None:
                raise ValueError("refine requires refinement controls")
            if self.voice is not None or self.duration_s is not None:
                raise ValueError("refine cannot carry a voice binding or a new duration")
            if self.output.container != "mp4":
                raise ValueError("refine output must be mp4")
        if self.video.immutable is not True or self.video.transformations:
            raise ValueError("video transformations are refused; source video bytes are immutable")
        backend_for(self.model.family).validate(self.model, self.operation, failure=AudioPostCapabilityError)
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
        raise AudioPostCapabilityError(
            "MODEL_MANIFEST_INVALID",
            "audio-post model manifest is absent or contains no object entries",
            "Supply a nonempty models array with immutable provenance for each engine.",
        )
    return payload


def load_audio_post_model_manifest(path: str | Path) -> dict[str, AudioPostModelRef]:
    source = Path(path).expanduser()
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AudioPostCapabilityError(
            "MODEL_MANIFEST_MISSING",
            f"model manifest does not exist: {source}",
            "Create an operator-supplied manifest; Wangp does not download models.",
            metadata={"path": str(source)},
        ) from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AudioPostCapabilityError(
            "MODEL_MANIFEST_INVALID",
            f"cannot read model manifest {source}: {exc}",
            "Fix the JSON manifest, then rerun the deterministic no-GPU audio-post plan.",
            metadata={"path": str(source)},
        ) from exc
    models: dict[str, AudioPostModelRef] = {}
    for index, item in enumerate(_entries(payload), start=1):
        try:
            family, preset = AudioPostFamily(item.get("family")), AudioPostPreset(item.get("preset"))
            key = model_id(family, preset)
            digest = item.get("sha256")
            if not isinstance(digest, str) or re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None:
                raise AudioPostCapabilityError(
                    "MODEL_HASH_MISSING",
                    f"model manifest entry {key} has no valid sha256",
                    "Record the operator-provided model hash; Wangp will not download a model.",
                    metadata={"model": key},
                )
            model = AudioPostModelRef.model_validate({**item, "sha256": digest})
            backend_for(family).validate(model, AudioPostOperation.sfx, failure=AudioPostCapabilityError)
        except AudioPostCapabilityError:
            raise
        except (ValueError, ValidationError) as exc:
            raise AudioPostCapabilityError(
                "AUDIO_POST_BACKEND_INCOMPLETE",
                f"model manifest entry {index} is incomplete: {exc}",
                "Record family, preset, hash, license/acceptance, source, usage constraint, and VRAM.",
                metadata={"entry": index},
            ) from exc
        if key in models:
            raise AudioPostCapabilityError(
                "MODEL_MANIFEST_INVALID",
                f"model manifest contains duplicate {key}",
                "Keep exactly one immutable entry per engine/preset.",
            )
        models[key] = model
    return models


def attach_manifest_model(
    payload: Mapping[str, Any], manifest: Mapping[str, AudioPostModelRef]
) -> AudioPostRequest:
    document = dict(payload)
    requested = document.get("model")
    if not isinstance(requested, dict):
        raise AudioPostCapabilityError(
            "AUDIO_POST_REQUEST_INVALID",
            "request is missing the model object",
            "Supply model.family and model.preset; the manifest supplies immutable provenance.",
        )
    try:
        key = model_id(
            AudioPostFamily(requested.get("family")),
            AudioPostPreset(requested.get("preset")),
        )
    except ValueError as exc:
        raise AudioPostCapabilityError(
            "AUDIO_POST_REQUEST_INVALID",
            f"unknown audio-post family/preset {requested.get('family')!r}/{requested.get('preset')!r}",
            "Use stable_audio/sound_effect, vibevoice/revoice, or deepfilternet/refinement.",
        ) from exc
    model = manifest.get(key)
    if model is None:
        raise AudioPostCapabilityError(
            "MODEL_MANIFEST_MISSING",
            f"manifest has no entry for {key}",
            "Add immutable model provenance; Wangp will not download the model.",
        )
    document["model"] = model.model_dump(mode="json")
    try:
        return AudioPostRequest.model_validate(document)
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        lowered = details.lower()
        if "video transformations" in lowered or "immutable" in lowered:
            code = "AUDIO_POST_VIDEO_MUTATION_REFUSED"
        elif "does not plan" in lowered:
            code = "AUDIO_POST_OPERATION_UNSUPPORTED"
        elif "sample_rate" in lowered or "channels" in lowered or "codec" in lowered or "container" in lowered:
            code = "AUDIO_POST_TARGET_LAYOUT_UNSUPPORTED"
        elif "duration" in lowered:
            code = "AUDIO_POST_DURATION_MISMATCH"
        elif "voice" in lowered:
            code = "AUDIO_POST_VOICE_MISSING"
        elif "stream" in lowered:
            code = "AUDIO_POST_SOURCE_STREAM_INVALID"
        else:
            code = "AUDIO_POST_REQUEST_INVALID"
        raise AudioPostCapabilityError(
            code,
            details,
            "Fix the typed request fields, then rerun the deterministic no-GPU audio-post plan.",
        ) from exc


def backend_settings(request: AudioPostRequest) -> dict[str, Any]:
    """Normalize immutable per-engine settings without invoking a backend."""

    adapter = backend_for(request.model.family)
    adapter.validate(request.model, request.operation, failure=AudioPostCapabilityError)
    settings: dict[str, Any] = {
        "backend": adapter.backend_id,
        "model_type": adapter.model_type,
        "model_sha256": request.model.sha256,
        "operation": request.operation.value,
        "prompt": request.prompt,
        "source_sha256": request.source.sha256,
        "source_video_stream": request.source.video.index,
        "source_audio_stream": request.source.audio.index,
        "sample_rate_hz": request.output.sample_rate_hz,
        "channels": request.output.channels,
        "container": request.output.container,
        "codec": request.output.codec,
        "recipe_seed": request.recipe_seed,
    }
    if request.duration_s is not None:
        settings["duration_s"] = request.duration_s
    if request.voice is not None:
        settings["voice_sha256"] = request.voice.sha256
        settings["voice_role"] = request.voice.role
    if request.refinement is not None:
        settings["refinement"] = request.refinement.model_dump(mode="json")
    return settings


def request_digest(request: AudioPostRequest) -> str:
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
        for family in AudioPostFamily
        for operation in AudioPostOperation
    ]


__all__ = [
    "CHANNELS", "MAX_DURATION_S", "MODEL_PRESETS", "SAMPLE_RATE_HZ", "SCHEMA_VERSION",
    "AudioPostCapabilityError", "AudioPostFamily", "AudioPostModelRef", "AudioPostOperation",
    "AudioPostPreset", "AudioPostRequest", "OutputFormat", "RefinementControls",
    "SourceDeclaration", "StreamDeclaration", "VideoFixedContract", "VideoTransform", "VoiceBinding",
    "attach_manifest_model", "backend_settings", "capability_matrix", "canonical_json",
    "canonical_sha256", "file_sha256", "load_audio_post_model_manifest", "request_digest",
]
