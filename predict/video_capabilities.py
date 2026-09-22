"""Typed Maestro video request normalization without GPU work.

This module is deliberately a planning surface.  It reuses the existing
WanGP job-config field set and profile authority, records immutable model,
LoRA, reference, window, and overlap inputs, and never converts a normalized
request into a generation claim.
"""
from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from host.video_backends import backend_for, model_id
from predict.job_config import SHOT_LENGTH_FLOOR_FRAMES, WanGPJobConfig
from predict.profile_selector import KNOWN_WANGP_PROFILES, ProfileDecision
from predict.render_profiles import Ref2VAProfile


SCHEMA_VERSION = "wangp-dspy.video-capability-request/v1"
FPS = Ref2VAProfile.FPS
MAX_LONG_FORM_S = 60 * 60


class VideoFamily(str, Enum):
    minimax_h3 = "minimax_h3"
    ltx = "ltx"
    scail = "scail"
    wan = "wan"
    hunyuan = "hunyuan"


class VideoPreset(str, Enum):
    standard = "standard"
    h3_vdn_hybrid_attention = "h3_vdn_hybrid_attention"
    taomate_three_step = "taomate_three_step"
    kfi_frames_injection = "kfi_frames_injection"
    h3_outpaint = "h3_outpaint"
    h3_audio_refinement = "h3_audio_refinement"
    ltx_2_5 = "2.5"
    ltx_2_3 = "2.3"
    scail_2 = "2"
    wan_2gp = "2gp"
    hunyuan_standard = "standard"


MODEL_PRESETS: Mapping[VideoFamily, frozenset[VideoPreset]] = {
    VideoFamily.minimax_h3: frozenset({
        VideoPreset.standard,
        VideoPreset.h3_vdn_hybrid_attention,
        VideoPreset.taomate_three_step,
        VideoPreset.kfi_frames_injection,
        VideoPreset.h3_outpaint,
        VideoPreset.h3_audio_refinement,
    }),
    VideoFamily.ltx: frozenset({VideoPreset.ltx_2_5, VideoPreset.ltx_2_3}),
    VideoFamily.scail: frozenset({VideoPreset.scail_2}),
    VideoFamily.wan: frozenset({VideoPreset.wan_2gp}),
    VideoFamily.hunyuan: frozenset({VideoPreset.hunyuan_standard}),
}


class VideoOperation(str, Enum):
    create = "create"
    extend = "extend"
    blend = "blend"
    retake = "retake"
    edit = "edit"
    outpaint = "outpaint"
    repaint = "repaint"
    recast = "recast"
    upscale = "upscale"


class OverlapStrategy(str, Enum):
    none = "none"
    sliding_window = "sliding_window"


class LongFormMode(str, Enum):
    one_window = "one_window"
    exact_timecode = "exact_timecode"
    window_count = "window_count"


