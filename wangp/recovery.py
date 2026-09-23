"""Typed OOM diagnosis and guidance that never mutates render semantics."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


OOM_SCHEMA = "wangp-dspy.oom-recovery/v1"
_OOM = re.compile(
    r"(?:out[ _-]of[ _-]memory|OutOfMemoryError|OUT_OF_MEMORY)", re.I
)
_CALIBRATIONS = (None, {"resolution": "512p", "frames": None},
                 {"resolution": "512p", "frames": "min"})


class RecoveryError(ValueError):
    """Typed rejection of malformed or non-OOM evidence."""

    def __init__(self, code: str, observed: str, remediation: str) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation


class OomEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    message: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    source: str = Field(min_length=1)


class RenderEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    model: str = Field(min_length=1)
    style_id: str = Field(min_length=1)
    resolution: str = Field(min_length=1)
    frames: int = Field(gt=0)
    calibration: Mapping[str, object] | None = None

    @model_validator(mode="after")
    def _known_calibration(self) -> "RenderEvidence":
        normalized = (
            None if self.calibration is None else dict(self.calibration)
        )
        if normalized not in _CALIBRATIONS:
            raise ValueError("calibration must be a known bounded-ladder value")
        return self


class OomRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = OOM_SCHEMA
    evidence: OomEvidence
    render: RenderEvidence
    command: tuple[str, ...] = Field(min_length=1)

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != OOM_SCHEMA:
            raise ValueError(f"unsupported recovery schema {value!r}; expected {OOM_SCHEMA}")
        return value


def load_oom_record(path: str | Path) -> OomRecord:
    source = Path(path).expanduser()
    payload = json.loads(source.read_text(encoding="utf-8"))
    return OomRecord.model_validate(payload)


def _next_calibration(current: Mapping[str, object] | None) -> dict[str, object] | None:
    index = _CALIBRATIONS.index(
        None if current is None else dict(current)
    )
    if index + 1 >= len(_CALIBRATIONS):
        return None
    value = _CALIBRATIONS[index + 1]
    return None if value is None else dict(value)


def diagnose_oom(record: OomRecord) -> dict[str, Any]:
    if _OOM.search(record.evidence.message) is None:
        raise RecoveryError(
            "OOM_NOT_DETECTED",
            f"recorded evidence has no OOM marker: {record.evidence.source}",
            "Use the matching renderer failure taxonomy; do not relabel an unrelated failure.",
        )
    next_step = _next_calibration(record.render.calibration)
    return {
        "schema_version": OOM_SCHEMA,
        "oom_detected": True,
        "evidence_source": record.evidence.source,
        "run_id": record.evidence.run_id,
        "strategy": "bounded-calibration",
        "calibration": next_step,
        "command": list(record.command),
        "preserves_model": True,
        "preserves_style": True,
        "gate_mutation": False,
        "automatic_change": False,
        "authorization_required": True,
    }


def render_recovery(payload: Mapping[str, Any]) -> str:
    value = dict(payload)
    command = subprocess.list2cmdline([str(item) for item in value["command"]])
    return "\n".join([
        f"oom_detected={str(value['oom_detected']).lower()}",
        f"strategy={value['strategy']}",
        f"calibration={json.dumps(value['calibration'], sort_keys=True)}",
        (
            f"preserves_model={str(value['preserves_model']).lower()} "
            f"preserves_style={str(value['preserves_style']).lower()}"
        ),
        (
            f"gate_mutation={str(value['gate_mutation']).lower()} "
            f"automatic_change={str(value['automatic_change']).lower()}"
        ),
        f"authorization_required={str(value['authorization_required']).lower()}",
        f"next command: {command}",
    ])


__all__ = [
    "OomRecord",
    "RecoveryError",
    "diagnose_oom",
    "load_oom_record",
    "render_recovery",
]
