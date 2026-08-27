"""WD-4s1b — beat-grid / lyric-boundary CLAIM fields + validator.

Doctrine (docs/extraction/shuohao-skills/changelog-design-rationale.md
section C, L17-18 + L47; upstream CHANGELOG:482-500):
"说明给人读，认领给机器查" — declarations are for humans, CLAIMS are
for machines to check. hookBeat [scene,beat] CLAIMS the hook's
location and the gate checks the claim: "衔接从此是门不是自觉" —
continuity becomes a gate, not self-discipline.

Our application: cut/shot records carry soft timing intentions (where
a cut should land relative to lyric phrases). This module makes them
machine-checkable: each cut CLAIMS its landing point as a lyric-phrase
boundary reference (phrase id + offset), and validate_beat_claims()
replays the claims against the beat grid deterministically.

ZERO-MODEL: no LLM, no network. Loud skip, never silent (same axiom
as gates/no_names_gate.py and predict/skeleton.py).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

# distinct typed kinds for the loud-skip cases (spec: empty grid and
# empty cuts must be DISTINCT typed results, not silent passes)
EMPTY_GRID = "empty_grid"
EMPTY_CUTS = "empty_cuts"


class BeatClaimValidationError(ValueError):
    """Deterministic beat-claim validation failed, or an input was
    structurally absent (loud skip). `.kind` is EMPTY_GRID /
    EMPTY_CUTS for the input cases, None for claim violations;
    `.violations` carries the per-cut violation strings."""

    def __init__(self, message: str, *,
                 kind: Optional[str] = None,
                 violations: Optional[List[str]] = None):
        self.kind = kind
        self.violations = violations or []
        super().__init__(message)


@dataclass(frozen=True)
class Phrase:
    id: str
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class BeatGrid:
    phrases: List[Phrase]


@dataclass(frozen=True)
class CutClaim:
    phrase_id: str
    offset: float                 # seconds within the phrase
    tolerance: Optional[float] = None   # per-cut override


@dataclass(frozen=True)
class CutRecord:
    """The shape cut/shot entries use: an actual cut time + its
    CLAIM (doctrine: the claim field is what makes the soft intent
    machine-checkable). claim=None is a violation (unclaimed cut),
    not a silent pass."""
    cut_id: str
    time: float
    claim: Optional[CutClaim] = None


def validate_beat_claims(grid: BeatGrid, cuts: List[CutRecord],
                         default_tolerance: float, *,
                         raise_on_invalid: bool = False
                         ) -> List[str]:
    """Replay every cut's claim against the beat grid.

    claimed landing time = phrase.start + offset;
    PASS when |actual - claimed| <= tolerance (per-cut override or
    default). Returns violation strings; raises typed
    BeatClaimValidationError when raise_on_invalid or when the INPUTS
    are structurally empty (loud skip — distinct kinds).
    """
    if grid is None or not getattr(grid, "phrases", None):
        raise BeatClaimValidationError(
            "beat grid is EMPTY — no phrase boundaries to check "
            "claims against (loud skip; a grid must be provided)",
            kind=EMPTY_GRID)
    if not cuts:
        raise BeatClaimValidationError(
            "cut list is EMPTY — nothing claims any lyric boundary "
            "(loud skip; cuts must exist to be checked)",
            kind=EMPTY_CUTS)

    by_id = {p.id: p for p in grid.phrases}
    v: List[str] = []

    for c in cuts:
        if c.claim is None:
            v.append(f"cut {c.cut_id!r} has NO CLAIM — timing-"
                     "sensitive cuts must claim a lyric-phrase "
                     "landing (说明给人读，认领给机器查)")
            continue
        ph = by_id.get(c.claim.phrase_id)
        if ph is None:
            v.append(f"cut {c.cut_id!r} claims unknown phrase "
                     f"{c.claim.phrase_id!r} — not found in the "
                     f"grid ({sorted(by_id)})")
            continue
        dur = ph.end - ph.start
        if c.claim.offset < 0 or c.claim.offset > dur:
            v.append(f"cut {c.cut_id!r} offset {c.claim.offset}s "
                     f"outside phrase {ph.id!r} bounds "
                     f"(0..{dur}s)")
            continue
        claimed = ph.start + c.claim.offset
        tol = (c.claim.tolerance if c.claim.tolerance is not None
               else default_tolerance)
        drift = abs(c.time - claimed)
        if drift > tol:
            v.append(f"cut {c.cut_id!r} drift {drift:.4f}s beyond "
                     f"tolerance {tol}s: actual {c.time}s vs "
                     f"claimed {claimed:.4f}s "
                     f"(phrase {ph.id!r} +{c.claim.offset}s)")

    if v and raise_on_invalid:
        raise BeatClaimValidationError(
            "beat-claim violations:\n- " + "\n- ".join(v),
            violations=v)
    return v


def load_grid_json(doc: dict) -> BeatGrid:
    return BeatGrid(phrases=[Phrase(**p)
                             for p in doc.get("phrases", [])])


def load_cuts_json(doc: dict) -> List[CutRecord]:
    out = []
    for c in doc.get("cuts", []):
        cl = c.get("claim")
        out.append(CutRecord(
            cut_id=c["cut_id"], time=float(c["time"]),
            claim=CutClaim(**cl) if cl else None))
    return out
