"""Typed finishing-request normalization without GPU, host, or render work."""
from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SCHEMA_VERSION = "wangp-dspy.finishing-request/v1"
MAX_DURATION_S = 4 * 60 * 60
DEFAULT_FPS = 24.0


class FinishingBackend(str, Enum):
    ffmpeg = "ffmpeg"
    rife = "rife"
    real_esrgan = "real_esrgan"
    film = "film"
    neural_frame_gen = "neural_frame_gen"


class InterpolationFactor(str, Enum):
    x2 = "x2"
    x3 = "x3"
    x4 = "x4"

    @property
    def multiplier(self) -> int:
        return {"x2": 2, "x3": 3, "x4": 4}[self.value]


class SpatialScale(str, Enum):
    x2 = "x2"
    x3 = "x3"
    x4 = "x4"

    @property
    def multiplier(self) -> int:
        return {"x2": 2, "x3": 3, "x4": 4}[self.value]


class OutputContainer(str, Enum):
    mp4 = "mp4"
    mov = "mov"
    mkv = "mkv"
    webm = "webm"


class OutputCodec(str, Enum):
    h264 = "h264"
    hevc = "hevc"
    vp9 = "vp9"
    av1 = "av1"
    prores = "prores"


BACKEND_OPERATIONS: Mapping[FinishingBackend, frozenset[str]] = {
    FinishingBackend.ffmpeg: frozenset({
        "interpolation", "spatial_upscale", "film_grain", "face_refinement", "codec",
    }),
    FinishingBackend.rife: frozenset({"interpolation", "codec"}),
    FinishingBackend.real_esrgan: frozenset({"spatial_upscale", "codec"}),
    FinishingBackend.film: frozenset({"film_grain", "codec"}),
    FinishingBackend.neural_frame_gen: frozenset({
        "interpolation", "spatial_upscale", "face_refinement", "codec",
    }),
}

CONTAINER_CODECS: Mapping[OutputContainer, frozenset[OutputCodec]] = {
    OutputContainer.mp4: frozenset({
        OutputCodec.h264, OutputCodec.hevc, OutputCodec.av1,
    }),
    OutputContainer.mov: frozenset({OutputCodec.h264, OutputCodec.prores}),
    OutputContainer.mkv: frozenset({
        OutputCodec.h264, OutputCodec.hevc, OutputCodec.vp9, OutputCodec.av1,
    }),
    OutputContainer.webm: frozenset({OutputCodec.vp9}),
}

CODEC_ARGUMENTS: Mapping[OutputCodec, tuple[str, ...]] = {
    OutputCodec.h264: ("-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p"),
    OutputCodec.hevc: ("-c:v", "libx265", "-crf", "20", "-pix_fmt", "yuv420p"),
    OutputCodec.vp9: ("-c:v", "libvpx-vp9", "-crf", "28", "-pix_fmt", "yuv420p"),
    OutputCodec.av1: ("-c:v", "libsvtav1", "-crf", "28", "-pix_fmt", "yuv420p"),
    OutputCodec.prores: ("-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le"),
}

_HASH_RE = re.compile(r"[0-9a-f]{64}")


