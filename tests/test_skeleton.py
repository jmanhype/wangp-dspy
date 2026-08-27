"""WD-gq8y RED tests — round-1 skeleton + deterministic validator +
sign-off gate + pretty-printer. Zero-model: no LLM, no network.
"""
import pytest

from predict.skeleton import (
    Skeleton, Cut, Merge, PayoffPlacement, Signoff,
    validate_skeleton, SkeletonValidationError, require_signoff,
    render_skeleton_for_review,
)


def _valid_signoff(status="approved"):
    return Signoff(status=status, reviewer="operator",
                   ts="2026-08-27T12:00:00Z")


def _valid_skeleton(**over):
    # frozen dataclasses: build via constructor overrides, not setattr
    from dataclasses import replace
    skel = Skeleton(
        skeleton_id="skel-001",
        cuts=[Cut(what="B-plot: rival studio", why="one main plotline "
                "fits short-drama; the rivalry is paid off by the "
                "lead's arc instead")],
        merges=[Merge(who="Detective Han + Officer Ru", why="duplicate "
                 "investigation function; one face carries the "
                 "clue-delivery beats", from_source="ep2/ep7")],
        payoff=PayoffPlacement(majors=[1, 4, 7, 10], total_episodes=10),
        cut_note="the story ends at the harbor reveal",
        merge_note="the lead group is chosen for complete arcs",
        signoff=_valid_signoff(),
    )
    return replace(skel, **over) if over else skel


# ── validator: valid skeleton ─────────────────────────────────────────

def test_valid_skeleton_passes():
    assert validate_skeleton(_valid_skeleton()) == []


# ── each of the four blocks individually empty -> rejected ────────────

def test_empty_cuts_rejected():
    v = validate_skeleton(_valid_skeleton(cuts=[]))
    assert any("cut" in x.lower() for x in v)


def test_empty_merges_rejected():
    v = validate_skeleton(_valid_skeleton(merges=[]))
    assert any("merge" in x.lower() for x in v)


def test_empty_payoff_rejected():
    v = validate_skeleton(_valid_skeleton(payoff=PayoffPlacement(
        majors=[], total_episodes=10)))
    assert any("payoff" in x.lower() or "major" in x.lower() for x in v)


def test_missing_signoff_block_rejected():
    v = validate_skeleton(_valid_skeleton(signoff=None))
    assert any("signoff" in x.lower() for x in v)


# ── cut/merge without why -> rejected ─────────────────────────────────

def test_cut_without_why_rejected():
    v = validate_skeleton(_valid_skeleton(cuts=[Cut(
        what="B-plot", why="")]))
    assert any("why" in x.lower() and "cut" in x.lower() for x in v)


def test_merge_without_why_rejected():
    v = validate_skeleton(_valid_skeleton(merges=[Merge(
        who="A+B", why="   ", from_source="ep1")]))
    assert any("why" in x.lower() and "merge" in x.lower() for x in v)


# ── payoff placement rules ────────────────────────────────────────────

def test_payoff_vacuum_at_start_rejected():
    # earliest major at ep 3 of 10 with nothing early: majors [3,6,9]
    # violates no-vacuum-at-start (gap from ep1 to first major > 2)
    v = validate_skeleton(_valid_skeleton(payoff=PayoffPlacement(
        majors=[3, 6, 9], total_episodes=10)))
    assert any("start" in x.lower() or "vacuum" in x.lower() for x in v)


def test_payoff_vacuum_at_end_rejected():
    v = validate_skeleton(_valid_skeleton(payoff=PayoffPlacement(
        majors=[1, 4, 6], total_episodes=10)))
    assert any("end" in x.lower() or "vacuum" in x.lower() for x in v)


def test_earliest_major_last_ep_rejected():
    # the ONLY major is at the final episode — nothing anchors the body
    v = validate_skeleton(_valid_skeleton(payoff=PayoffPlacement(
        majors=[10], total_episodes=10)))
    assert any("last" in x.lower() or "final" in x.lower()
               or "anchors" in x.lower() for x in v), v


def test_payoff_in_range():
    v = validate_skeleton(_valid_skeleton(payoff=PayoffPlacement(
        majors=[0, 11], total_episodes=10)))
    assert any("range" in x.lower() or "1" in x for x in v)


# ── typed error ───────────────────────────────────────────────────────

def test_invalid_raises_typed():
    with pytest.raises(SkeletonValidationError) as ei:
        validate_skeleton(_valid_skeleton(cuts=[]), raise_on_invalid=True)
    assert "cut" in str(ei.value).lower()


def test_decision_sentences_required():
    v = validate_skeleton(_valid_skeleton(cut_note=""))
    assert any("cutNote" in x or "cut_note" in x or "decision" in x.lower()
               for x in v)
    v2 = validate_skeleton(_valid_skeleton(merge_note=""))
    assert any("mergeNote" in x or "merge_note" in x or "decision" in x.lower()
               for x in v2)


# ── sign-off gate ─────────────────────────────────────────────────────

def test_pending_signoff_blocks():
    skel = _valid_skeleton(signoff=_valid_signoff(status="pending"))
    with pytest.raises(Exception) as ei:  # exact type pinned below
        require_signoff(skel)
    assert "skel-001" in str(ei.value) and "pending" in str(ei.value)


def test_rejected_signoff_blocks():
    skel = _valid_skeleton(signoff=_valid_signoff(status="rejected"))
    with pytest.raises(Exception) as ei:
        require_signoff(skel)
    assert "skel-001" in str(ei.value)


def test_approved_signoff_passes_gate():
    require_signoff(_valid_skeleton())  # no raise


# ── pretty-printer: the three sign-off questions ──────────────────────

def test_render_contains_three_questions():
    out = render_skeleton_for_review(_valid_skeleton())
    assert "cut" in out.lower()
    assert "merged" in out.lower() or "merge" in out.lower()
    assert "major" in out.lower()
    # decision sentences headline the review (L17)
    assert "the story ends at" in out
    assert "complete arcs" in out


def test_render_lists_each_cut_and_merge():
    out = render_skeleton_for_review(_valid_skeleton())
    assert "B-plot: rival studio" in out
    assert "Detective Han + Officer Ru" in out


# ── pipeline seam ─────────────────────────────────────────────────────

def test_pipeline_refuses_unapproved_skeleton():
    """Pipeline.forward with a skeleton gate: pending skeleton must
    raise before any stage runs (typed, names id+status)."""
    from predict.pipeline import Pipeline, PipelineStageError

    class Boom:
        def __getattr__(self, name):
            raise AssertionError(
                f"stage must not run before sign-off: {name}")

    pipe = Pipeline(genre="surreal", director=Boom(),
                    selector=Boom())
    skel = _valid_skeleton(signoff=_valid_signoff(status="pending"))
    with pytest.raises(PipelineStageError) as ei:
        pipe.forward_with_skeleton("intent", skeleton=skel)
    assert "signoff" in str(ei.value).lower()
    assert "skel-001" in str(ei.value)
