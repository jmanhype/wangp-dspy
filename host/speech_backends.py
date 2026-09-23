"""Explicit fail-closed adapters for planned speech engines."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from services.jobs.compile_guard import assert_not_compiling


@dataclass(frozen=True)
class SpeechBackendAdapter:
    backend_id: str
    model_type: str
    operations: frozenset[str]
    vram_profiles: frozenset[str]
    max_segment_chars: int
    max_segment_duration_s: float
    reference_counts: frozenset[int]

    def supports(self, operation) -> bool:
        return operation.value in self.operations

    def validate(self, model, operation, *, failure: Callable[..., Exception]) -> None:
        """Check immutable metadata only; this adapter never contacts a host."""

        assert_not_compiling(adapter=self.backend_id)
        if not model.license.strip() or not model.source.strip() or not model.usage_constraint.strip():
            raise failure(
                "SPEECH_BACKEND_INCOMPLETE",
                f"backend {self.backend_id} lacks license, source, or usage provenance",
                "Record immutable upstream provenance and operator acceptance before planning.",
            )
        if model.license_accepted is not True:
            raise failure(
                "SPEECH_BACKEND_INCOMPLETE",
                f"backend {self.backend_id} has not recorded license acceptance",
                "The operator must accept the exact model license explicitly.",
            )
        if model.vram_profile not in self.vram_profiles:
            raise failure(
                "SPEECH_BACKEND_INCOMPLETE",
                f"backend {self.backend_id} has unsupported VRAM profile {model.vram_profile!r}",
                "Use a profile declared for this planned backend.",
                metadata={"supported": sorted(self.vram_profiles)},
            )
        if operation.value not in self.operations:
            raise failure(
                "SPEECH_ENGINE_MODE_UNSUPPORTED",
                f"backend {self.backend_id} does not plan {operation.value}",
                "Select a supported engine/mode pair; do not bypass the matrix.",
                metadata={"supported_modes": sorted(self.operations)},
            )

    def validate_shape(self, request, *, failure: Callable[..., Exception]) -> None:
        if len(request.references) not in self.reference_counts:
            raise failure(
                "SPEECH_ENGINE_MODE_UNSUPPORTED",
                f"backend {self.backend_id} accepts reference counts {sorted(self.reference_counts)} for {request.mode.value}",
                "Use a supported reference count for this independently implemented engine.",
                metadata={"supported_reference_counts": sorted(self.reference_counts)},
            )
        if request.segment_policy.max_segment_chars > self.max_segment_chars:
            raise failure(
                "SPEECH_SEGMENT_INVALID",
                f"backend {self.backend_id} accepts at most {self.max_segment_chars} characters per segment",
                "Lower the requested segment character limit.",
                metadata={"engine_limit": self.max_segment_chars},
            )
        if request.segment_policy.max_segment_duration_s > self.max_segment_duration_s:
            raise failure(
                "SPEECH_SEGMENT_INVALID",
                f"backend {self.backend_id} accepts at most {self.max_segment_duration_s:g} seconds per segment",
                "Lower the requested segment duration limit.",
                metadata={"engine_limit": self.max_segment_duration_s},
            )

    def describe(self) -> dict[str, object]:
        return {
            "backend_id": self.backend_id,
            "model_type": self.model_type,
            "modes": sorted(self.operations),
            "vram_profiles": sorted(self.vram_profiles),
            "max_segment_chars": self.max_segment_chars,
            "max_segment_duration_s": self.max_segment_duration_s,
            "supported_reference_counts": sorted(self.reference_counts),
            "execution_status": "planned",
            "host_contact": False,
        }


BACKENDS: Mapping[str, SpeechBackendAdapter] = {
    "vibevoice": SpeechBackendAdapter(
        backend_id="wangp-vibevoice-7b-planned",
        model_type="planned/vibevoice_7b",
        operations=frozenset(("speech", "voice_clone")),
        vram_profiles=frozenset(("24gb", "48gb")),
        max_segment_chars=1200,
        max_segment_duration_s=30.0,
        reference_counts=frozenset((0, 1, 2)),
    ),
    "chatterbox": SpeechBackendAdapter(
        backend_id="wangp-chatterbox-planned",
        model_type="planned/chatterbox",
        operations=frozenset(("speech",)),
        vram_profiles=frozenset(("12gb", "16gb", "24gb", "48gb")),
        max_segment_chars=600,
        max_segment_duration_s=20.0,
        reference_counts=frozenset((0,)),
    ),
}


def backend_for(family) -> SpeechBackendAdapter:
    try:
        return BACKENDS[family.value]
    except (AttributeError, KeyError) as exc:
        raise ValueError(f"unknown speech family {family!r}") from exc


def model_id(family, preset) -> str:
    return f"{family.value}/{preset.value}"


__all__ = ["BACKENDS", "SpeechBackendAdapter", "backend_for", "model_id"]
