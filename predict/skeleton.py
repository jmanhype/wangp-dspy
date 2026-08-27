"""WD-gq8y — round-1 skeleton artifact + deterministic validation +
sign-off gate.

Doctrine (docs/extraction/shuohao-skills/pass-methodology-outline.md,
outline-pass section):
- L19-26 two-round skeleton validation: round 1 "fast version" fills
  the four blocks, validates, STOPS for USER sign-off; round 2
  refines after feedback. Rationale (L26): the fast round is cheap —
  "错了只损失一轮骨架，不是 60 集梗概" (an error costs one skeleton,
  not 60 episode synopses).
- L17 decision sentences: cutNote + mergeNote headline the review's
  key-decisions block shown for sign-off.
- L15 evidence-on-decisions: every keep/cut decision carries its why.

ZERO-MODEL: no LLM, no network — deterministic validation only.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class SkeletonValidationError(ValueError):
    """Deterministic skeleton validation failed. The violation list
    is on `.violations` and joined in the message (loud failure, same
    pattern as predict/prompt_director.py _reject_meta_hints and
    gates/no_names_gate.py)."""


@dataclass(frozen=True)
class Cut:
    what: str
    why: str          # L15: every cut carries its why


@dataclass(frozen=True)
class Merge:
    who: str
    why: str
    from_source: str = ""   # characters[].from provenance (L12 area)


@dataclass(frozen=True)
class PayoffPlacement:
    majors: List[int]       # 1-based episode numbers, ascending
    total_episodes: int


@dataclass(frozen=True)
class Signoff:
    status: str             # pending | approved | rejected
    reviewer: str
    ts: str


@dataclass(frozen=True)
class Skeleton:
    skeleton_id: str
    cuts: List[Cut]
    merges: List[Merge]
    payoff: PayoffPlacement
    cut_note: str           # L17 decision sentence: "the story ends at..."
    merge_note: str         # L17: why the lead group was chosen
    signoff: Optional[Signoff] = None


def _nonempty(s: str) -> bool:
    return isinstance(s, str) and bool(s.strip())


def validate_skeleton(skel: Skeleton, *,
                      raise_on_invalid: bool = False) -> List[str]:
    """Deterministic round-1 validation -> violation strings.

    Rules (all four blocks present+nonempty; whys required; payoff
    spacing adapted from the doctrine's hard rules):
    - majors sorted, in range 1..total_episodes
    - no vacuum at start: first major <= 3 (episode 1..3 window)
    - no vacuum at end: last major >= total_episodes - 2
    - earliest major not in the final episode only placement:
      if the earliest major IS the last episode, nothing anchors the
      body — rejected
    """
    v: List[str] = []

    if not isinstance(skel.cuts, list) or not skel.cuts:
        v.append("cuts block is empty — every skeleton must state "
                 "what was cut (or merge cuts are intentional and "
                 "must still be recorded)")
    else:
        for i, c in enumerate(skel.cuts):
            if not _nonempty(c.what):
                v.append(f"cut[{i}].what is empty")
            if not _nonempty(c.why):
                v.append(f"cut[{i}] '{c.what}' has no why — every "
                         "cut decision carries its evidence (L15)")

    if not isinstance(skel.merges, list) or not skel.merges:
        v.append("merges block is empty — who was merged must be "
                 "recorded (合人 by duplicate function)")
    else:
        for i, m in enumerate(skel.merges):
            if not _nonempty(m.who):
                v.append(f"merge[{i}].who is empty")
            if not _nonempty(m.why):
                v.append(f"merge[{i}] '{m.who}' has no why — merge "
                         "decisions carry their evidence")

    p = skel.payoff
    if p is None:
        v.append("payoff block is missing")
    else:
        majors = list(p.majors or [])
        n = p.total_episodes
        if not majors:
            v.append("payoff block is empty — major-beat placement "
                     "must be stated (排爽点)")
        if n <= 0:
            v.append("total_episodes must be positive")
        else:
            out_of_range = [m for m in majors
                            if not (1 <= m <= n)]
            if out_of_range:
                v.append(f"majors out of range 1..{n}: "
                         f"{out_of_range}")
            srt = sorted(majors)
            if majors != srt:
                v.append("majors must be ascending")
            if srt:
                if srt[0] > 2:
                    v.append(f"payoff vacuum at start: first major "
                             f"lands at ep {srt[0]} of {n} (must be "
                             "within the first 2 episodes)")
                for a, b in zip(srt, srt[1:]):
                    if b - a > 3:
                        v.append(f"payoff gap: {b - a} dry episodes "
                                 f"between majors at ep {a} and ep "
                                 f"{b} (max 3)")
                        break
                if srt[-1] < n - 2:
                    v.append(f"payoff vacuum at end: last major at "
                             f"ep {srt[-1]} of {n} (must land within "
                             "the final 3)")
                if len(srt) >= 1 and srt[0] == n and n > 1:
                    v.append("earliest major is the final episode — "
                             "nothing anchors the body")

    if not _nonempty(skel.cut_note):
        v.append("cutNote decision sentence missing (L17: 'the "
                 "story ends at…' headlines the sign-off review)")
    if not _nonempty(skel.merge_note):
        v.append("mergeNote decision sentence missing (L17: why the "
                 "lead group was chosen)")

    if skel.signoff is None:
        v.append("signoff block missing (pending/approved/rejected)")

    if v and raise_on_invalid:
        raise SkeletonValidationError(
            "skeleton validation failed:\n- " + "\n- ".join(v))
    return v


def require_signoff(skel: Skeleton) -> None:
    """Sign-off gate: proceeding past round 1 requires
    signoff.status == approved. Typed, loud, names id + status."""
    if skel.signoff is None:
        raise SkeletonValidationError(
            f"skeleton {skel.skeleton_id!r} has no signoff block — "
            "round-1 requires explicit user sign-off before any "
            "expensive stage runs")
    if skel.signoff.status != "approved":
        raise SkeletonValidationError(
            f"skeleton {skel.skeleton_id!r} signoff status is "
            f"{skel.signoff.status!r} — refusing to proceed past "
            "round 1 (an error costs one skeleton, not 60 episode "
            "synopses)")
    viol = validate_skeleton(skel)
    if viol:
        raise SkeletonValidationError(
            f"approved skeleton {skel.skeleton_id!r} still invalid: "
            + "; ".join(viol[:5]))


def render_skeleton_for_review(skel: Skeleton) -> str:
    """Pretty-print for HUMAN review — the three sign-off questions
    rendered explicitly (L19-26): which lines cut / which people
    merged / where the majors land."""
    lines = [f"=== round-1 skeleton {skel.skeleton_id} — "
             "for sign-off ===", ""]
    lines.append("KEY DECISIONS (decision sentences, L17):")
    lines.append(f"  cut:   {skel.cut_note}")
    lines.append(f"  merge: {skel.merge_note}")
    lines.append("")
    lines.append("Q1 — WHICH LINES WERE CUT?")
    for c in skel.cuts:
        lines.append(f"  - {c.what}")
        lines.append(f"      why: {c.why}")
    lines.append("")
    lines.append("Q2 — WHICH PEOPLE WERE MERGED?")
    for m in skel.merges:
        lines.append(f"  - {m.who}"
                     + (f"  (from: {m.from_source})" if m.from_source
                        else ""))
        lines.append(f"      why: {m.why}")
    lines.append("")
    lines.append("Q3 — WHERE DO THE MAJORS LAND?")
    p = skel.payoff
    if p:
        lines.append(f"  majors at eps {p.majors} of "
                     f"{p.total_episodes}")
    st = skel.signoff.status if skel.signoff else "(missing)"
    lines.append("")
    lines.append(f"sign-off status: {st}"
                 + (f" by {skel.signoff.reviewer} at "
                    f"{skel.signoff.ts}" if skel.signoff else ""))
    return "\n".join(lines)
