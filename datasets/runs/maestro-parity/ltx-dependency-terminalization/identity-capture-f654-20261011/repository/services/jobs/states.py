"""Job state machine — EXACT vocabulary (operator ruling 3).

    pending -> preflight -> rendering -> rendered_pending_qc -> qc -> done
                    |            |              ^    |
                    v            v              |    v
                 failed  <-------+------------------+
                    |
                    +-> pending (retry via append-only queue attempt)
                    +-> preflight (legacy retry, same class)
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
    # "-> pending" from active states is ONLY the stale-active recovery
    # path (queue.recover_stale_active): the owning process is dead or
    # its heartbeat is stale, so the job re-enters the queue without
    # redoing per-clip checkpoints (reviewer B2).
    "preflight": frozenset({"rendering", "failed", "pending"}),
    "rendering": frozenset({"rendered_pending_qc", "failed", "pending"}),
    # parked render: QC was unavailable; resume when it returns
    "rendered_pending_qc": frozenset({"preflight", "qc", "failed"}),
    "qc": frozenset({"done", "failed", "rendered_pending_qc", "pending"}),
    # Explicit failed-job retry is mediated by JobQueue.requeue_failed,
    # which appends a new attempt record before taking this transition.
    "failed": frozenset({"pending", "preflight", "dead_letter"}),
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
