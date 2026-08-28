"""Provenance-tier gate — canon citation vs (inferred) marker.

ADOPT of the shuohao-skills inferred-marker convention
(docs/extraction/shuohao-skills/inferred-marker-convention.md,
WD-oyti; GLM verdict ADOPT 7/7 zero overrides).

Two-tier provenance for identity/bible claims:
- CANON: a claim grounded in a canon citation (bible field / source
  quote) — no marker needed.
- INFERRED: a claim the writer had to fill to make the setting usable
  — carries EXACTLY ONE `(inferred)` marker ("只用一种标记，不要中英都加"
  — one marker per item, never both languages' markers).

There is NO unmarked middle ground: an identity claim that is neither
cited nor marked is a violation (the extraction's core prescription —
"invented bible details currently indistinguishable from canon at
generation time").

Placement rules (profile-pass.md:42-44):
1. Markers live in HUMAN fields only — they must NEVER appear inside
   machine prompts ("(inferred) 混进去会被画进画面" — the marker would
   literally get painted into the image). The stripping seam is
   host/wangp_adapter.brief_to_prompt() (handoff-to-prompt time); this
   module provides check_prompt_fields() for that assertion and
   strip_markers() for the removal itself.
2. Evidence can never be inferred — evidence stays verbatim (that is
   the language_gate EVIDENCE class's job; this gate covers the
   identity/appearance/identity_lock human-review surface).
3. Specific-neutral fallback: when inference fails, commit to a
   neutral but CONCRETE setting — never blank, never vague
   ("亚洲人"-class hedges). check_specific_neutral() flags blanks and
   hedge vocabulary in required identity fields.

Decision-vs-fact trails (from/mergeNote ↔ inferred) are separate audit
trails that never mix — schema home: docs/entity-registry.md
("Decision provenance" section), datasets/entity-registry.json.

ZERO-MODEL: no LLM, no network. Deterministic string checks.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = [
    "ProvenanceViolation", "ProvenanceGateError",
    "check_provenance_tier", "strip_markers", "check_prompt_fields",
    "check_specific_neutral", "INFERRED_MARKER", "MARKER_RE",
    "HEDGE_TERMS",
]

# The single sanctioned marker form. Exactly one per item, English
# report form (our pipeline reports are English; the Chinese 「（推断）」
# form is NOT accepted here — one marker, not both).
INFERRED_MARKER = "(inferred)"

# Marker occurrences anywhere in the text (case-insensitive, tolerant
# of inner whitespace so "( inferred )" still counts as the marker).
MARKER_RE = re.compile(r"\(\s*inferred\s*\)", re.IGNORECASE)

# Human-facing identity fields where provenance tiers apply. These are
# the bible-side counterparts of RenderBrief.identity_lock: appearance
# and identity descriptions carried in entity records / briefs before
# they become prompt fragments.
IDENTITY_FIELDS = ("appearance", "identity", "identity_lock")

# Vague-hedge vocabulary (specific-neutral fallback rule): these mark
# the "泛泛的「亚洲人」" failure mode — a required identity field left
# as a category instead of a concrete setting.
HEDGE_TERMS = (
    "asian", "european", "american", "african", "middle eastern",
    "east asian", "south asian", "western", "generic", "unspecified",
    "tbd", "tba", "unknown", "vague",
)


class ProvenanceGateError(ValueError):
    """Typed gate failure. kind marks the loud-skip case."""

    def __init__(self, message: str, *, kind: str | None = None,
                 violations: list | None = None):
        self.kind = kind
        self.violations = violations or []
        super().__init__(message)


@dataclass(frozen=True)
class ProvenanceViolation:
    field: str
    matched_text: str
    reason: str

    def __str__(self) -> str:  # pragma: no cover - display only
        return f"{self.field} provenance violation: {self.reason}"


def _split_claims(text: str) -> list[str]:
    """Split a multi-claim identity description into items.

    Items are separated by ';', newlines, or ' and ' conjunctions at
    the top level. Each item is checked independently: exactly one
    tier (canon-cited context OR one marker) per item.
    """
    parts = re.split(r";|\n|(?<=\.)\s+and\s+", text, flags=re.I)
    return [p.strip() for p in parts if p.strip()]


def check_provenance_tier(text: str, *, field: str = "identity",
                          has_canon_citation: bool = False) -> list:
    """Return ProvenanceViolation list for one identity claim *text*.

    Tiers:
    - has_canon_citation=True: claim is grounded in canon — clean,
      UNLESS it also carries a marker (double-marked = violation:
      "exactly one marker per item, never both" extends to
      citation+marker redundancy).
    - has_canon_citation=False: the claim MUST carry exactly one
      `(inferred)` marker. Zero markers = unmarked middle ground
      (violation). Two or more = double-marked (violation).

    Pure, deterministic, offline. Empty text raises typed loud skip.
    """
    if not isinstance(text, str) or not text.strip():
        raise ProvenanceGateError(
            f"provenance gate: {field!r} is EMPTY/blank — nothing to "
            "tier (loud skip; specific-neutral fallback applies: "
            "commit to a concrete setting, never leave blank)",
            kind="empty_text")

    markers = MARKER_RE.findall(text)
    n = len(markers)

    if has_canon_citation:
        if n >= 1:
            return [ProvenanceViolation(
                field=field, matched_text=text[:60],
                reason=("claim already carries a canon citation AND "
                        "an (inferred) marker — exactly one provenance "
                        "tier per item (inferred-marker-convention.md, "
                        "profile-pass.md:24)"))]
        return []

    if n == 0:
        return [ProvenanceViolation(
            field=field, matched_text=text[:60],
            reason=("identity claim is NEITHER canon-cited NOR "
                    "(inferred)-marked — no unmarked middle ground "
                    "(inferred-marker-convention.md rule 1); cite the "
                    "bible field or add exactly one (inferred)"))]
    if n > 1:
        return [ProvenanceViolation(
            field=field, matched_text=text[:60],
            reason=(f"{n} (inferred) markers on one item — exactly "
                    "ONE marker per item, never both "
                    "(只用一种标记，不要中英都加; profile-pass.md:24)"))]
    return []


def strip_markers(text: str) -> str:
    """Remove every `(inferred)` marker from *text* (the handoff
    stripping step). Collapses the whitespace the marker occupied so
    sentences stay grammatical: "grey hull (inferred), ink bleed" ->
    "grey hull, ink bleed".

    This is what brief_to_prompt() applies before any prompt field is
    built — the marker NEVER enters a machine prompt.
    """
    out = MARKER_RE.sub("", text)
    # collapse doubled spaces/punctuation left behind
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\s+([,.;])", r"\1", out)
    return out.strip()


def check_prompt_fields(prompt_text: str) -> list:
    """Assert a rendered prompt carries NO provenance markers.

    Called at the brief_to_prompt seam (handoff-to-prompt time). Any
    `(inferred)` substring in a prompt field is a typed violation —
    the marker would literally get painted into the render
    (profile-pass.md:44).
    """
    hits = MARKER_RE.findall(prompt_text or "")
    if not hits:
        return []
    return [ProvenanceViolation(
        field="prompt", matched_text=prompt_text[:80],
        reason=(f"{len(hits)} (inferred) marker(s) reached a prompt "
                "field — markers live in human fields ONLY and are "
                "stripped at handoff-to-prompt time "
                "(inferred-marker-convention.md placement rule 1; "
                "profile-pass.md:44)"))]


def check_specific_neutral(text: str, *, field: str = "identity") -> list:
    """Specific-neutral fallback check (placement rule 3).

    A REQUIRED identity field must be a concrete setting: non-blank
    AND free of vague-hedge vocabulary. Blank is caught upstream by
    the empty-text loud skip; this catches the "泛泛的「亚洲人」"
    hedge class.
    """
    if not isinstance(text, str) or not text.strip():
        return []  # blank handled by check_provenance_tier loud skip
    low = text.lower()
    hedges = [h for h in HEDGE_TERMS if re.search(
        r"(?<![\w])" + re.escape(h) + r"(?![\w])", low)]
    if hedges:
        return [ProvenanceViolation(
            field=field, matched_text=", ".join(hedges),
            reason=("required identity field is a vague hedge "
                    f"({', '.join(hedges)}) — commit to a neutral but "
                    "CONCRETE setting, never blank, never generic "
                    "(inferred-marker-convention.md rule 3, "
                    "profile-pass.md:44)"))]
    return []
