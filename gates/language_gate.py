"""Language-class gate — two-class field split for DSPy signatures.

ADOPT of the shuohao-skills language-split field contract
(docs/extraction/shuohao-skills/language-split-contract.md — the
extraction doc IS the design source of truth; profile-pass.md:16
machine-fields-always-English, :26 evidence-never-translated,
CHANGELOG:440-458 bidirectional language gates
"设定英文混进中文…都拦").

Classes:
- ENGINE_BOUND: fields the render/QC engines consume — LOCKED
  ENGLISH ("机器字段不跟随 lang——图像模型和 TTS 引擎吃英文最稳").
  Non-ASCII content fails LOUDLY.
- HUMAN_REVIEW: fields humans read — follow the workflow language,
  ANY language accepted; when a workflow_lang is scoped, mixing the
  wrong language is flagged (bidirectional, like theirs).
- EVIDENCE: verbatim source language, NEVER translated
  ("引文永远保持原文语言——它是证据，翻译了就不是证据了"); checked
  against source text when available, loud typed skip when not.

Naming rule (CHANGELOG:794 promptZh→promptLocal lesson): never name
a multilingual field after one language — pinned by test.

ZERO-MODEL: no LLM, no network. Deterministic script/introspection.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

__all__ = [
    "LanguageViolation", "LanguageGateError", "check_language_class",
    "FIELD_CLASSES", "ENGINE_BOUND", "HUMAN_REVIEW", "EVIDENCE",
    "EMPTY_TEXT", "NO_SOURCE",
]

ENGINE_BOUND = "engine_bound"
HUMAN_REVIEW = "human_review"
EVIDENCE = "evidence"

EMPTY_TEXT = "empty_text"
NO_SOURCE = "no_source"

# Field-class contract for every wangp-dspy DSPy output signature.
# RenderBrief: ALL fields engine-bound — they feed the WanGP render
# prompt verbatim (subject/motion/camera/style/audio_direction/
# negatives/identity_lock are prompt fragments, not review prose).
# ProfileSelector.decision: machine-parsed JSON — engine-bound.
# RenderQC.critique: machine-parsed JSON — engine-bound;
# RenderQC notes: the one-sentence human summary — human-review.
FIELD_CLASSES = {
    "RenderBrief": {
        "subject": ENGINE_BOUND,
        "motion": ENGINE_BOUND,
        "camera": ENGINE_BOUND,
        "style": ENGINE_BOUND,
        "audio_direction": ENGINE_BOUND,
        "negatives": ENGINE_BOUND,
        "identity_lock": ENGINE_BOUND,
    },
    "ProfileSelector": {
        "decision": ENGINE_BOUND,
    },
    "RenderQC": {
        "critique": ENGINE_BOUND,
        "notes": HUMAN_REVIEW,
    },
}


class LanguageGateError(ValueError):
    """Typed gate failure. kind=EMPTY_TEXT / NO_SOURCE for the
    loud-skip cases; violation failures carry .violations."""

    def __init__(self, message: str, *, kind: str | None = None,
                 violations: list | None = None):
        self.kind = kind
        self.violations = violations or []
        super().__init__(message)


@dataclass(frozen=True)
class LanguageViolation:
    field_class: str
    matched_text: str
    reason: str

    def __str__(self) -> str:  # pragma: no cover
        return (f"{self.field_class} language violation: "
                f"{self.reason}")


# non-ASCII letters/markers — engine-bound fields must be plain
# English (ASCII punctuation like em-dashes is tolerated; letters
# beyond Latin are not)
_NON_ASCII_RE = re.compile(r"[^\x00-\x7F]")
_NON_ASCII_WORD_RE = re.compile(
    r"[^\x00-\x7F\W_]+")   # runs of non-ASCII word characters

# for the bidirectional human-review check: does the text contain
# ASCII-word content (English words)?
_ASCII_WORD_RE = re.compile(r"[A-Za-z]{2,}")

# CJK detection for scoped-lang checks (extend per observed cases —
# measure-then-threshold, same stance as common-actions)
_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff]")


def _is_mostly_target_lang(text: str, workflow_lang: str) -> bool:
    if workflow_lang == "zh":
        # scoped zh: text is compliant when it has CJK and its ASCII
        # words are incidental (brand tokens etc. would be evidence
        # class anyway)
        return bool(_CJK_RE.search(text))
    return True  # en scope: English presence is the target


def check_language_class(text: str, *, field_class: str,
                         workflow_lang: str | None = None,
                         source_text: str | None = None) -> list:
    """Return LanguageViolation list for *text* in a field of the
    given class (empty = clean).

    Pure, deterministic, offline. Empty text raises typed loud skip.
    """
    if not isinstance(text, str) or not text.strip():
        raise LanguageGateError(
            "language gate: text is EMPTY/blank — nothing to check "
            "(loud skip)", kind=EMPTY_TEXT)

    if field_class == ENGINE_BOUND:
        hits = _NON_ASCII_WORD_RE.findall(text)
        if hits:
            runs = ", ".join(repr(h) for h in hits[:3])
            return [LanguageViolation(
                field_class=ENGINE_BOUND, matched_text=runs,
                reason=(f"non-English text {runs} in an engine-bound "
                        "field — engine fields are LOCKED ENGLISH "
                        "(profile-pass.md:16); translate or rewrite"))]
        return []

    if field_class == HUMAN_REVIEW:
        if workflow_lang is None:
            return []   # unscoped: any language accepted
        # bidirectional scoped check (like theirs): mixing the
        # non-target language is flagged
        if workflow_lang == "zh" and _ASCII_WORD_RE.search(text) \
                and _CJK_RE.search(text):
            en_runs = ", ".join(
                m.group(0) for m in
                _ASCII_WORD_RE.finditer(text))[:60]
            return [LanguageViolation(
                field_class=HUMAN_REVIEW, matched_text=en_runs,
                reason=(f"English text {en_runs!r} mixed into a "
                        f"lang-scoped ({workflow_lang}) human-review "
                        "field — bidirectional gate "
                        "(设定英文混进中文…都拦)"))]
        return []

    if field_class == EVIDENCE:
        if source_text is None:
            raise LanguageGateError(
                "language gate: EVIDENCE field checked without "
                "source text — verbatim comparison impossible (loud "
                "skip; evidence is never translated, so a source is "
                "required)", kind=NO_SOURCE)
        norm = lambda s: "".join(
            ch for ch in unicodedata.normalize("NFC", s)
            if not unicodedata.combining(ch)).strip()
        if norm(text) != norm(source_text):
            return [LanguageViolation(
                field_class=EVIDENCE, matched_text=text[:40],
                reason=("evidence text differs from source — "
                        "evidence is verbatim source language, never "
                        "translated (profile-pass.md:26)"))]
        return []

    raise LanguageGateError(
        f"unknown field class {field_class!r} "
        f"({ENGINE_BOUND}|{HUMAN_REVIEW}|{EVIDENCE})")
