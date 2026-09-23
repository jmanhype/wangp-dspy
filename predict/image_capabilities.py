"""Typed Maestro image request normalization without GPU work."""
from __future__ import annotations

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

from host.image_backends import backend_for, model_id
from predict.video_capabilities import canonical_sha256, file_sha256


SCHEMA_VERSION = "wangp-dspy.image-capability-request/v1"
MAX_REFERENCES = 10
MAX_IMAGE_EDGE_PX = 4096


class ImageFamily(str, Enum):
    qwen_image = "qwen_image"
    flux_kontext = "flux_kontext"


class ImagePreset(str, Enum):
    qwen_standard = "qwen-standard"
    qwen_professional = "qwen-professional"
    flux_standard = "flux-standard"
    flux_kontext = "flux-kontext"


MODEL_PRESETS: Mapping[ImageFamily, frozenset[ImagePreset]] = {
    ImageFamily.qwen_image: frozenset(
        (ImagePreset.qwen_standard, ImagePreset.qwen_professional)
    ),
    ImageFamily.flux_kontext: frozenset(
        (ImagePreset.flux_standard, ImagePreset.flux_kontext)
    ),
}


class ImageOperation(str, Enum):
    generate = "generate"
    edit = "edit"
    upscale = "upscale"
    outpaint = "outpaint"
    identity_edit = "identity_edit"


class ReferenceRole(str, Enum):
    subject = "subject"
    style = "style"
    identity = "identity"
    composition = "composition"


class ImageFormat(str, Enum):
    png = "png"
    jpeg = "jpeg"
    webp = "webp"


class EnhancementMode(str, Enum):
    off = "off"
    operator_authorized = "operator_authorized"


class IdentityMetric(str, Enum):
    face_embedding_cosine = "face_embedding_cosine"