class FinishingCapabilityError(ValueError):
    """A typed, fail-closed finishing planning rejection."""

    def __init__(
        self,
        code: str,
        observed: str,
        remediation: str,
        *,
        next_command: str = "wgp finish plan --request <request> --dry-run --json",
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
    if _HASH_RE.fullmatch(normalized) is None:
        raise ValueError("sha256 must be exactly 64 lowercase hexadecimal characters")
    return normalized


def _fraction(value: str) -> float:
    numerator, separator, denominator = value.partition("/")
    if not separator or not numerator.isdigit() or not denominator.isdigit():
        raise ValueError("frame rate must be an N/D rational string such as 24000/1001")
    if int(denominator) == 0:
        raise ValueError("frame-rate denominator cannot be zero")
    return int(numerator) / int(denominator)


class SourceStreamDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    index: int = Field(ge=0)
    codec_name: str = Field(min_length=1, pattern=r"^[a-z0-9_]+$")
    codec_type: str = Field(pattern="^video$")
    width: int = Field(ge=16, le=16_384)
    height: int = Field(ge=16, le=16_384)
    duration_s: float = Field(gt=0.0, le=MAX_DURATION_S)
    avg_frame_rate: str

    @field_validator("avg_frame_rate")
    @classmethod
    def _rational_rate(cls, value: str) -> str:
        rate = _fraction(value)
        if not 1.0 <= rate <= 240.0:
            raise ValueError("avg_frame_rate must normalize between 1 and 240 fps")
        return value


class SourceAssetDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    stream: SourceStreamDeclaration
    immutable: bool = True
    measurement: str = Field(default="declared_ffprobe_unverified")

    _hash = field_validator("sha256", mode="before")(_lower_hash)

    @model_validator(mode="after")
    def _fixed_source(self) -> "SourceAssetDeclaration":
        if self.immutable is not True:
            raise ValueError("finishing source must be declared immutable")
        if self.measurement != "declared_ffprobe_unverified":
            raise ValueError("source measurement must remain declared_ffprobe_unverified")
        return self


class InterpolationControls(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    factor: InterpolationFactor
    target_fps: float = Field(gt=1.0, le=240.0)
    scene_detection: bool = True


class SpatialUpscaleControls(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scale: SpatialScale
    model_sha256: str | None = Field(default=None, min_length=64, max_length=64)


class FilmGrainControls(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    strength: float = Field(ge=0.0, le=64.0)
    size: int = Field(default=16, ge=4, le=64)
    temporal_persistence: float = Field(default=0.5, ge=0.0, le=1.0)


class FaceTrack(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    track_id: str = Field(min_length=1, max_length=120)
    identity_label: str = Field(min_length=1, max_length=160)
    confidence: float = Field(ge=0.0, le=1.0)
    start_s: float = Field(ge=0.0, lt=MAX_DURATION_S)
    end_s: float = Field(gt=0.0, le=MAX_DURATION_S)
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    width: float = Field(gt=0.0, le=1.0)
    height: float = Field(gt=0.0, le=1.0)
    source: str = Field(min_length=1)
    license: str = Field(min_length=1)
    consent_ref: str = Field(min_length=1)

    @model_validator(mode="after")
    def _geometry(self) -> "FaceTrack":
        if self.end_s <= self.start_s:
            raise ValueError("face track end_s must be greater than start_s")
        if self.x + self.width > 1.0 + 1e-12:
            raise ValueError("face-track x plus width must remain within normalized bounds")
        if self.y + self.height > 1.0 + 1e-12:
            raise ValueError("face-track y plus height must remain within normalized bounds")
        return self


class FaceRefinementControls(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tracks: tuple[FaceTrack, ...] = Field(min_length=1)
    selected_track: str | None = None
    strength: float = Field(ge=0.0, le=1.0)


class NeuralPathDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    model_sha256: str = Field(min_length=64, max_length=64)
    backend_profile: str = Field(min_length=1)
    minimum_vram_gb: int = Field(ge=4, le=256)
    authorized_host: str | None = None
    support_status: str = Field(default="unavailable_without_authorized_host")

    _hash = field_validator("model_sha256", mode="before")(_lower_hash)

    @model_validator(mode="after")
    def _explicit_unavailability(self) -> "NeuralPathDeclaration":
        if self.authorized_host is not None or self.support_status != "unavailable_without_authorized_host":
            raise ValueError(
                "the no-GPU surface cannot authorize a neural host; declare "
                "authorized_host=null and support_status=unavailable_without_authorized_host"
            )
        return self


class OutputTarget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    container: OutputContainer
    codec: OutputCodec
    overwrite: bool = False
    measurement: str = Field(default="planned_ffprobe_unverified")

    @model_validator(mode="after")
    def _codec_container(self) -> "OutputTarget":
        if self.codec not in CONTAINER_CODECS[self.container]:
            allowed = ", ".join(item.value for item in sorted(
                CONTAINER_CODECS[self.container], key=lambda item: item.value
            ))
            raise ValueError(
                f"container {self.container.value} does not support codec "
                f"{self.codec.value}; allowed: {allowed}"
            )
        if self.overwrite is not False:
            raise ValueError("finishing refuses overwrite; choose a new output path")
        if self.measurement != "planned_ffprobe_unverified":
            raise ValueError("output measurement must remain planned_ffprobe_unverified")
        return self


class FinishingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SCHEMA_VERSION
    backend: FinishingBackend
    source: SourceAssetDeclaration
    interpolation: InterpolationControls | None = None
    spatial_upscale: SpatialUpscaleControls | None = None
    film_grain: FilmGrainControls | None = None
    face_refinement: FaceRefinementControls | None = None
    neural_path: NeuralPathDeclaration | None = None
    output: OutputTarget
    recipe_seed: int = Field(ge=0, le=2_147_483_647)

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version {value!r}; expected {SCHEMA_VERSION}")
        return value

    @model_validator(mode="after")
    def _one_operation_and_backend_shape(self) -> "FinishingRequest":
        selected = {
            "interpolation": self.interpolation is not None,
            "spatial_upscale": self.spatial_upscale is not None,
            "film_grain": self.film_grain is not None,
            "face_refinement": self.face_refinement is not None,
        }
        if not any(selected.values()):
            raise ValueError("finishing request requires at least one refinement operation")
        unsupported = sorted(name for name, enabled in selected.items() if enabled and name not in BACKEND_OPERATIONS[self.backend])
        if unsupported:
            raise ValueError(
                f"backend {self.backend.value} does not plan operations: {', '.join(unsupported)}"
            )
        spatial_model = self.spatial_upscale.model_sha256 if self.spatial_upscale else None
        if self.backend is FinishingBackend.real_esrgan and spatial_model is None:
            raise ValueError("real_esrgan spatial upscale requires an immutable model_sha256")
        if self.backend is not FinishingBackend.real_esrgan and spatial_model is not None:
            raise ValueError("model_sha256 is valid only for the real_esrgan backend")
        if self.neural_path is not None and self.backend is not FinishingBackend.neural_frame_gen:
            raise ValueError("neural_path requires backend neural_frame_gen")
        if self.interpolation is not None:
            source_fps = _fraction(self.source.stream.avg_frame_rate)
            expected = round(source_fps * self.interpolation.factor.multiplier, 6)
            if abs(self.interpolation.target_fps - expected) > 0.001:
                raise ValueError(
                    f"interpolation target_fps must equal source fps {source_fps:.6f} "
                    f"times {self.interpolation.factor.multiplier}"
                )
        if self.face_refinement is not None:
            ids = [track.track_id for track in self.face_refinement.tracks]
            if len(ids) != len(set(ids)):
                raise ValueError("face track_id values must be unique")
        return self


def request_operations(request: FinishingRequest) -> tuple[str, ...]:
    operations = tuple(name for name, value in (
        ("interpolation", request.interpolation),
        ("spatial_upscale", request.spatial_upscale),
        ("film_grain", request.film_grain),
        ("face_refinement", request.face_refinement),
    ) if value is not None)
    return (*operations, "codec")


def backend_settings(request: FinishingRequest) -> dict[str, Any]:
    """Normalize immutable per-backend settings without invoking a backend."""

    operations = request_operations(request)
    settings: dict[str, Any] = {
        "backend": request.backend.value,
        "operations": list(operations),
        "source_sha256": request.source.sha256,
        "source_stream_index": request.source.stream.index,
        "source_width": request.source.stream.width,
        "source_height": request.source.stream.height,
        "source_frame_rate": request.source.stream.avg_frame_rate,
        "container": request.output.container.value,
        "codec": request.output.codec.value,
        "codec_arguments": list(CODEC_ARGUMENTS[request.output.codec]),
        "recipe_seed": request.recipe_seed,
    }
    if request.interpolation is not None:
        settings["interpolation"] = request.interpolation.model_dump(mode="json")
    if request.spatial_upscale is not None:
        settings["spatial_upscale"] = request.spatial_upscale.model_dump(mode="json")
    if request.film_grain is not None:
        settings["film_grain"] = request.film_grain.model_dump(mode="json")
    if request.face_refinement is not None:
        settings["face_refinement"] = request.face_refinement.model_dump(mode="json")
    if request.neural_path is not None:
        settings["neural_path"] = request.neural_path.model_dump(mode="json")
        settings["neural_execution"] = "unavailable"
    return settings


def canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def request_digest(request: FinishingRequest) -> str:
    return canonical_sha256(request.model_dump(mode="json"))


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finishing_next_command(verb: str = "plan") -> str:
    return f"wgp finish {verb} --request <request> --dry-run --json"


__all__ = [
    "BACKEND_OPERATIONS", "CODEC_ARGUMENTS", "CONTAINER_CODECS", "DEFAULT_FPS",
    "MAX_DURATION_S", "SCHEMA_VERSION", "FaceRefinementControls", "FaceTrack",
    "FinishingBackend", "FinishingCapabilityError", "FinishingRequest",
    "InterpolationControls", "InterpolationFactor", "NeuralPathDeclaration",
    "OutputCodec", "OutputContainer", "OutputTarget", "SourceAssetDeclaration",
    "SourceStreamDeclaration", "SpatialScale", "SpatialUpscaleControls",
    "backend_settings", "canonical_json", "canonical_sha256", "file_sha256",
    "finishing_next_command", "request_digest", "request_operations",
]
