"""Explicit fail-closed adapters for the two planned music backends."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from services.jobs.compile_guard import assert_not_compiling


@dataclass(frozen=True)
class MusicBackendAdapter:
    backend_id: str
    model_type: str
    operations: frozenset[str]
    vram_profiles: frozenset[str]

    def supports(self, operation) -> bool:
        return operation.value in self.operations

    def validate(self, model, operation, *, failure: Callable[..., Exception]) -> None:
        """Check local provenance only; this adapter never contacts a host."""

        assert_not_compiling(adapter=self.backend_id)
        if not model.license.strip() or not model.source.strip() or not model.usage_constraint.strip():
            raise failure(
                "MUSIC_BACKEND_INCOMPLETE",
                f"backend {self.backend_id} lacks license, source, or usage provenance",
                "Record immutable upstream provenance and operator acceptance before planning.",
            )
        if model.license_accepted is not True:
            raise failure(
                "MUSIC_BACKEND_INCOMPLETE",
                f"backend {self.backend_id} has not recorded license acceptance",
                "The operator must accept the exact model license explicitly.",
            )
        if model.vram_profile not in self.vram_profiles:
            raise failure(
                "MUSIC_BACKEND_INCOMPLETE",
                f"backend {self.backend_id} has unsupported VRAM profile {model.vram_profile!r}",
                "Use a profile declared for this planned backend.",
                metadata={"supported": sorted(self.vram_profiles)},
            )
        if operation.value not in self.operations:
            raise failure(
                "MUSIC_OPERATION_UNSUPPORTED",
                f"backend {self.backend_id} does not plan {operation.value}",
                "Select a supported backend/operation pair; do not bypass the matrix.",
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


_OPERATIONS = frozenset(("generate", "style_adaptation"))
BACKENDS: Mapping[str, MusicBackendAdapter] = {
    "ace_step": MusicBackendAdapter(
        backend_id="wangp-music-ace-step-planned",
        model_type="planned/ace_step",
        operations=_OPERATIONS,
        vram_profiles=frozenset(("16gb", "24gb", "48gb")),
    ),
    "stable_audio": MusicBackendAdapter(
        backend_id="wangp-music-stable-audio-planned",
        model_type="planned/stable_audio",
        operations=frozenset(("generate",)),
        vram_profiles=frozenset(("12gb", "16gb", "24gb", "48gb")),
    ),
}


def backend_for(family) -> MusicBackendAdapter:
    try:
        return BACKENDS[family.value]
    except (AttributeError, KeyError) as exc:
        raise ValueError(f"unknown music family {family!r}") from exc


def model_id(family, preset) -> str:
    return f"{family.value}/{preset.value}"


__all__ = ["BACKENDS", "MusicBackendAdapter", "backend_for", "model_id"]
