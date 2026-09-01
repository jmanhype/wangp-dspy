"""services/jobs/states — exact job state machine (operator ruling 3)."""
import pytest

from services.jobs.states import (
    JOB_STATES,
    ALLOWED_TRANSITIONS,
    InvalidTransition,
    JobStateError,
    terminal_states,
    can_transition,
    transition,
)


def test_exact_state_vocabulary():
    assert JOB_STATES == ("pending", "preflight", "rendering",
                          "rendered_pending_qc", "qc", "done", "failed",
                          "dead_letter")


def test_happy_path_pending_to_done():
    path = ["pending", "preflight", "rendering",
            "rendered_pending_qc", "qc", "done"]
    for a, b in zip(path, path[1:]):
        assert can_transition(a, b)


def test_render_completing_with_qc_unavailable_lands_in_rendered_pending_qc():
    # tonight's live failure mode: render done, QC service gone — the
    # job must NOT be failed; it waits in rendered_pending_qc.
    assert can_transition("rendering", "rendered_pending_qc")
    assert can_transition("rendered_pending_qc", "qc")


def test_rendered_pending_qc_can_requeue_preflight_when_qc_returns():
    assert can_transition("rendered_pending_qc", "preflight")


def test_failed_can_retry_or_dead_letter():
    assert can_transition("failed", "preflight")   # retry same class
    assert can_transition("failed", "dead_letter")  # N=3 exhausted


def test_preflight_reject_sends_to_failed():
    assert can_transition("preflight", "failed")


def test_terminal_states_are_done_and_dead_letter():
    assert terminal_states() == frozenset({"done", "dead_letter"})


def test_invalid_transition_raises():
    with pytest.raises(InvalidTransition):
        transition("pending", "done")


def test_transition_returns_new_state():
    assert transition("pending", "preflight") == "preflight"


def test_unknown_state_raises():
    with pytest.raises(JobStateError):
        transition("queued", "pending")


def test_terminal_state_cannot_leave():
    with pytest.raises(InvalidTransition):
        transition("done", "pending")
    with pytest.raises(InvalidTransition):
        transition("dead_letter", "failed")
