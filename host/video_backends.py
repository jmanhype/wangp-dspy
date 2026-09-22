"""Explicit fail-closed adapters for planned Maestro video backends."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from services.jobs.compile_guard import assert_not_compiling


@dataclass(frozen=True)
class VideoBackendAdapter:
    backend_id: str
    model_type: str
    operations: frozenset[str]
    vram_profiles: frozenset[str]

    def supports(self, operation) -> bool:
        return operation.value in self.operations

    def validate(self, model, operation, *, failure: Callable[..., Exception]) -> None:
        """Validate local immutable metadata only; never contact a host."""

        assert_not_compiling(adapter=self.backend_id)
        if not model.license.strip():
            raise failure(
                "VIDEO_BACKEND_INCOMPLETE",
                f"backend {self.backend_id} has no recorded license",
                "Record the model license and operator acceptance before planning.",
            )
        if model.license_accepted is not True:
            raise failure(
                "VIDEO_BACKEND_INCOMPLETE",
                f"backend {self.backend_id} has not recorded license acceptance",
                "The operator must accept the exact model license explicitly.",
            )
        if model.vram_profile not in self.vram_profiles:
            raise failure(
                "VIDEO_BACKEND_INCOMPLETE",
                f"backend {self.backend_id} has unsupported VRAM profile {model.vram_profile!r}",
                "Use a profile declared for this planned backend.",
                metadata={"supported": sorted(self.vram_profiles)},
            )
        if operation.value not in self.operations:
            raise failure(
                "VIDEO_OPERATION_UNSUPPORTED",
                f"backend {self.backend_id} does not plan {operation.value}",
                "Select a documented family/preset and operation pair; do not bypass the matrix.",
                metadata={"supported_operations": sorted(self.operations)},
            )

    def describe(self) -> dict[str, object]:
        return {
            "backend_id": self.backend_id,
            "model_type": self.model_type,
            "operations": sorted(self.operations),
            "vram_profiles": sorted(self.vram_profiles),
            "execution_status": "planned",
            "host_contact": False,
        }


_ALL = frozenset((
    "create", "extend", "blend", "retake", "edit", "outpaint",
    "repaint", "recast", "upscale",
))
_NO_OUTPAINT = _ALL - {"outpaint"}
_CONTINUITY = _ALL - {"outpaint", "upscale"}
_EDIT_FAMILY = _ALL - {"blend"}


BACKENDS: Mapping[str, VideoBackendAdapter] = {
    "minimax_h3": VideoBackendAdapter(
        backend_id="wangp-minimax-h3",
        model_type="minimax_h3_fl2va_pruned",
        operations=_ALL,
        vram_profiles=frozenset(("24gb", "48gb")),
    ),
    "ltx": VideoBackendAdapter(
        backend_id="maestro-ltx-planned",
        model_type="planned/ltx",
        operations=_EDIT_FAMILY,
        vram_profiles=frozenset(("16gb", "24gb", "48gb")),
    ),
    "scail": VideoBackendAdapter(
        backend_id="maestro-scail-planned",
        model_type="planned/scail",
        operations=_CONTINUITY,
        vram_profiles=frozenset(("24gb", "48gb")),
    ),
    "wan": VideoBackendAdapter(
        backend_id="wangp-wan2gp",
        model_type="planned/wan_2gp",
        operations=_ALL,
        vram_profiles=frozenset(("16gb", "24gb", "48gb")),
    ),
    "hunyuan": VideoBackendAdapter(
        backend_id="maestro-hunyuan-planned",
        model_type="planned/hunyuan",
        operations=_NO_OUTPAINT,
        vram_profiles=frozenset(("24gb", "48gb")),
    ),
}


def backend_for(family) -> VideoBackendAdapter:
    try:
        return BACKENDS[family.value]
    except (AttributeError, KeyError) as exc:
        raise ValueError(f"unknown video family {family!r}") from exc


def model_id(family, preset) -> str:
    return f"{family.value}/{preset.value}"


__all__ = ["BACKENDS", "VideoBackendAdapter", "backend_for", "model_id"]
