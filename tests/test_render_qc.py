"""WD-hjn4 RED tests: RenderQC — VLM-scored gate with genre thresholds.

- VLM critique signature: coherence, brief_adherence,
  concept_encoding, scores 0-10, consumed from a CritiqueRecord
- genre threshold table (operator-tunable module constants):
  comedy>=7, edu>=8, music>=5, surreal>=4.5
- verdict enum {pass, revise, reject} with typed reasons
- CONCEPT_ENCODING_FAILURE (informed-good + blind-bad pattern) ->
  exactly ONE revision anchored on a single field, then escalate to
  human (typed escalation, never silent)
- DummyLM only; no real VLM/network.
"""
import json

import dspy
import pytest

from wangp_dspy.prompt_director import RenderBrief
from wangp_dspy.profile_selector import ProfileDecision
from wangp_dspy.render_qc import (
    CRITIQUE_FIELDS, GENRE_THRESHOLDS, CritiqueRecord, QCVerdict,
    RenderQC, RenderQCSignature, Verdict,
)

BRIEF = RenderBrief(
    subject="astronaut, cracked visor", motion="slow head turn",
    camera="dolly in", style="16mm archival grain")

DECISION = ProfileDecision(
    model="h3", resolution="768p", shot_length_frames=176,
    seed_policy="fixed_per_story", wangp_profile="profile3")


def _crit(**over):
    base = {
        "coherence": 8.0, "brief_adherence": 8.0, "concept_encoding": 8.0,
        "scores": {"coherence": 8, "brief_adherence": 8,
                   "concept_encoding": 8},
        "notes": "solid",
    }
    base.update(over)
    return base


def _lm(crit):
    return dspy.utils.DummyLM([
        {"reasoning": "r", "critique": json.dumps(crit)}])


# ── 1: signature shape ───────────────────────────────────────────────────

def test_signature_takes_context_and_outputs_critique():
    ins = RenderQCSignature.input_fields
    for f in ("subject", "motion", "camera", "style", "model",
              "shot_length_frames"):
        assert f in ins, f
    assert set(RenderQCSignature.output_fields) == {"critique"}


def test_critique_field_vocabulary():
    assert CRITIQUE_FIELDS == ("coherence", "brief_adherence",
                               "concept_encoding")


# ── 2: CritiqueRecord schema (RED: module absent) ────────────────────────

def test_critique_record_valid():
    r = CritiqueRecord(**_crit())
    assert r.coherence == 8.0


def test_critique_record_rejects_out_of_range():
    with pytest.raises(Exception):
        CritiqueRecord(**_crit(coherence=11.0))
    with pytest.raises(Exception):
        CritiqueRecord(**_crit(brief_adherence=-0.1))


# ── 3: genre threshold table ─────────────────────────────────────────────

def test_threshold_constants():
    assert GENRE_THRESHOLDS == {"comedy": 7.0, "edu": 8.0,
                                "music": 5.0, "surreal": 4.5}


# ── 4: verdicts at boundaries ────────────────────────────────────────────

def _qc(genre):
    return RenderQC(genre=genre)


def test_comedy_boundary_pair():
    assert _qc("comedy").judge(CritiqueRecord(**_crit(coherence=7.0))).verdict is Verdict.PASS
    assert _qc("comedy").judge(CritiqueRecord(**_crit(coherence=6.9))).verdict is Verdict.REVISE


def test_edu_boundary_pair():
    assert _qc("edu").judge(CritiqueRecord(**_crit(brief_adherence=8.0))).verdict is Verdict.PASS
    assert _qc("edu").judge(CritiqueRecord(**_crit(brief_adherence=7.9))).verdict is Verdict.REVISE


def test_music_boundary_pair():
    assert _qc("music").judge(CritiqueRecord(**_crit(concept_encoding=5.0))).verdict is Verdict.PASS
    assert _qc("music").judge(CritiqueRecord(**_crit(concept_encoding=4.9))).verdict is Verdict.REVISE


def test_surreal_boundary_pair():
    assert _qc("surreal").judge(CritiqueRecord(**_crit(coherence=4.5))).verdict is Verdict.PASS
    assert _qc("surreal").judge(CritiqueRecord(**_crit(coherence=4.4))).verdict is Verdict.REVISE


def test_reject_on_very_low_scores():
    v = _qc("comedy").judge(CritiqueRecord(**_crit(coherence=2.0)))
    assert v.verdict is Verdict.REJECT


def test_unknown_genre_rejected():
    with pytest.raises(Exception):
        RenderQC(genre="horror")


def test_verdict_vocabulary():
    assert {v.value for v in Verdict} == {"pass", "revise", "reject"}


def test_verdict_has_typed_reason():
    v = _qc("comedy").judge(CritiqueRecord(**_crit(coherence=6.9)))
    assert v.reason  # typed, non-empty
    assert isinstance(v, QCVerdict)


# ── 5: CONCEPT_ENCODING_FAILURE — one revision, then escalate ───────────

def _cef_critiques():
    """Informed-good + blind-bad: brief WITH context scores well, the
    same clip judged WITHOUT the brief scores badly -> the model encoded
    the prompt text, not the concept."""
    informed = CritiqueRecord(**_crit(concept_encoding=8.0, notes="matches brief well"))
    blind = CritiqueRecord(**_crit(concept_encoding=2.0, notes="concept unreadable"))
    return informed, blind


def test_cef_allows_exactly_one_revision_then_escalates():
    informed, blind = _cef_critiques()
    qc = RenderQC(genre="comedy")
    d1 = qc.detect_concept_failure(informed=informed, blind=blind)
    assert d1 is True
    # first revision request: anchored on a SINGLE field, allowed
    v1 = qc.request_revision(d1, attempt=1)
    assert v1.verdict is Verdict.REVISE
    assert v1.anchor_field in CRITIQUE_FIELDS
    # second attempt with the failure still standing: typed escalation
    with pytest.raises(Exception) as ei:
        qc.request_revision(d1, attempt=2)
    assert "human" in str(ei.value).lower()


def test_cef_not_detected_when_blind_agrees():
    informed, blind = _cef_critiques()
    blind = CritiqueRecord(**_crit(concept_encoding=7.5, notes="fine"))
    qc = RenderQC(genre="comedy")
    assert qc.detect_concept_failure(informed=informed, blind=blind) is False


# ── 6: end-to-end with DummyLM critique ──────────────────────────────────

def test_full_pipeline_pass():
    qc = RenderQC(genre="edu")
    with dspy.context(lm=_lm(_crit())):
        v = qc.run(brief=BRIEF, decision=DECISION)
    assert v.verdict is Verdict.PASS


def test_full_pipeline_malformed_critique_raises():
    qc = RenderQC(genre="edu")
    lm = dspy.utils.DummyLM([{"reasoning": "r", "critique": "not json"}])
    with dspy.context(lm=lm):
        with pytest.raises(Exception):
            qc.run(brief=BRIEF, decision=DECISION)
