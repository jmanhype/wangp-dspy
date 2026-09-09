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
    """Typed rejection of absent or contradictory visual evidence.

    ``scores`` and ``raw_response`` preserve audit evidence when the gate
    rejects a cut; without them the failure cannot be replayed offline.
    """

    def __init__(self, message: str, *, scores: Optional[Mapping] = None,
                 raw_response: Optional[str] = None):
        super().__init__(message)
        self.scores = dict(scores or {})
        self.raw_response = (str(raw_response)
                             if raw_response is not None else None)


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
    raw_response: Optional[str] = None

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
    except VisionJudgeError:
        raise
    except Exception as exc:
        raise VisionJudgeError(
            f"vision judge failed: {exc}",
            scores=getattr(exc, "scores", None),
            raw_response=getattr(exc, "raw_response", None),
        ) from exc
    if not isinstance(raw, Mapping):
        raise VisionJudgeError("vision judge must return a mapping")
    raw_response = raw.get("raw_response")
    values = {}
    for name in ("mouth_sync", "action_match", "speaker_attribution"):
        try:
            value = float(raw[name])
        except (KeyError, TypeError, ValueError) as exc:
            raise VisionJudgeError(
                f"vision result missing numeric {name}",
                scores=values, raw_response=raw_response) from exc
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise VisionJudgeError(
                f"vision result {name} must be 0..1, got {value!r}",
                scores=values, raw_response=raw_response)
        values[name] = value
    passed = min(values.values()) >= float(pass_bar)
    evidence = VisionJudgeEvidence(
        video_path=video_path, expected_speaker=expected_speaker,
        expected_action=expected_action, pass_bar=float(pass_bar),
        passed=passed, notes=str(raw.get("notes", "")), raw_response=(
            str(raw_response) if raw_response is not None else None), **values)
    if not passed:
        raise VisionJudgeError(
            "visual gate failed: mouth/action/speaker attribution below pass bar",
            scores=values, raw_response=raw_response)
    return evidence


__all__ = ["VisionJudgeError", "VisionJudgeEvidence", "run_vision_judge"]
