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
from typing import Callable, Mapping, Optional, Tuple
from statistics import median


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
    mouth_sync: Optional[float]
    mouth_activity: float
    av_sync_verified: bool
    speaker_mouth_bboxes: Tuple[Tuple[float, float, float, float], ...]
    speaker_mouth_bbox: Tuple[float, float, float, float]
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
    reference_image_path: Optional[str] = None,
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
        kwargs = dict(video_path=video_path, expected_speaker=expected_speaker,
                      expected_action=expected_action)
        if reference_image_path is not None:
            kwargs["reference_image_path"] = reference_image_path
        raw = judge(**kwargs)
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
    raw = dict(raw)
    if "mouth_activity" not in raw and "mouth_sync" in raw:
        raw["mouth_activity"] = raw["mouth_sync"]
    values = {}
    for name in ("mouth_activity", "action_match", "speaker_attribution"):
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
    bboxes_raw = raw.get("speaker_mouth_bboxes")
    if (not isinstance(bboxes_raw, (list, tuple)) or len(bboxes_raw) != 3
            or any(not isinstance(item, (list, tuple)) or len(item) != 4
                   for item in bboxes_raw)):
        raise VisionJudgeError(
            "vision result must include three speaker_mouth_bboxes [x,y,w,h]",
            scores=values, raw_response=raw_response)
    try:
        bboxes = tuple(
            tuple(float(value) for value in bbox) for bbox in bboxes_raw)
    except (TypeError, ValueError) as exc:
        raise VisionJudgeError(
            "speaker_mouth_bbox values must be numeric",
            scores=values, raw_response=raw_response) from exc
    for bbox in bboxes:
        if (not all(math.isfinite(value) for value in bbox)
                or any(value < 0.0 or value > 1.0 for value in bbox)
                or bbox[2] <= 0.0 or bbox[3] <= 0.0
                or bbox[0] + bbox[2] > 1.0001
                or bbox[1] + bbox[3] > 1.0001):
            raise VisionJudgeError(
                "speaker_mouth_bboxes must be normalized and fit inside the frame",
                scores=values, raw_response=raw_response)
    centers = [(bbox[0] + bbox[2] / 2.0, bbox[1] + bbox[3] / 2.0)
               for bbox in bboxes]
    if (max(x for x, _ in centers) - min(x for x, _ in centers) > 0.03
            or max(y for _, y in centers) - min(y for _, y in centers) > 0.03):
        raise VisionJudgeError(
            "speaker_mouth_bboxes lack spatial consensus",
            scores=values, raw_response=raw_response)
    bbox = tuple(median(bbox[index] for bbox in bboxes) for index in range(4))
    # mouth_activity is descriptive evidence only. A three-still judge cannot
    # infer temporal speech motion reliably; SyncNet owns that blocking gate.
    passed = min(values["action_match"],
                 values["speaker_attribution"]) >= float(pass_bar)
    evidence = VisionJudgeEvidence(
        video_path=video_path, expected_speaker=expected_speaker,
        expected_action=expected_action, pass_bar=float(pass_bar),
        passed=passed, mouth_sync=None, av_sync_verified=False,
        speaker_mouth_bboxes=bboxes,
        speaker_mouth_bbox=bbox,
        notes="Still-image visual QC only; phonetic AV synchrony is unmeasured. " + str(raw.get("notes", "")), raw_response=(
            str(raw_response) if raw_response is not None else None), **values)
    if not passed:
        raise VisionJudgeError(
            "visual gate failed: mouth/action/speaker attribution below pass bar",
            scores=values, raw_response=raw_response)
    return evidence


__all__ = ["VisionJudgeError", "VisionJudgeEvidence", "run_vision_judge"]
