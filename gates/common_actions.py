"""Common-actions gate — deterministic anti-mush check on action text.

ADOPT of the shuohao-skills script-pass common-actions rule
(docs/extraction/shuohao-skills/pass-methodology-outline.md section 4,
script-pass L10-18; RUBRIC-methodology-extraction.md A4.2): video
models only act what they've seen millions of times — walking,
sitting, handing, nodding are safe; precise physics interaction,
micro-expression direction, and inch-scale displacement will break.
The judgment test (verbatim): "is this action common in real-life
video?"

Detection is pattern matching against the RISKY section of
datasets/common-actions.json ONLY — word-boundary anchored,
case-insensitive (same _compile style as gates/no_names_gate.py).
SAFE-list presence is NOT required: the gate rejects known-bad
patterns only (a mis-blocking gate is worse than no gate; the seed
list grows from observed 3090 mush cases, each addition citing the
failing render — docs/common-actions.md).

The gate is ALWAYS ACTIVE in brief validation (patterns are bundled
with the repo; no registry= skip — unlike no-names, whose registry is
per-production context). ZERO-MODEL: no LLM, no network.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

__all__ = ["ActionViolation", "check_common_actions",
           "load_actions_registry", "EMPTY_TEXT"]

EMPTY_TEXT = "empty_text"

_VALID_CATEGORIES = {"physics", "micro_expression", "fine_displacement"}

_REPO = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = _REPO / "datasets" / "common-actions.json"


class ActionGateError(ValueError):
    """Typed gate failure. kind=EMPTY_TEXT for the loud-skip case;
    otherwise a brief/action violation (used via ValueError subtype
    compatibility with the RenderBrief rejection path)."""

    def __init__(self, message: str, *, kind: str | None = None):
        self.kind = kind
        super().__init__(message)


@dataclass(frozen=True)
class ActionViolation:
    """One risky action pattern found in text."""
    id: str
    category: str          # physics | micro_expression | fine_displacement
    matched_text: str
    span: tuple[int, int]

    def __str__(self) -> str:  # pragma: no cover - display only
        return (f"{self.category} pattern {self.id!r} on "
                f"{self.matched_text!r} — not a common real-life-video "
                "action; rewrite the beat")


def _compile(pattern: str) -> re.Pattern[str]:
    # word-boundary anchored, case-insensitive — same style as
    # gates/no_names_gate.py _compile; the pattern body itself may
    # contain its own alternations.
    return re.compile(
        r"(?<![\w])(" + pattern + r")(?![\w])", re.IGNORECASE)


def _iter_patterns(registry: dict):
    rows = []
    for r in registry.get("risky", []):
        pat = (r.get("pattern") or "").strip()
        if not pat:
            continue
        rows.append((r.get("id", pat), r.get("category", ""),
                     pat, _compile(pat)))
    # longest patterns first so overlapping hits prefer the specific
    rows.sort(key=lambda r: len(r[2]), reverse=True)
    return rows


def check_common_actions(text: str,
                         registry: dict | None = None
                         ) -> list[ActionViolation]:
    """Return every RISKY pattern hit in *text* (empty list = clean).

    Pure, deterministic, offline. Empty/whitespace text raises typed
    ActionGateError(kind=EMPTY_TEXT) — loud skip, never a silent pass.
    """
    if not isinstance(text, str) or not text.strip():
        raise ActionGateError(
            "common-actions gate: text is EMPTY/blank — nothing to "
            "check (loud skip; pass actual action text)", kind=EMPTY_TEXT)
    if registry is None:
        registry = load_actions_registry(DEFAULT_REGISTRY)
    violations: list[ActionViolation] = []
    taken: list[tuple[int, int]] = []
    for pid, cat, _pat, rx in _iter_patterns(registry):
        for m in rx.finditer(text):
            span = (m.start(1), m.end(1))
            if any(s <= span[0] and span[1] <= e for s, e in taken):
                continue
            taken.append(span)
            violations.append(ActionViolation(
                id=pid, category=cat, matched_text=m.group(1),
                span=span))
    violations.sort(key=lambda v: v.span)
    return violations


def load_actions_registry(path) -> dict:
    """Load + validate the actions registry JSON."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"actions registry not found: {p}")
    doc = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or "risky" not in doc:
        raise ValueError(
            f"actions registry {p} must be a JSON object with a "
            "'risky' array (schema: docs/common-actions.md)")
    for i, r in enumerate(doc["risky"]):
        for f in ("id", "pattern", "category", "rationale"):
            if not (r.get(f) or "").strip():
                raise ValueError(
                    f"actions registry entry {i} missing {f!r}")
        if r["category"] not in _VALID_CATEGORIES:
            raise ValueError(
                f"actions registry entry {i} category "
                f"{r['category']!r} not in {sorted(_VALID_CATEGORIES)}")
    return doc
