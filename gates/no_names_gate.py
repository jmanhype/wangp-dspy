"""No-proper-nouns gate — deterministic registry matching.

ADOPT of the shuohao-skills no-names doctrine
(docs/extraction/shuohao-skills/no-names-doctrine.md, WD-4k56/qbcj,
GLM verdict ADOPT): character names, aliases, real people, and IP
names must never appear in image/render prompts — image/video models
bias toward their memorized version of named entities.

Detection is EXACT registry matching only (names + aliases,
case-insensitive, word-boundary anchored). NO LLM, NO network, NO
heuristic proper-noun guessing — our own banked briefs legitimately
contain film-stock and hardware proper nouns ("Kodak Vision3 500T",
"IBM 3420-type", "PS2"), so only registry-listed entities are
violations.

Registry schema: docs/entity-registry.md. Seed registry:
datasets/entity-registry.json.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

__all__ = ["NameViolation", "check_no_proper_nouns", "load_registry"]

_VALID_TYPES = {"character", "place", "ip", "person", "work"}


@dataclass(frozen=True)
class NameViolation:
    """One registry name found in a prompt."""
    entity_id: str
    canonical_name: str
    matched_name: str      # the surface form as it appeared
    span: tuple[int, int]  # (start, end) char offsets in text

    def __str__(self) -> str:  # pragma: no cover - display only
        return (f"proper noun {self.matched_name!r} "
                f"(entity {self.canonical_name!r}, id {self.entity_id}) "
                f"is forbidden in prompts")


def _compile(name: str) -> re.Pattern[str]:
    # word-boundary anchored, case-insensitive exact match.
    # \b around a multiword phrase anchors its outer edges; inner
    # spaces match any whitespace run so "Vermilion  Bay" also fires.
    escaped = re.escape(name.strip())
    return re.compile(r"(?<![\w])" + escaped.replace(r"\ ", r"\s+") +
                      r"(?![\w])", re.IGNORECASE)


def _iter_patterns(registry: dict):
    """Yield (entity_id, canonical, surface, compiled) in a
    deterministic order: longest names first so alias 'Mira Chen'
    is reported in preference to overlapping name 'Mira' alone."""
    rows = []
    for ent in registry.get("entities", []):
        surfaces = [ent.get("name", "")] + list(ent.get("aliases", []))
        for s in surfaces:
            s = (s or "").strip()
            if s:
                rows.append((ent.get("id", s), ent.get("name", s), s,
                             _compile(s)))
    rows.sort(key=lambda r: len(r[2]), reverse=True)
    return rows


def check_no_proper_nouns(text: str, registry: dict) -> list[NameViolation]:
    """Return every registry name found in *text* (empty list = clean).

    Pure, deterministic, offline. Word-boundary semantics are defined
    in docs/entity-registry.md: a match must not touch a word
    character on either side — 'Kaiju' in 'Kaiju rising' and
    'the kaiju' hits; 'kaijur'/'kaijux' do not.
    """
    if not text or not registry or not registry.get("entities"):
        return []
    violations: list[NameViolation] = []
    taken: list[tuple[int, int]] = []
    for eid, canon, surface, rx in _iter_patterns(registry):
        for m in rx.finditer(text):
            span = (m.start(), m.end())
            # longer (alias) matches already claimed this span
            if any(s <= span[0] and span[1] <= e for s, e in taken):
                continue
            taken.append(span)
            violations.append(NameViolation(
                entity_id=eid, canonical_name=canon,
                matched_name=m.group(0), span=span))
    violations.sort(key=lambda v: v.span)
    return violations


def load_registry(path) -> dict:
    """Load + validate a registry JSON file. Raises FileNotFoundError /
    ValueError with a loud, specific message."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"entity registry not found: {p}")
    doc = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or "entities" not in doc:
        raise ValueError(
            f"entity registry {p} must be a JSON object with an "
            "'entities' array (schema: docs/entity-registry.md)")
    for i, ent in enumerate(doc["entities"]):
        if not isinstance(ent, dict) or not (ent.get("name") or "").strip():
            raise ValueError(
                f"entity registry {p}: entity[{i}] missing 'name'")
        if ent.get("type") not in _VALID_TYPES:
            raise ValueError(
                f"entity registry {p}: entity[{i}] type "
                f"{ent.get('type')!r} not in {sorted(_VALID_TYPES)}")
        for alias in ent.get("aliases", []):
            if not isinstance(alias, str) or not alias.strip():
                raise ValueError(
                    f"entity registry {p}: entity[{i}] has a non-string "
                    "or empty alias")
    return doc
