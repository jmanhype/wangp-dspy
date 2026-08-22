"""MultiShotAssembler — shot chain with continuity lock and
mistake-lock (WD-c4uh). Pure logic; no rendering, no GPU, no LM.

Rules (typed enforcement, ChainValidationError):
- STYLE LOCK: the style descriptor carries VERBATIM between
  consecutive shots (identical strings, not merely similar).
- SUBJECT ANCHOR: the first key term of every shot's subject must be
  consistent across the chain (the anchor noun carries the protagonist).
- END-STATE CHAINING: shot N+1 must OPEN FROM shot N's terminal_state.
  Exact rule: the FIRST KEY TERM (longest alphabetic token sequence up
  to the first comma) of shot N's terminal_state must appear verbatim
  in shot N+1's subject OR motion — i.e. the state the last shot ended
  on is what the next shot visibly starts from.
- MISTAKE-LOCK: declared_deviations are pinned canon. The assembler
  records them in the continuity digest and NEVER corrects or filters
  them; QC interplay is downstream and out of scope here.
- BOUNDS: 2 <= len(shots) <= 20.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from wangp_dspy.profile_selector import ProfileDecision
from wangp_dspy.prompt_director import RenderBrief

MIN_SHOTS = 2
MAX_SHOTS = 20


class ChainValidationError(Exception):
    """Typed violation of the chain rules above."""


def _key_term(text: str) -> str:
    """First key term: leading tokens up to the first comma/period,
    lowercased. 'astronaut mid-turn, dust rising' -> 'astronaut mid-turn'."""
    head = text.split(",")[0].split(".")[0]
    return " ".join(head.split()).lower().strip()


@dataclass(frozen=True)
class ShotPlan:
    brief: RenderBrief
    decision: ProfileDecision
    terminal_state: str
    declared_deviations: tuple = ()

    def __post_init__(self) -> None:
        if not isinstance(self.terminal_state, str) \
                or not self.terminal_state.strip():
            raise ValueError("terminal_state must be a nonempty string")
        if not isinstance(self.declared_deviations, tuple):
            raise ValueError("declared_deviations must be a tuple")
        for d in self.declared_deviations:
            if not isinstance(d, str) or not d.strip():
                raise ValueError(
                    "each declared deviation must be a nonempty string")


@dataclass(frozen=True)
class AssembledChain:
    shots: tuple
    continuity_digest: str


class MultiShotAssembler:
    """Assemble ShotPlans into a validated, digest-stamped chain."""

    def assemble(self, shots) -> AssembledChain:
        plans = tuple(shots)
        n = len(plans)
        if n < MIN_SHOTS:
            raise ChainValidationError(
                f"chain must contain at least {MIN_SHOTS} shots, got {n}")
        if n > MAX_SHOTS:
            raise ChainValidationError(
                f"chain must contain at most {MAX_SHOTS} shots, got {n}")

        # style lock: verbatim carry between consecutive shots
        for i in range(1, n):
            prev_style = plans[i - 1].brief.style
            cur_style = plans[i].brief.style
            if prev_style != cur_style:
                raise ChainValidationError(
                    f"style continuity violation at shot {i}: style "
                    f"descriptor must carry VERBATIM between consecutive "
                    f"shots ({prev_style!r} -> {cur_style!r})")

        # subject anchor: first key term consistent across the chain
        anchors = [_key_term(p.brief.subject) for p in plans]
        anchor = anchors[0]
        for i, a in enumerate(anchors):
            if not a:
                raise ChainValidationError(
                    f"subject anchor missing at shot {i}")
            first_word = a.split()[0]
            if first_word != anchor.split()[0]:
                raise ChainValidationError(
                    f"subject anchor violation at shot {i}: "
                    f"{first_word!r} != {anchor.split()[0]!r} — the "
                    "subject anchor must stay consistent across the chain")

        # end-state chaining: shot i opens from shot i-1 terminal_state
        for i in range(1, n):
            carried = _key_term(plans[i - 1].terminal_state)
            nxt_subject = plans[i].brief.subject.lower()
            nxt_motion = plans[i].brief.motion.lower()
            if carried not in nxt_subject and carried not in nxt_motion:
                raise ChainValidationError(
                    f"end-state chaining violation at shot {i}: shot "
                    f"must open from the previous terminal_state "
                    f"{carried!r}, but neither its subject nor motion "
                    "carries it forward")

        digest = self._digest(plans)
        return AssembledChain(shots=plans, continuity_digest=digest)

    @staticmethod
    def _digest(plans) -> str:
        payload = json.dumps(
            [
                {
                    "subject": p.brief.subject,
                    "motion": p.brief.motion,
                    "camera": p.brief.camera,
                    "style": p.brief.style,
                    "terminal_state": p.terminal_state,
                    "declared_deviations": list(p.declared_deviations),
                }
                for p in plans
            ],
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
