"""Whisper transcript gates for Ref2VA continuation audio.

The gate intentionally has no model dependency.  A production caller injects
the repository's Whisper runner (local or remote); tests inject a deterministic
transcriber.  Both pre-render guide audio and post-render/remux audio must pass
the same word-overlap bar before a cut is eligible for QC.
"""
from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from typing import Callable, Mapping, Optional

from predict.continuation_lane import transcript_match_score


class WhisperGateError(ValueError):
    """Typed, fail-closed transcript gate rejection."""


@dataclass(frozen=True)
class WhisperGateEvidence:
    phase: str
    audio_path: str
    intended_text: str
    transcript: str
    score: float
    pass_bar: float
    passed: bool

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def run_whisper_gate(
    audio_path: str,
    intended_text: str,
    *,
    transcriber: Optional[Callable[[str], object]],
    phase: str,
    pass_bar: float = 0.5,
) -> WhisperGateEvidence:
    """Transcribe one artifact and compare it to the intended line."""
    if phase not in {"pre", "post"}:
        raise WhisperGateError("phase: must be 'pre' or 'post'")
    if not isinstance(audio_path, str) or not audio_path:
        raise WhisperGateError(f"{phase}_audio_path: required")
    if not isinstance(intended_text, str) or not intended_text.strip():
        raise WhisperGateError("intended_text: required")
    if not math.isfinite(float(pass_bar)) or not 0.0 <= float(pass_bar) <= 1.0:
        raise WhisperGateError("pass_bar: must be between 0 and 1")
    if transcriber is None:
        raise WhisperGateError(
            f"{phase}: Whisper transcriber is not wired; refusing ungated audio")
    try:
        raw = transcriber(audio_path)
    except Exception as exc:
        raise WhisperGateError(f"{phase}: Whisper transcription failed: {exc}") from exc
    if isinstance(raw, Mapping):
        transcript = raw.get("text", "")
    else:
        transcript = raw
    if not isinstance(transcript, str):
        raise WhisperGateError(
            f"{phase}: transcriber must return text or {{'text': text}}")
    score = transcript_match_score(transcript, intended_text)
    passed = score >= float(pass_bar)
    evidence = WhisperGateEvidence(
        phase=phase, audio_path=audio_path, intended_text=intended_text,
        transcript=transcript, score=round(score, 3), pass_bar=float(pass_bar),
        passed=passed)
    if not passed:
        raise WhisperGateError(
            f"{phase}: transcript score {score:.3f} below pass bar "
            f"{float(pass_bar):.3f}")
    return evidence


__all__ = ["WhisperGateError", "WhisperGateEvidence", "run_whisper_gate"]
