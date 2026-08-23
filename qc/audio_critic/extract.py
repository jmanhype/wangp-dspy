"""Deterministic prose→structured extractor (slice 1).

Contract: docs/PROPOSAL_audio_critic_service.md — "for music,
initially a regex/keyword extractor tuned on the existing critique
corpus in sgflix_audio_factory/critiques/, which is real training
data for the parser". The recorded fixtures in tests/.../fixtures/
are that corpus (neonhearts batches 001-003, fetched from the 3090).

Deterministic: same prose in, same structured out. Score 0-40 via
"<n> out of 40" / "score of N" patterns; flags via keyword mapping
onto the profile's CLOSED vocabulary. Unparseable score => parse_ok
False with a neutral score (0) — never invented numbers.
"""
from __future__ import annotations

import re

from qc.audio_critic.profiles import PROFILES
from qc.audio_critic.schema import AudioCriticError

# score patterns observed in the corpus:
#   "rate ... as 35 out of 40", "approximately 38 out of 40"
_SCORE_RE = re.compile(
    r"(?:score|rate|rating)[^0-9]{0,40}?(\d{1,2})\s+out\s+of\s+(\d+)",
    re.IGNORECASE)
# fallback: any "<n> out of 40" without a leading verb
_BARE_RE = re.compile(r"(\d{1,2})\s+out\s+of\s+40", re.IGNORECASE)

# keyword -> flag mapping (music profile; prose words are matched
# case-insensitively as substrings, first hit per flag wins)
_MUSIC_KEYWORDS = [
    ("timing_drift", ("off-beat", "off beat", "offbeat",
                      "not on-beat", "timing issue")),
    ("muddy_vocals", ("unclear vocal", "muddy", "clarity of the "
                      "vocals is poor")),
    ("background_noise", ("background noise", "noises")),
    ("weak_flow", ("poor flow", "flow is weak")),
    ("good_clarity", ("clarity of the vocals is good",
                      "vocals are clearer", "vocals are now clearer",
                      "clear pitch")),
]


def extract_structured(profile: str, prose: str) -> dict:
    """Deterministic extraction of structured fields from critique
    prose. Returns a dict WITHOUT schema/model (build_critique
    assembles the full record). parse_ok False when no score was
    found — the neutral fallback keeps the record schema-valid."""
    if profile not in PROFILES:
        raise AudioCriticError(f"unknown profile: {profile!r}")
    if not isinstance(prose, str):
        raise AudioCriticError("prose must be a string")
    prof = PROFILES[profile]
    lo, hi = prof["score_scale"]

    score, parse_ok = None, True
    m = _SCORE_RE.search(prose) or _BARE_RE.search(prose)
    if m:
        score = int(m.group(1))
    if score is None:
        score, parse_ok = lo, False  # neutral, flagged not-parsed
    score = max(lo, min(hi, score))

    flags = []
    lowered = prose.lower()
    if profile == "music":
        for flag, keywords in _MUSIC_KEYWORDS:
            if any(k in lowered for k in keywords):
                flags.append(flag)

    # decision: threshold heuristic, documented as advisory (the
    # music lane's keeper/reject gate is rule_critic's, unchanged)
    if profile == "music":
        span = hi - lo
        decision = ("keeper_candidate"
                    if score >= lo + span * 0.5 else "reject")
    else:
        span = hi - lo
        if score >= lo + span * 0.6:
            decision = "pass"
        elif score >= lo + span * 0.35:
            decision = "revise"
        else:
            decision = "reject"

    # reason: first sentence-ish chunk, bounded
    first = re.split(r"(?<=[.!?])\s", prose.strip(), maxsplit=1)[0]
    reason = first if len(first) <= 300 else first[:297] + "..."

    return {
        "profile": profile,
        "score": score,
        "score_scale": list(prof["score_scale"]),
        "flags": flags,
        "reason": reason or "(no reason extracted)",
        "decision": decision,
        "parse_ok": parse_ok,
    }
