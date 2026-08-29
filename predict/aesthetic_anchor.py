"""AestheticAnchor — deterministic style lock + continuity references
from master-first plates (WD-tzy9, S5 film lane).

Doctrine:
- MASTER-FIRST (G6): the anchor cites locked master plates by sha256.
  The plates are the visual ground truth; the style descriptor is the
  textual projection of what the plates show.
- DETERMINISTIC: build() sorts masters canonically and emits sorted-key
  compact JSON — same inputs yield byte-identical bytes and the same
  anchor_id (sha256 over those bytes). Pure logic: no LM, no GPU.
- PROVENANCE-LINKED (WD-oyti): master shas ARE canon citations — briefs
  carrying the anchor ride the canon tier, no (inferred) markers.
- LICENSE-CLEAN: style sources must declare a license from the accepted
  allowlist; anything else is a typed rejection, never a warning.
- CONTINUITY INTEGRATION: the anchor's style_descriptor satisfies
  MultiShotAssembler's STYLE LOCK verbatim by construction — there is
  exactly one style authority per production.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

# Accepted licenses for style/identity sources (operator allowlist;
# extend ONLY with licenses the operator has ruled on).
ACCEPTED_LICENSES = frozenset({"CC0", "CC-BY-4.0", "CC-BY-SA-4.0", "OQL-1.0"})

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class AnchorValidationError(Exception):
    """Typed rejection of an invalid anchor construction."""


def _validate(style_descriptor: str, masters: dict, license: str) -> None:
    if not isinstance(style_descriptor, str) or not style_descriptor.strip():
        raise AnchorValidationError(
            f"style_descriptor must be a nonempty string, got {style_descriptor!r}")
    if not isinstance(masters, dict) or not masters:
        raise AnchorValidationError(
            "masters must be a nonempty dict of cut -> master sha256 "
            "(G6 master-lock: an anchor without locked plates is not an "
            "anchor)")
    for cut, sha in masters.items():
        if not isinstance(sha, str) or not _SHA256_RE.match(sha):
            raise AnchorValidationError(
                f"master plate {cut!r} sha256 {sha!r} is not a lowercase "
                "64-hex sha256 — record the LIVE hash of the locked plate, "
                "never a placeholder")
    if license not in ACCEPTED_LICENSES:
        raise AnchorValidationError(
            f"license {license!r} is not in the accepted allowlist "
            f"{sorted(ACCEPTED_LICENSES)} — license-clean or no anchor")


@dataclass(frozen=True)
class AestheticAnchor:
    """Immutable aesthetic anchor artifact."""
    style_descriptor: str
    masters: dict
    license: str
    canon_citations: tuple

    @classmethod
    def build(cls, style_descriptor: str, masters: dict, license: str):
        _validate(style_descriptor, masters, license)
        canon = tuple(sorted(masters.values()))
        return cls(
            style_descriptor=" ".join(style_descriptor.split()),
            masters=dict(sorted(masters.items())),
            license=license,
            canon_citations=canon,
        )

    def to_canonical_json(self) -> str:
        return json.dumps(
            {
                "style_descriptor": self.style_descriptor,
                "masters": self.masters,
                "license": self.license,
                "canon_citations": list(self.canon_citations),
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def to_record(self) -> dict:
        return json.loads(self.to_canonical_json())


def canonical_bytes(anchor: AestheticAnchor) -> bytes:
    return anchor.to_canonical_json().encode("utf-8")


def anchor_id(anchor: AestheticAnchor) -> str:
    return hashlib.sha256(canonical_bytes(anchor)).hexdigest()
