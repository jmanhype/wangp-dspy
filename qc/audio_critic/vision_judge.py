"""Integrated per-cut vision judge contract.

The repository does not assume a particular VLM.  A caller injects a judge
that receives the rendered video and typed speaker/action expectations.  The
adapter's result is normalized into durable evidence and fails closed when
the mouth or action attribution does not meet the configured bar.
"""
from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from typing import Callable, Mapping, Optional


class VisionJudgeError(ValueError):
    """Typed rejection of absent or contradictory visual evidence."""


@dataclass(frozen=True)
class VisionJudgeEvidence:
    video_path: str
    expected_speaker: str
    expected_action: str
    mouth_sync: float
    action_match: float
    speaker_attribution: float
    pass_bar: float
    passed: bool
    notes: str = ""

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def run_vision_judge(
    video_path: str,
    *,
    expected_speaker: str,
    expected_action: str,
    judge: Optional[Callable],
    pass_bar: float = 0.7,
) -> VisionJudgeEvidence:
    if not isinstance(video_path, str) or not video_path:
        raise VisionJudgeError("video_path: required")
    if not expected_speaker or not expected_action:
        raise VisionJudgeError("expected_speaker and expected_action are required")
    if judge is None:
        raise VisionJudgeError("vision judge is not wired; refusing ungated video")
    if not math.isfinite(float(pass_bar)) or not 0.0 <= float(pass_bar) <= 1.0:
        raise VisionJudgeError("pass_bar: must be between 0 and 1")
    try:
        raw = judge(video_path=video_path,
                    expected_speaker=expected_speaker,
                    expected_action=expected_action)
    except Exception as exc:
        raise VisionJudgeError(f"vision judge failed: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise VisionJudgeError("vision judge must return a mapping")
    values = {}
    for name in ("mouth_sync", "action_match", "speaker_attribution"):
        try:
            value = float(raw[name])
        except (KeyError, TypeError, ValueError) as exc:
            raise VisionJudgeError(f"vision result missing numeric {name}") from exc
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise VisionJudgeError(f"vision result {name} must be 0..1, got {value!r}")
        values[name] = value
    passed = min(values.values()) >= float(pass_bar)
    evidence = VisionJudgeEvidence(
        video_path=video_path, expected_speaker=expected_speaker,
        expected_action=expected_action, pass_bar=float(pass_bar),
        passed=passed, notes=str(raw.get("notes", "")), **values)
    if not passed:
        raise VisionJudgeError(
            "visual gate failed: mouth/action/speaker attribution below pass bar")
    return evidence


__all__ = ["VisionJudgeError", "VisionJudgeEvidence", "run_vision_judge"]
