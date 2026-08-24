"""RenderQC — VLM-scored output gate with genre thresholds (WD-hjn4).

Consumes VLM critiques (coherence, brief_adherence, concept_encoding,
each 0-10) from a CritiqueRecord, judges them against per-genre
operator-tunable thresholds, and emits a typed verdict
(pass/revise/reject). CONCEPT_ENCODING_FAILURE (informed-good +
blind-bad pattern) earns exactly ONE anchored revision, then a typed
escalation to human — never silent.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping

import dspy

from predict.profile_selector import ProfileDecision
from predict.prompt_director import RenderBrief

CRITIQUE_FIELDS = ("coherence", "brief_adherence", "concept_encoding")

# Operator-tunable genre thresholds (minimum acceptable score across
# the critique fields; comedy needs tight concept encoding, surreal
# tolerates looser coherence). MappingProxyType: read-only at runtime;
# retuning = source edit (GLM F1).
GENRE_THRESHOLDS: Mapping = MappingProxyType({
    "comedy": 7.0,
    "edu": 8.0,
    "music": 5.0,
    "surreal": 4.5,
})

# A score this far below threshold is beyond revision -> reject.
REJECT_FLOOR_RATIO = 0.5  # < 50% of the genre threshold -> reject

# informed-vs-blind concept_encoding gap that signals the model encoded
# the PROMPT TEXT (visible to the informed judge) but not the CONCEPT
CEF_GAP = 5.0
CEF_BLIND_BELOW = 4.0

MAX_REVISIONS = 1


class ConceptEncodingFailureError(Exception):
    """Typed escalation: one revision was already granted for a
    CONCEPT_ENCODING_FAILURE and it persists — a human must decide."""


class Verdict(Enum):
    PASS = "pass"
    REVISE = "revise"
    REJECT = "reject"


@dataclass(frozen=True)
class CritiqueRecord:
    coherence: float
    brief_adherence: float
    concept_encoding: float
    scores: dict
    notes: str = ""

    def __post_init__(self) -> None:
        for f in CRITIQUE_FIELDS:
            v = getattr(self, f)
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                raise ValueError(f"{f} must be numeric")
            if not 0.0 <= v <= 10.0:
                raise ValueError(f"{f} must be within 0-10, got {v}")


@dataclass(frozen=True)
class QCVerdict:
    verdict: Verdict
    reason: str
    anchor_field: str | None = None
    scores: dict | None = None


class RenderQCSignature(dspy.Signature):
    """Critique a rendered video clip against its brief and profile.

    Output ONE JSON object with EXACTLY these keys:
      coherence: 0-10, does the clip hold together visually
      brief_adherence: 0-10, does it match subject/motion/camera/style
      concept_encoding: 0-10, is the core concept legible on screen
      scores: {"coherence": n, "brief_adherence": n,
               "concept_encoding": n}
      notes: one sentence

    Judge strictly; output the JSON object only.
    """
    subject: str = dspy.InputField()
    motion: str = dspy.InputField()
    camera: str = dspy.InputField()
    style: str = dspy.InputField()
    model: str = dspy.InputField()
    shot_length_frames: int = dspy.InputField()
    # QB1: the gate critiques the RENDERED material itself (path to the
    # produced video — the VLM provider resolves frames from it), not a
    # text-only description of the expectation.
    video: str = dspy.InputField(
        desc="path to the rendered video clip to critique")
    critique: str = dspy.OutputField(
        desc="JSON: coherence, brief_adherence, concept_encoding, "
             "scores, notes")


class RenderQC(dspy.ChainOfThought):
    """Threshold gate over VLM critiques for one genre."""

    def __init__(self, genre: str):
        if genre not in GENRE_THRESHOLDS:
            raise ValueError(
                f"unknown genre {genre!r}; known: "
                f"{sorted(GENRE_THRESHOLDS)}")
        super().__init__(RenderQCSignature)
        self.genre = genre

    # ── threshold judgment ───────────────────────────────────────────

    def judge(self, critique: CritiqueRecord) -> QCVerdict:
        threshold = GENRE_THRESHOLDS[self.genre]
        scores = {f: getattr(critique, f) for f in CRITIQUE_FIELDS}
        worst_field, worst = min(scores.items(), key=lambda kv: kv[1])
        if worst >= threshold:
            return QCVerdict(
                verdict=Verdict.PASS,
                reason=f"all critique fields >= {threshold} for genre "
                       f"{self.genre!r}", scores=scores)
        if worst < threshold * REJECT_FLOOR_RATIO:
            return QCVerdict(
                verdict=Verdict.REJECT,
                reason=f"{worst_field}={worst} is far below the "
                       f"{self.genre} threshold {threshold}",
                scores=scores)
        return QCVerdict(
            verdict=Verdict.REVISE,
            reason=f"{worst_field}={worst} below {self.genre} "
                   f"threshold {threshold}",
            anchor_field=worst_field, scores=scores)

    # ── concept-encoding failure (informed-good + blind-bad) ────────

    def detect_concept_failure(self, informed: CritiqueRecord,
                               blind: CritiqueRecord) -> bool:
        return (informed.concept_encoding - blind.concept_encoding
                >= CEF_GAP and blind.concept_encoding < CEF_BLIND_BELOW)

    def request_revision(self, failure_detected: bool,
                         attempt: int) -> QCVerdict:
        if not failure_detected:
            raise ValueError("no concept-encoding failure to revise")
        if attempt > MAX_REVISIONS:
            raise ConceptEncodingFailureError(
                "CONCEPT_ENCODING_FAILURE persists after the single "
                "allowed revision — escalating to human review")
        # single revision anchored on the one failing field
        return QCVerdict(
            verdict=Verdict.REVISE,
            reason="CONCEPT_ENCODING_FAILURE: informed-good + "
                   "blind-bad — one anchored revision allowed",
            anchor_field="concept_encoding")

    # ── end-to-end ───────────────────────────────────────────────────

    def run(self, brief: RenderBrief,
            decision: ProfileDecision, video: str = "") -> QCVerdict:
        out = super().forward(
            subject=brief.subject, motion=brief.motion,
            camera=brief.camera, style=brief.style,
            model=decision.model,
            shot_length_frames=decision.shot_length_frames,
            video=video)
        critique = _parse_critique(out.critique)
        return self.judge(critique)


def _parse_critique(raw: str) -> CritiqueRecord:
    try:
        doc = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"LM output is not valid JSON: {raw!r}") from exc
    if not isinstance(doc, dict):
        raise ValueError(f"critique JSON must be an object, got {doc!r}")
    missing = [k for k in CRITIQUE_FIELDS if k not in doc]
    if missing:
        raise ValueError(f"critique JSON missing keys: {missing}")
    return CritiqueRecord(
        coherence=float(doc["coherence"]),
        brief_adherence=float(doc["brief_adherence"]),
        concept_encoding=float(doc["concept_encoding"]),
        scores=doc.get("scores") or {},
        notes=str(doc.get("notes", "")),
    )
