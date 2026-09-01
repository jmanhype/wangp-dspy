"""Job state machine — EXACT vocabulary (operator ruling 3).

    pending -> preflight -> rendering -> rendered_pending_qc -> qc -> done
                    |            |              ^    |
                    v            v              |    v
                 failed  <-------+------------------+
                    |
                    +-> preflight (retry, same class) 
                    +-> dead_letter (after N=3 failures of same class)

`rendered_pending_qc` is tonight's live-verified failure mode made
structural: a render completing while QC is UNAVAILABLE parks there
(NOT failed) and resumes when QC returns.
"""
from __future__ import annotations

from typing import FrozenSet, Tuple

JOB_STATES: Tuple[str, ...] = (
    "pending", "preflight", "rendering",
    "rendered_pending_qc", "qc", "done", "failed", "dead_letter",
)

_TERMINAL = frozenset({"done", "dead_letter"})

ALLOWED_TRANSITIONS: dict = {
    "pending": frozenset({"preflight"}),
    "preflight": frozenset({"rendering", "failed"}),
    "rendering": frozenset({"rendered_pending_qc", "failed"}),
    # parked render: QC was unavailable; resume when it returns
    "rendered_pending_qc": frozenset({"preflight", "qc", "failed"}),
    "qc": frozenset({"done", "failed", "rendered_pending_qc"}),
    "failed": frozenset({"preflight", "dead_letter"}),
    "done": frozenset(),
    "dead_letter": frozenset(),
}


class JobStateError(ValueError):
    """Unknown state or illegal transition attempted."""


class InvalidTransition(JobStateError):
    """The from->to pair is not in ALLOWED_TRANSITIONS."""


def terminal_states() -> FrozenSet[str]:
    return frozenset(_TERMINAL)


def can_transition(src: str, dst: str) -> bool:
    if src not in ALLOWED_TRANSITIONS:
        raise JobStateError(f"unknown job state {src!r}")
    if dst not in JOB_STATES:
        raise JobStateError(f"unknown job state {dst!r}")
    return dst in ALLOWED_TRANSITIONS[src]


def transition(src: str, dst: str) -> str:
    if not can_transition(src, dst):
        allowed = sorted(ALLOWED_TRANSITIONS[src]) or ["none (terminal)"]
        raise InvalidTransition(
            f"illegal job state transition {src!r} -> {dst!r} "
            f"(allowed: {allowed})")
    return dst


__all__ = [
    "JOB_STATES", "ALLOWED_TRANSITIONS", "JobStateError",
    "InvalidTransition", "terminal_states", "can_transition",
    "transition",
]
