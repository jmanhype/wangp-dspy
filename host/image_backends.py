"""Explicit fail-closed adapters for planned Maestro image backends."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from services.jobs.compile_guard import assert_not_compiling


@dataclass(frozen=True)
class ImageBackendAdapter:
    backend_id: str
    model_type: str
    operations: frozenset[str]
    vram_profiles: frozenset[str]
    dimension_quantum: int
    max_references: int = 10

    def supports(self, operation) -> bool:
        return operation.value in self.operations

    def validate(self, model, operation, *, failure: Callable[..., Exception]) -> None:
        """Check immutable metadata only; this adapter never contacts a host."""

        assert_not_compiling(adapter=self.backend_id)
        if not model.license.strip() or model.license_accepted is not True:
            raise failure(
                "IMAGE_BACKEND_INCOMPLETE",
                f"backend {self.backend_id} lacks license acceptance",
                "Record the model license and explicit operator acceptance.",
            )
        if model.vram_profile not in self.vram_profiles:
            raise failure(
                "IMAGE_BACKEND_INCOMPLETE",
                f"backend {self.backend_id} has unsupported VRAM profile {model.vram_profile!r}",
                "Use an inventory profile declared for this planned backend.",
                metadata={"supported": sorted(self.vram_profiles)},
            )
        if operation.value not in self.operations:
            raise failure(
                "IMAGE_OPERATION_UNSUPPORTED",
                f"backend {self.backend_id} does not plan {operation.value}",
                "Select a documented backend/operation pair; do not bypass the matrix.",
                metadata={"supported_operations": sorted(self.operations)},
            )

    def validate_output(self, output, *, failure: Callable[..., Exception]) -> None:
        quantum = self.dimension_quantum
        if output.width % quantum or output.height % quantum:
            raise failure(
                "IMAGE_OUTPUT_UNSUPPORTED",
                f"{self.backend_id} requires {quantum}-pixel output alignment, got {output.width}x{output.height}",
                "Choose aligned dimensions supported by the planned backend.",
            )

    def describe(self) -> dict[str, object]:
        return {
            "backend_id": self.backend_id,
            "model_type": self.model_type,
            "operations": sorted(self.operations),
            "vram_profiles": sorted(self.vram_profiles),
            "dimension_quantum": self.dimension_quantum,
            "max_references": self.max_references,
            "execution_status": "planned",
            "host_contact": False,
        }


_ALL = frozenset(("generate", "edit", "upscale", "outpaint", "identity_edit"))
_EDIT_FAMILY = _ALL - {"upscale", "outpaint"}

BACKENDS: Mapping[str, ImageBackendAdapter] = {
    "qwen_image": ImageBackendAdapter(
        backend_id="wangp-qwen-image-planned",
        model_type="planned/qwen_image",
        operations=_ALL,
        vram_profiles=frozenset(("16gb", "24gb", "48gb")),
        dimension_quantum=8,
    ),
    "flux_kontext": ImageBackendAdapter(
        backend_id="wangp-flux-kontext-planned",
        model_type="planned/flux_kontext",
        operations=_EDIT_FAMILY,
        vram_profiles=frozenset(("24gb", "48gb")),
        dimension_quantum=16,
    ),
}


def backend_for(family) -> ImageBackendAdapter:
    try:
        return BACKENDS[family.value]
    except (AttributeError, KeyError) as exc:
        raise ValueError(f"unknown image family {family!r}") from exc


def model_id(family, preset) -> str:
    return f"{family.value}/{preset.value}"


__all__ = ["BACKENDS", "ImageBackendAdapter", "backend_for", "model_id"]
