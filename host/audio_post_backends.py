"""Explicit fail-closed adapters for planned audio-post engines."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from services.jobs.compile_guard import assert_not_compiling


@dataclass(frozen=True)
class AudioPostBackendAdapter:
    backend_id: str
    model_type: str
    operations: frozenset[str]
    vram_profiles: frozenset[str]
    max_duration_s: float
    target_sample_rate_hz: int
    target_channels: int

    def supports(self, operation) -> bool:
        return operation.value in self.operations

    def validate(self, model, operation, *, failure: Callable[..., Exception]) -> None:
        """Validate immutable metadata only; this adapter never contacts a host."""

        assert_not_compiling(adapter=self.backend_id)
        if not model.license.strip() or not model.source.strip() or not model.usage_constraint.strip():
            raise failure(
                "AUDIO_POST_BACKEND_INCOMPLETE",
                f"backend {self.backend_id} lacks license, source, or usage provenance",
                "Record immutable upstream provenance and operator acceptance before planning.",
            )
        if model.license_accepted is not True:
            raise failure(
                "AUDIO_POST_BACKEND_INCOMPLETE",
                f"backend {self.backend_id} has not recorded license acceptance",
                "The operator must accept the exact model license explicitly.",
            )
        if model.vram_profile not in self.vram_profiles:
            raise failure(
                "AUDIO_POST_BACKEND_INCOMPLETE",
                f"backend {self.backend_id} has unsupported VRAM profile {model.vram_profile!r}",
                "Use a profile declared for this planned backend.",
                metadata={"supported": sorted(self.vram_profiles)},
            )
        if operation.value not in self.operations:
            raise failure(
                "AUDIO_POST_OPERATION_UNSUPPORTED",
                f"backend {self.backend_id} does not plan {operation.value}",
                "Select a supported engine/operation pair; do not bypass the matrix.",
                metadata={"supported_operations": sorted(self.operations)},
            )

    def describe(self) -> dict[str, object]:
        return {
            "backend_id": self.backend_id,
            "model_type": self.model_type,
            "operations": sorted(self.operations),
            "vram_profiles": sorted(self.vram_profiles),
            "max_duration_s": self.max_duration_s,
            "target_sample_rate_hz": self.target_sample_rate_hz,
            "target_channels": self.target_channels,
            "execution_status": "planned",
            "host_contact": False,
        }


BACKENDS: Mapping[str, AudioPostBackendAdapter] = {
    "stable_audio": AudioPostBackendAdapter(
        backend_id="wangp-stable-audio-sfx-planned",
        model_type="planned/stable_audio_sfx",
        operations=frozenset(("sfx",)),
        vram_profiles=frozenset(("12gb", "16gb", "24gb", "48gb")),
        max_duration_s=600.0,
        target_sample_rate_hz=48_000,
        target_channels=2,
    ),
    "vibevoice": AudioPostBackendAdapter(
        backend_id="wangp-vibevoice-revoice-planned",
        model_type="planned/vibevoice_revoice",
        operations=frozenset(("revoice",)),
        vram_profiles=frozenset(("24gb", "48gb")),
        max_duration_s=600.0,
        target_sample_rate_hz=48_000,
        target_channels=2,
    ),
    "deepfilternet": AudioPostBackendAdapter(
        backend_id="wangp-deepfilternet-refine-planned",
        model_type="planned/deepfilternet_refine",
        operations=frozenset(("refine",)),
        vram_profiles=frozenset(("8gb", "12gb", "16gb", "24gb", "48gb")),
        max_duration_s=3_600.0,
        target_sample_rate_hz=48_000,
        target_channels=2,
    ),
}


def backend_for(family) -> AudioPostBackendAdapter:
    try:
        return BACKENDS[family.value]
    except (AttributeError, KeyError) as exc:
        raise ValueError(f"unknown audio-post family {family!r}") from exc


def model_id(family, preset) -> str:
    return f"{family.value}/{preset.value}"


__all__ = ["BACKENDS", "AudioPostBackendAdapter", "backend_for", "model_id"]