class ImageCapabilityError(ValueError):
    """A typed, fail-closed image planning rejection."""

    def __init__(
        self,
        code: str,
        observed: str,
        remediation: str,
        *,
        next_command: str = "wgp image plan --request <request> --models <models> --dry-run --json",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation
        self.next_command = next_command
        self.metadata = dict(metadata or {})


def _sha256(value: str) -> str:
    normalized = value.lower()
    if re.fullmatch(r"[0-9a-f]{64}", normalized) is None:
        raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
    return normalized


class ImageModelRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    family: ImageFamily
    preset: ImagePreset
    sha256: str = Field(min_length=64, max_length=64)
    license: str = Field(min_length=1)
    license_accepted: bool
    vram_profile: str = Field(min_length=1)

    @field_validator("sha256")
    @classmethod
    def _normalize_sha256(cls, value: str) -> str:
        return _sha256(value)

    @model_validator(mode="after")
    def _preset_belongs_to_family(self) -> "ImageModelRef":
        if self.preset not in MODEL_PRESETS[self.family]:
            allowed = ", ".join(item.value for item in MODEL_PRESETS[self.family])
            raise ValueError(f"preset {self.preset.value!r} is invalid for {self.family.value}; allowed: {allowed}")
        return self


class ImageReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    role: ReferenceRole
    license: str = Field(min_length=1)

    @field_validator("sha256")
    @classmethod
    def _normalize_sha256(cls, value: str) -> str:
        return _sha256(value)


class ImageMask(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)

    @field_validator("path")
    @classmethod
    def _png(cls, value: str) -> str:
        if Path(value).suffix.lower() != ".png":
            raise ValueError("edit mask must be a PNG path")
        return value

    @field_validator("sha256")
    @classmethod
    def _normalize_sha256(cls, value: str) -> str:
        return _sha256(value)


class EditRegion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    source_width: int = Field(gt=0, le=MAX_IMAGE_EDGE_PX)
    source_height: int = Field(gt=0, le=MAX_IMAGE_EDGE_PX)

    @model_validator(mode="after")
    def _inside_source(self) -> "EditRegion":
        if self.x + self.width > self.source_width or self.y + self.height > self.source_height:
            raise ValueError("edit region must fit inside the declared source dimensions")
        return self


class OutputConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    format: ImageFormat = ImageFormat.png
    transparency: bool = False
    width: int = Field(ge=64, le=MAX_IMAGE_EDGE_PX)
    height: int = Field(ge=64, le=MAX_IMAGE_EDGE_PX)

    @model_validator(mode="after")
    def _alpha_contract(self) -> "OutputConstraints":
        if self.transparency and self.format is not ImageFormat.png:
            raise ValueError("transparency requires PNG output")
        return self


class UpscaleControls(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_width: int = Field(gt=0, le=MAX_IMAGE_EDGE_PX)
    source_height: int = Field(gt=0, le=MAX_IMAGE_EDGE_PX)
    factor: int = Field(ge=2, le=4)


class OutpaintControls(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_width: int = Field(gt=0, le=MAX_IMAGE_EDGE_PX)
    source_height: int = Field(gt=0, le=MAX_IMAGE_EDGE_PX)


class PromptEnhancement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: EnhancementMode = EnhancementMode.off
    provider: str | None = None
    authorization_ref: str | None = None

    @model_validator(mode="after")
    def _authorization(self) -> "PromptEnhancement":
        if self.mode is EnhancementMode.off:
            if self.provider is not None or self.authorization_ref is not None:
                raise ValueError("prompt enhancement off must omit provider and authorization_ref")
            return self
        if not self.provider or not self.authorization_ref:
            raise ValueError("authorized enhancement requires provider and authorization_ref")
        return self


class IdentityGate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metric: IdentityMetric
    threshold: float = Field(gt=0.0, le=1.0)


class ImageCapabilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SCHEMA_VERSION
    model: ImageModelRef
    operation: ImageOperation
    prompt: str = Field(min_length=1)
    license: str = Field(min_length=1)
    references: tuple[ImageReference, ...] = Field(default=(), max_length=MAX_REFERENCES)
    mask: ImageMask | None = None
    edit_region: EditRegion | None = None
    upscale: UpscaleControls | None = None
    outpaint: OutpaintControls | None = None
    prompt_enhancement: PromptEnhancement = PromptEnhancement()
    output: OutputConstraints
    identity_gate: IdentityGate | None = None
    recipe_seed: int = Field(ge=0, le=2_147_483_647)

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version {value!r}; expected {SCHEMA_VERSION}")
        return value

    @model_validator(mode="after")
    def _operation_shape(self) -> "ImageCapabilityRequest":
        adapter = backend_for(self.model.family)
        adapter.validate(self.model, self.operation, failure=ImageCapabilityError)
        adapter.validate_output(self.output, failure=ImageCapabilityError)
        operation = self.operation
        if len(self.references) > MAX_REFERENCES:
            raise ValueError(f"image requests accept at most {MAX_REFERENCES} references")
        if operation is ImageOperation.generate:
            if self.mask or self.edit_region or self.upscale or self.outpaint:
                raise ValueError("generate cannot carry edit, upscale, or outpaint controls")
        elif operation is ImageOperation.upscale:
            if len(self.references) != 1 or self.mask or self.outpaint or self.edit_region:
                raise ValueError("upscale requires exactly one reference and no edit/outpaint controls")
            if self.upscale is None:
                raise ValueError("upscale requires source dimensions and factor")
            expected = (self.upscale.source_width * self.upscale.factor, self.upscale.source_height * self.upscale.factor)
            if (self.output.width, self.output.height) != expected:
                raise ValueError("upscale output dimensions must equal source dimensions multiplied by factor")
        else:
            if len(self.references) < 1:
                raise ValueError(f"{operation.value} requires at least one reference")
            if self.mask is None:
                raise ValueError(f"{operation.value} requires a PNG edit mask")
            if operation is ImageOperation.outpaint:
                if self.outpaint is None:
                    raise ValueError("outpaint requires source dimensions")
                if self.output.width <= self.outpaint.source_width or self.output.height <= self.outpaint.source_height:
                    raise ValueError("outpaint output must be larger than the source on both axes")
            if operation is ImageOperation.identity_edit:
                if not any(reference.role is ReferenceRole.identity for reference in self.references):
                    raise ValueError("identity_edit requires at least one identity reference")
                if self.identity_gate is None:
                    raise ValueError("identity_edit requires an objective identity gate")
        return self


def _manifest_entries(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("models"), list):
        payload = payload["models"]
    if not isinstance(payload, list) or not payload:
        raise ImageCapabilityError(
            "MODEL_MANIFEST_INVALID",
            "image model manifest is absent or contains no entries",
            "Supply a nonempty models array with one entry per backend/preset.",
        )
    return [item for item in payload if isinstance(item, dict)]


def load_image_model_manifest(path: str | Path) -> dict[str, ImageModelRef]:
    source = Path(path).expanduser()
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ImageCapabilityError(
            "MODEL_MANIFEST_MISSING",
            f"model manifest does not exist: {source}",
            "Create an operator-supplied manifest; Wangp does not download models.",
            metadata={"path": str(source)},
        ) from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ImageCapabilityError(
            "MODEL_MANIFEST_INVALID",
            f"cannot read model manifest {source}: {exc}",
            "Fix the JSON manifest, then rerun the no-GPU image plan.",
            metadata={"path": str(source)},
        ) from exc

    models: dict[str, ImageModelRef] = {}
    for index, item in enumerate(_manifest_entries(payload), start=1):
        try:
            family = ImageFamily(item.get("family"))
            preset = ImagePreset(item.get("preset"))
        except ValueError as exc:
            raise ImageCapabilityError(
                "MODEL_MANIFEST_INVALID",
                f"model manifest entry {index} has unknown backend/preset {item.get('family')!r}/{item.get('preset')!r}",
                "Use a backend/preset combination from docs/image-capabilities.md.",
            ) from exc
        key = model_id(family, preset)
        if key in models:
            raise ImageCapabilityError(
                "MODEL_MANIFEST_INVALID",
                f"model manifest contains duplicate {key}",
                "Keep exactly one immutable entry per backend/preset.",
            )
        digest = item.get("sha256")
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None:
            raise ImageCapabilityError(
                "MODEL_HASH_MISSING",
                f"model manifest entry {key} has no valid sha256",
                "Record the operator-provided 64-character model hash.",
                metadata={"model": key},
            )
        if not isinstance(item.get("license"), str) or not item["license"].strip():
            raise ImageCapabilityError(
                "IMAGE_BACKEND_INCOMPLETE",
                f"model manifest entry {key} has no recorded license",
                "Record the model license before planning.",
            )
        if item.get("license_accepted") is not True or not isinstance(item.get("vram_profile"), str) or not item["vram_profile"].strip():
            raise ImageCapabilityError(
                "IMAGE_BACKEND_INCOMPLETE",
                f"model manifest entry {key} lacks license acceptance or VRAM profile",
                "Record explicit license acceptance and the supported VRAM profile.",
            )
        model = ImageModelRef(
            family=family,
            preset=preset,
            sha256=digest,
            license=item["license"],
            license_accepted=True,
            vram_profile=item["vram_profile"],
        )
        backend_for(family).validate(model, ImageOperation.generate, failure=ImageCapabilityError)
        models[key] = model
    return models


def attach_manifest_model(
    payload: Mapping[str, Any], manifest: Mapping[str, ImageModelRef]
) -> ImageCapabilityRequest:
    document = dict(payload)
    requested = document.get("model")
    if not isinstance(requested, dict):
        raise ImageCapabilityError(
            "IMAGE_REQUEST_INVALID",
            "request is missing the model object",
            "Supply model.family and model.preset; the manifest supplies immutable provenance.",
        )
    try:
        family = ImageFamily(requested.get("family"))
        preset = ImagePreset(requested.get("preset"))
    except ValueError as exc:
        raise ImageCapabilityError(
            "IMAGE_REQUEST_INVALID",
            f"unknown image backend/preset {requested.get('family')!r}/{requested.get('preset')!r}",
            "Use a backend/preset documented in docs/image-capabilities.md.",
        ) from exc
    key = model_id(family, preset)
    model = manifest.get(key)
    if model is None:
        raise ImageCapabilityError(
            "MODEL_MANIFEST_MISSING",
            f"manifest has no entry for {key}",
            "Add an operator-supplied hash/license/VRAM entry; Wangp will not download the model.",
        )
    document["model"] = model.model_dump(mode="json")
    try:
        return ImageCapabilityRequest.model_validate(document)
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        lowered = details.lower()
        code = "IMAGE_REQUEST_INVALID"
        if "references" in lowered and ("at most" in lowered or "longer than" in lowered):
            code = "IMAGE_REFERENCE_LIMIT_EXCEEDED"
        elif "identity" in lowered:
            code = "IMAGE_IDENTITY_GATE_MISSING"
        elif "prompt_enhancement" in lowered or "prompt enhancement" in lowered:
            code = "IMAGE_PROMPT_ENHANCEMENT_UNAUTHORIZED"
        elif "mask" in lowered:
            code = "IMAGE_MASK_INVALID"
        elif "does not plan" in lowered or "operation" in lowered:
            code = "IMAGE_OPERATION_UNSUPPORTED"
        elif any(word in lowered for word in ("output", "upscale", "outpaint", "dimension", "alignment")):
            code = "IMAGE_OUTPUT_UNSUPPORTED"
        raise ImageCapabilityError(
            code,
            details,
            "Fix the typed request fields, then rerun the deterministic no-GPU image plan.",
        ) from exc


def backend_settings(request: ImageCapabilityRequest) -> dict[str, Any]:
    """Normalize only immutable image fields; no bytes are decoded or sent."""

    adapter = backend_for(request.model.family)
    return {
        "normalization_version": "wangp-dspy.image-backend-settings/v1",
        "backend": request.model.family.value,
        "backend_id": adapter.backend_id,
        "backend_profile": adapter.model_type,
        "model_type": adapter.model_type,
        "preset": request.model.preset.value,
        "model_sha256": request.model.sha256,
        "operation": request.operation.value,
        "prompt": request.prompt,
        "prompt_enhancement": request.prompt_enhancement.model_dump(mode="json"),
        "references": [reference.model_dump(mode="json") for reference in request.references],
        "mask": request.mask.model_dump(mode="json") if request.mask else None,
        "edit_region": request.edit_region.model_dump(mode="json") if request.edit_region else None,
        "upscale": request.upscale.model_dump(mode="json") if request.upscale else None,
        "outpaint": request.outpaint.model_dump(mode="json") if request.outpaint else None,
        "output": request.output.model_dump(mode="json"),
        "alpha_mode": "8_bit_alpha" if request.output.transparency else "none",
        "identity_gate": request.identity_gate.model_dump(mode="json") if request.identity_gate else None,
        "image_seed": request.recipe_seed,
        "output_license": request.license,
        "host_contact": False,
    }


def request_digest(request: ImageCapabilityRequest) -> str:
    return canonical_sha256(request.model_dump(mode="json"))


def capability_matrix() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for family in ImageFamily:
        adapter = backend_for(family)
        for operation in ImageOperation:
            rows.append({
                "family": family.value,
                "operation": operation.value,
                "status": "planned",
                "supported_for_planning": str(adapter.supports(operation)).lower(),
                "generation_evidence": "none",
            })
    return rows


__all__ = [
    "MAX_IMAGE_EDGE_PX",
    "MAX_REFERENCES",
    "SCHEMA_VERSION",
    "EditRegion",
    "EnhancementMode",
    "IdentityGate",
    "IdentityMetric",
    "ImageCapabilityError",
    "ImageCapabilityRequest",
    "ImageFamily",
    "ImageFormat",
    "ImageMask",
    "ImageModelRef",
    "ImageOperation",
    "ImagePreset",
    "ImageReference",
    "OutpaintControls",
    "OutputConstraints",
    "PromptEnhancement",
    "ReferenceRole",
    "UpscaleControls",
    "attach_manifest_model",
    "backend_settings",
    "backend_for",
    "capability_matrix",
    "canonical_sha256",
    "file_sha256",
    "load_image_model_manifest",
    "model_id",
    "request_digest",
]