class VideoCapabilityError(ValueError):
    """A typed, fail-closed video planning rejection."""

    def __init__(
        self,
        code: str,
        observed: str,
        remediation: str,
        *,
        next_command: str = "wgp video --request <request> --models <models> --dry-run --json",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation
        self.next_command = next_command
        self.metadata = dict(metadata or {})


class VideoModelRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    family: VideoFamily
    preset: VideoPreset
    sha256: str = Field(min_length=64, max_length=64)
    license: str = Field(min_length=1)
    license_accepted: bool
    vram_profile: str = Field(min_length=1)

    @field_validator("sha256")
    @classmethod
    def _lower_hex(cls, value: str) -> str:
        normalized = value.lower()
        if re.fullmatch(r"[0-9a-f]{64}", normalized) is None:
            raise ValueError("model sha256 must be 64 lowercase hexadecimal characters")
        return normalized

    @model_validator(mode="after")
    def _preset_belongs_to_family(self) -> "VideoModelRef":
        if self.preset not in MODEL_PRESETS[self.family]:
            allowed = ", ".join(sorted(item.value for item in MODEL_PRESETS[self.family]))
            raise ValueError(f"preset {self.preset.value!r} is not valid for {self.family.value}; allowed: {allowed}")
        return self


class VideoLoRA(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    weight: float = Field(ge=0.0, le=1.0)

    @field_validator("sha256")
    @classmethod
    def _lower_hex(cls, value: str) -> str:
        normalized = value.lower()
        if re.fullmatch(r"[0-9a-f]{64}", normalized) is None:
            raise ValueError("LoRA sha256 must be 64 lowercase hexadecimal characters")
        return normalized


class VideoClipPrompt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    prompt: str = Field(min_length=1)
    duration_s: float = Field(gt=0.0, le=MAX_LONG_FORM_S)
    reference: str | None = None


class VideoOverlap(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    strategy: OverlapStrategy = OverlapStrategy.none
    frames: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _strategy_shape(self) -> "VideoOverlap":
        if self.strategy is OverlapStrategy.none and self.frames != 0:
            raise ValueError("overlap strategy none requires frames=0")
        if self.strategy is OverlapStrategy.sliding_window and self.frames < 1:
            raise ValueError("overlap strategy sliding_window requires at least one frame")
        return self


class ExactTimecode(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    start: str
    end: str


class LongFormControl(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: LongFormMode
    one_window: bool | None = None
    exact_timecode: ExactTimecode | None = None
    window_count: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _one_control(self) -> "LongFormControl":
        selected = sum(value is not None for value in (self.one_window, self.exact_timecode, self.window_count))
        if selected != 1:
            raise ValueError("long_form must supply exactly the control selected by mode")
        if self.mode is LongFormMode.one_window and self.one_window is not True:
            raise ValueError("mode one_window requires one_window=true")
        if self.mode is LongFormMode.exact_timecode and self.exact_timecode is None:
            raise ValueError("mode exact_timecode requires start and end timecodes")
        if self.mode is LongFormMode.window_count and self.window_count is None:
            raise ValueError("mode window_count requires a positive window_count")
        return self


class RenderControls(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    width: int = Field(default=480, ge=64, le=4096)
    height: int = Field(default=832, ge=64, le=4096)
    num_inference_steps: int = Field(default=20, ge=1, le=100)
    guidance_scale: float = Field(default=1.0, ge=0.0, le=20.0)
    embedded_guidance_scale: float = Field(default=6.0, ge=0.0, le=20.0)
    force_fps: str = Field(default="24")
    profile: str = "profile3"

    @field_validator("profile")
    @classmethod
    def _known_profile(cls, value: str) -> str:
        if value not in KNOWN_WANGP_PROFILES:
            raise ValueError(f"unknown WangP profile {value!r}; known: {sorted(KNOWN_WANGP_PROFILES)}")
        return value

    @field_validator("force_fps")
    @classmethod
    def _supported_fps(cls, value: str) -> str:
        if value != "24":
            raise ValueError(
                f"unsupported force_fps {value!r}; video planning and "
                "window accounting require the verified 24fps contract"
            )
        return value


class VideoCapabilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SCHEMA_VERSION
    model: VideoModelRef
    operation: VideoOperation
    clips: Sequence[VideoClipPrompt] = Field(min_length=1)
    overlap: VideoOverlap = VideoOverlap()
    long_form: LongFormControl
    loras: Sequence[VideoLoRA] = Field(default_factory=tuple)
    render: RenderControls = RenderControls()
    recipe_seed: int = Field(ge=0, le=2_147_483_647)

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version {value!r}; expected {SCHEMA_VERSION}")
        return value

    @model_validator(mode="after")
    def _model_operation(self) -> "VideoCapabilityRequest":
        backend_for(self.model.family).validate(
            self.model,
            self.operation,
            failure=VideoCapabilityError,
        )
        if self.overlap.frames >= min(
            max(1, int(round(clip.duration_s * FPS))) for clip in self.clips
        ):
            raise ValueError("overlap frames must be shorter than every clip")
        return self


_TIMECODE_RE = re.compile(r"^([01][0-9]):([0-5][0-9]):([0-5][0-9]):([0-9][0-9])$")


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


def parse_timecode(value: str) -> float:
    match = _TIMECODE_RE.fullmatch(value or "")
    if match is None:
        raise VideoCapabilityError(
            "VIDEO_TIMECODE_INVALID",
            f"invalid HH:MM:SS:FF timecode {value!r}",
            "Use a 24-fps timecode from 00:00:00:00 through 01:00:00:00.",
            metadata={"fps": FPS, "value": value},
        )
    hours, minutes, seconds, frames = (int(part) for part in match.groups())
    if frames > 23:
        raise VideoCapabilityError(
            "VIDEO_TIMECODE_INVALID",
            f"invalid HH:MM:SS:FF timecode {value!r}: frame field {frames} is outside 0..23",
            "Use a 24-fps timecode with frame fields 00 through 23.",
            metadata={"fps": FPS, "value": value, "frames": frames},
        )
    return hours * 3600 + minutes * 60 + seconds + frames / FPS


def _manifest_entries(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("models"), list):
        payload = payload["models"]
    if not isinstance(payload, list) or not payload:
        raise VideoCapabilityError(
            "MODEL_MANIFEST_INVALID",
            "video model manifest is absent or contains no entries",
            "Supply a nonempty models array with one entry per family/preset.",
        )
    return [item for item in payload if isinstance(item, dict)]


def load_video_model_manifest(path: str | Path) -> tuple[dict[str, VideoModelRef], dict[str, dict[str, Any]]]:
    source = Path(path).expanduser()
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VideoCapabilityError(
            "MODEL_MANIFEST_MISSING",
            f"model manifest does not exist: {source}",
            "Create an operator-supplied manifest; Wangp does not download models.",
            next_command="wgp doctor --capabilities",
            metadata={"path": str(source)},
        ) from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VideoCapabilityError(
            "MODEL_MANIFEST_INVALID",
            f"cannot read model manifest {source}: {exc}",
            "Fix the JSON manifest, then rerun the no-GPU video plan.",
            metadata={"path": str(source)},
        ) from exc

    models: dict[str, VideoModelRef] = {}
    raw: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(_manifest_entries(payload), start=1):
        family = item.get("family")
        preset = item.get("preset")
        try:
            family_value = VideoFamily(family)
            preset_value = VideoPreset(preset)
        except ValueError as exc:
            raise VideoCapabilityError(
                "MODEL_MANIFEST_INVALID",
                f"model manifest entry {index} has unknown family/preset {family!r}/{preset!r}",
                "Use one family/preset combination from docs/video-capabilities.md.",
                metadata={"entry": index},
            ) from exc
        key = model_id(family_value, preset_value)
        if key in models:
            raise VideoCapabilityError(
                "MODEL_MANIFEST_INVALID",
                f"model manifest contains duplicate {key}",
                "Keep exactly one immutable entry per family/preset.",
            )
        digest = item.get("sha256")
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None:
            raise VideoCapabilityError(
                "MODEL_HASH_MISSING",
                f"model manifest entry {key} has no valid sha256",
                "Record the operator-provided 64-character model hash; Wangp will not download a model.",
                metadata={"model": key},
            )
        if not isinstance(item.get("license"), str) or not item["license"].strip():
            raise VideoCapabilityError(
                "VIDEO_BACKEND_INCOMPLETE",
                f"model manifest entry {key} has no recorded license",
                "Record the model license and operator acceptance before planning.",
            )
        if item.get("license_accepted") is not True:
            raise VideoCapabilityError(
                "VIDEO_BACKEND_INCOMPLETE",
                f"model manifest entry {key} has license_accepted=false",
                "The operator must explicitly record license acceptance; planning never infers consent.",
            )
        if not isinstance(item.get("vram_profile"), str) or not item["vram_profile"].strip():
            raise VideoCapabilityError(
                "VIDEO_BACKEND_INCOMPLETE",
                f"model manifest entry {key} has no VRAM profile",
                "Record the minimum supported VRAM profile from the authorized host inventory.",
            )
        model = VideoModelRef(
            family=family_value,
            preset=preset_value,
            sha256=digest,
            license=item["license"],
            license_accepted=True,
            vram_profile=item["vram_profile"],
        )
        try:
            backend_for(family_value).validate(model, VideoOperation.create, failure=VideoCapabilityError)
        except VideoCapabilityError:
            raise
        models[key] = model
        raw[key] = item
    return models, raw


def attach_manifest_model(
    payload: Mapping[str, Any], manifest: Mapping[str, VideoModelRef]
) -> VideoCapabilityRequest:
    document = dict(payload)
    requested = document.get("model")
    if not isinstance(requested, dict):
        raise VideoCapabilityError(
            "VIDEO_REQUEST_INVALID",
            "request is missing the model object",
            "Supply model.family and model.preset; the manifest supplies immutable provenance.",
        )
    try:
        family = VideoFamily(requested.get("family"))
        preset = VideoPreset(requested.get("preset"))
    except ValueError as exc:
        raise VideoCapabilityError(
            "VIDEO_REQUEST_INVALID",
            f"unknown model family/preset {requested.get('family')!r}/{requested.get('preset')!r}",
            "Use a family/preset documented in docs/video-capabilities.md.",
        ) from exc
    key = model_id(family, preset)
    model = manifest.get(key)
    if model is None:
        raise VideoCapabilityError(
            "MODEL_MANIFEST_MISSING",
            f"manifest has no entry for {key}",
            "Add an operator-supplied hash/license/VRAM entry; Wangp will not download the model.",
        )
    document["model"] = model.model_dump(mode="json")
    try:
        return VideoCapabilityRequest.model_validate(document)
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        code = "VIDEO_REQUEST_INVALID"
        lowered = details.lower()
        if "overlap" in lowered:
            code = "VIDEO_OVERLAP_INVALID"
        elif "force_fps" in lowered:
            code = "VIDEO_FRAME_RATE_UNSUPPORTED"
        elif "timecode" in lowered or "long_form.exact_timecode" in lowered:
            code = "VIDEO_TIMECODE_INVALID"
        elif "window" in lowered or "one_window" in lowered:
            code = "VIDEO_WINDOW_COUNT_INVALID"
        elif "does not plan" in lowered or "operation" in lowered:
            code = "VIDEO_OPERATION_UNSUPPORTED"
        raise VideoCapabilityError(
            code,
            details,
            "Fix the typed request fields, then rerun the deterministic no-GPU plan.",
        ) from exc


def _decision(model_family: VideoFamily, render: RenderControls, frames: int) -> ProfileDecision:
    return ProfileDecision(
        model="h3" if model_family is VideoFamily.minimax_h3 else "wan2gp",
        resolution="768p" if render.height >= 768 else "720p",
        shot_length_frames=frames,
        seed_policy="fixed_per_story",
        wangp_profile=render.profile,
    )


def backend_settings(
    *,
    model: VideoModelRef,
    operation: VideoOperation,
    prompt: str,
    duration_s: float,
    render: RenderControls,
    recipe_seed: int,
) -> dict[str, Any]:
    """Regenerate settings using only existing WanGPJobConfig fields."""

    adapter = backend_for(model.family)
    adapter.validate(model, operation, failure=VideoCapabilityError)
    requested_frames = max(1, int(round(duration_s * int(render.force_fps))))
    if requested_frames < SHOT_LENGTH_FLOOR_FRAMES:
        raise VideoCapabilityError(
            "VIDEO_FRAME_COUNT_BELOW_FLOOR",
            f"clip duration {duration_s}s resolves to {requested_frames}f, below the {SHOT_LENGTH_FLOOR_FRAMES}f floor",
            "Increase the clip duration to at least the governed WanGP floor.",
            metadata={
                "requested_frames": requested_frames,
                "floor": SHOT_LENGTH_FLOOR_FRAMES,
            },
        )
    decision = _decision(model.family, render, requested_frames)
    config = WanGPJobConfig(
        model_type=adapter.model_type,
        script=prompt,
        prompt="multishot",
        width=render.width,
        height=render.height,
        frames_per_shot=requested_frames,
        num_inference_steps=render.num_inference_steps,
        guidance_scale=render.guidance_scale,
        embedded_guidance_scale=render.embedded_guidance_scale,
        force_fps=render.force_fps,
        seed=recipe_seed,
    )
    settings = config.to_settings_doc(flat=True)
    settings["profile"] = {"profile1": 1, "profile2": 2, "profile3": 3}[
        decision.wangp_profile
    ]
    settings["resolution"] = decision.resolution
    return settings


def request_digest(request: VideoCapabilityRequest) -> str:
    return canonical_sha256(request.model_dump(mode="json"))


def capability_matrix() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for family in VideoFamily:
        adapter = backend_for(family)
        for operation in VideoOperation:
            rows.append({
                "family": family.value,
                "operation": operation.value,
                "status": "planned",
                "supported_for_planning": str(adapter.supports(operation)).lower(),
                "generation_evidence": "none",
            })
    return rows


__all__ = [
    "FPS",
    "MAX_LONG_FORM_S",
    "MODEL_PRESETS",
    "SCHEMA_VERSION",
    "LongFormControl",
    "LongFormMode",
    "OverlapStrategy",
    "RenderControls",
    "VideoCapabilityError",
    "VideoCapabilityRequest",
    "VideoClipPrompt",
    "VideoFamily",
    "VideoLoRA",
    "VideoModelRef",
    "VideoOperation",
    "VideoPreset",
    "attach_manifest_model",
    "backend_settings",
    "capability_matrix",
    "canonical_json",
    "canonical_sha256",
    "file_sha256",
    "load_video_model_manifest",
    "model_id",
    "parse_timecode",
    "request_digest",
]
