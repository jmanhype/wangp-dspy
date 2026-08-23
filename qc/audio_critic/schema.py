"""audio-critic/1 — shared output schema (slice 1, pure).

Contract: docs/PROPOSAL_audio_critic_service.md. Single source of
truth imported by BOTH the 3090-side service and the client judges.
Typed AudioCriticError on every validation failure — never a raw
crash, never silent prose passthrough.
"""
from __future__ import annotations

SCHEMA_NAME = "audio-critic/1"


class AudioCriticError(ValueError):
    """Typed schema/validation failure. Messages name the field;
    untrusted values are not echoed."""


def validate_critique(record: dict) -> dict:
    """Validate an audio-critic/1 record against its PROFILE.

    Checks: schema string, required fields, profile known, score within
    the profile's bounds, score_scale echoes the profile, flags drawn
    from the profile's CLOSED vocabulary, decision in the profile's
    enum, parse_ok boolean, model non-empty string.
    Returns the record unchanged on success.
    """
    from qc.audio_critic.profiles import PROFILES

    if not isinstance(record, dict):
        raise AudioCriticError("critique must be an object")
    if record.get("schema") != SCHEMA_NAME:
        raise AudioCriticError(
            f"schema must be {SCHEMA_NAME!r}")
    required = ("profile", "score", "score_scale", "flags", "reason",
                "decision", "model", "parse_ok")
    for f in required:
        if f not in record:
            raise AudioCriticError(f"missing field: {f}")
    profile = record["profile"]
    if profile not in PROFILES:
        raise AudioCriticError(f"unknown profile: {profile!r}")
    prof = PROFILES[profile]

    score = record["score"]
    if isinstance(score, bool) or not isinstance(score, int):
        raise AudioCriticError("score must be an int")
    lo, hi = prof["score_scale"]
    if not (lo <= score <= hi):
        raise AudioCriticError(
            f"score {score} outside profile bounds {[lo, hi]}")

    if list(record["score_scale"]) != list(prof["score_scale"]):
        raise AudioCriticError(
            "score_scale must echo the profile's "
            f"{prof['score_scale']}")

    flags = record["flags"]
    if not isinstance(flags, list) or \
            not all(isinstance(f, str) for f in flags):
        raise AudioCriticError("flags must be a list of strings")
    vocab = set(prof["flags"])
    unknown = [f for f in flags if f not in vocab]
    if unknown:
        raise AudioCriticError(
            f"flags not in the closed vocabulary for profile "
            f"{profile!r}: {sorted(unknown)} (allowed: {sorted(vocab)})")

    if record["decision"] not in prof["decisions"]:
        raise AudioCriticError(
            f"decision {record['decision']!r} not in the enum for "
            f"profile {profile!r}: {list(prof['decisions'])}")

    if not isinstance(record["reason"], str) or \
            not record["reason"].strip():
        raise AudioCriticError("reason must be a non-empty string")
    if not isinstance(record["model"], str) or \
            not record["model"].strip():
        raise AudioCriticError("model must be a non-empty string")
    if not isinstance(record["parse_ok"], bool):
        raise AudioCriticError("parse_ok must be a boolean")
    return record


def build_critique(structured: dict, *, model: str) -> dict:
    """Assemble + validate a full audio-critic/1 record from an
    extractor's structured output. Raises AudioCriticError if the
    assembled record is invalid — no silent defaults beyond the
    documented extractor fallbacks."""
    record = dict(structured)
    record["schema"] = SCHEMA_NAME
    record["model"] = model
    return validate_critique(record)
