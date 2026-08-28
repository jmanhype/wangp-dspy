"""S2 diarization consumption surface (WD-j9nx/S2).

The repo CONSUMES out-of-repo speaker-diarization output: a versioned
JSON timeline schema (per-speaker segments with start/end/speaker id),
a deterministic validator that rejects malformed timelines with typed
errors naming the rule (R1-R6), and a deterministic converter to
`<d>Name</d>` speaker-attribution blocks compatible with the G5 prompt
contract (S1) — the bridge into S3's `<d>` speaker gate.

Binding constraint: the two banned ASR/diarization packages NEVER appear in repo code
paths (license + operator rule). This module imports neither; it is
pure dict logic, zero-model, no I/O in the validator.

Determinism invariant: same input bytes -> same output bytes (no
timestamps, no randomness, no dict-order leakage). Proven by test.

Spec: docs/specs/s2-diarization.md · Plan: docs/plans/s2-diarization.md
Maestro audio_analysis.py:675-780 is IDEA-ONLY reference (non-commercial
— never vendored); this schema is our own design.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

__all__ = [
    "DIARIZATION_SCHEMA_VERSION", "FLOAT_TOL", "DiarizationError",
    "SpeakerBlock", "validate_diarization",
    "diarization_to_speaker_blocks", "render_attribution",
]

DIARIZATION_SCHEMA_VERSION = 1

# float tolerance for boundary comparisons (R5 end <= duration_sec)
FLOAT_TOL = 1e-6

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")

_TOP_LEVEL_KEYS = frozenset(
    ("schema_version", "audio_sha256", "duration_sec", "speakers",
     "segments"))


class DiarizationError(ValueError):
    """Typed rejection. Every message names the failing rule id."""


@dataclass(frozen=True)
class SpeakerBlock:
    """One segment of a validated timeline, converted 1:1."""
    start: float
    end: float
    speaker: str
    text_hint: str = ""


def _reject(rule: str, msg: str) -> None:
    raise DiarizationError(f"{rule}: {msg}")


def validate_diarization(doc: dict) -> None:
    """Validate one diarization timeline doc against schema v1.

    Pure function, no I/O. Raises DiarizationError naming the first
    failing rule (R1-R6 + unknown-key discipline).
    """
    if not isinstance(doc, dict):
        _reject("R0", f"timeline must be an object, got {type(doc).__name__}")

    # unknown top-level keys rejected (forward-compat discipline: a
    # schema change must bump schema_version, not sneak keys in)
    unknown = set(doc) - _TOP_LEVEL_KEYS
    if unknown:
        _reject("R0", f"unknown top-level key(s): {sorted(unknown)}")

    # R1: schema_version must be int == 1 (no floats, no strings)
    sv = doc.get("schema_version")
    if not isinstance(sv, int) or isinstance(sv, bool) or sv != DIARIZATION_SCHEMA_VERSION:
        _reject("R1", f"schema_version must be int == "
                      f"{DIARIZATION_SCHEMA_VERSION}, got {sv!r}")

    # R2: audio_sha256 must be 64 lowercase hex chars
    sha = doc.get("audio_sha256")
    if not isinstance(sha, str) or not _SHA_RE.match(sha):
        _reject("R2", "audio_sha256 must be 64 lowercase hex chars")

    # R3: duration_sec must be a positive finite number
    dur = doc.get("duration_sec")
    if (not isinstance(dur, (int, float)) or isinstance(dur, bool)
            or not math.isfinite(dur) or dur <= 0):
        _reject("R3", "duration_sec must be a positive finite number")

    # R4: speakers must be a non-empty list of unique non-empty strings
    speakers = doc.get("speakers")
    if (not isinstance(speakers, list) or not speakers
            or any(not isinstance(s, str) or not s.strip()
                   for s in speakers)):
        _reject("R4", "speakers must be a non-empty list of unique "
                      "non-empty strings")
    if len(set(speakers)) != len(speakers):
        _reject("R4", "speakers must be unique")
    assert isinstance(speakers, list)

    # R5: segments — list; per-segment bounds + membership + text type
    segments = doc.get("segments")
    if not isinstance(segments, list):
        _reject("R5", "segments must be a list")
    assert isinstance(segments, list) and isinstance(dur, (int, float))
    speaker_set = set(speakers)
    for i, seg in enumerate(segments):
        if not isinstance(seg, dict):
            _reject("R5", f"segment[{i}] must be an object")
        start = seg.get("start")
        end = seg.get("end")
        if (not isinstance(start, (int, float)) or isinstance(start, bool)
                or not isinstance(end, (int, float)) or isinstance(end, bool)
                or not math.isfinite(start) or not math.isfinite(end)):
            _reject("R5", f"segment[{i}] start/end must be finite numbers")
        if start < 0:
            _reject("R5", f"segment[{i}] start must be >= 0, got {start}")
        if start >= end:
            _reject("R5", f"segment[{i}] requires start < end "
                          f"({start} >= {end})")
        if end > dur + FLOAT_TOL:
            _reject("R5", f"segment[{i}] end {end} exceeds duration_sec "
                          f"{dur}")
        spk = seg.get("speaker")
        if spk not in speaker_set:
            _reject("R5", f"segment[{i}] speaker {spk!r} not in speakers")
        if "text" in seg and not isinstance(seg["text"], str):
            _reject("R5", f"segment[{i}] text must be a string when present")

    # R6: sorted by start ascending (ties broken by end); no overlaps
    # (same-speaker overlap also rejected — one contiguous run per
    # speaker interval; merging is the external tool's job)
    for i in range(len(segments) - 1):
        a, b = segments[i], segments[i + 1]
        if (a["start"], a["end"]) > (b["start"], b["end"]):
            _reject("R6", f"segments[{i}]..[{i+1}] not sorted by start "
                          "(ties broken by end)")
        if a["end"] > b["start"] + FLOAT_TOL:
            _reject("R6", f"segments[{i}]..[{i+1}] overlap "
                          f"({a['end']} > {b['start']})")


def diarization_to_speaker_blocks(doc: dict) -> list:
    """Convert a validated timeline to SpeakerBlocks, 1:1, order
    preserved. Re-validates defensively (single authority — the
    converter raises the same typed errors on invalid input)."""
    validate_diarization(doc)
    return [
        SpeakerBlock(
            start=float(seg["start"]), end=float(seg["end"]),
            speaker=seg["speaker"],
            text_hint=seg.get("text", "") or "")
        for seg in doc["segments"]
    ]


def render_attribution(blocks: list) -> str:
    """Render SpeakerBlocks as `<d>Name</d>` tokens — EXACTLY the shape
    G5 accepts (bracketed/parenthesized labels are rejected by G5).
    One token per line, block order preserved. Deterministic."""
    return "\n".join(f"<d>{b.speaker}</d>" for b in blocks)
