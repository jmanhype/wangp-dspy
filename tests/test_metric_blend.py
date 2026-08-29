"""WD-k2ua — GEPA metric blend tests (TDD)."""
import json
import pytest

from metrics.metric_blend import (
    MetricBlend, SectionWeights, blended_score, load_scores,
    record_scores, SECTION_CRITIQUE_MAP)


# ── typed inputs ─────────────────────────────────────────────────────

def test_section_weights_reject_unknown_section():
    with pytest.raises(ValueError, match="unknown sections"):
        SectionWeights(weights={"nonexistent": 1.0})


def test_section_weights_reject_non_numeric():
    with pytest.raises(ValueError, match="must be numeric"):
        SectionWeights(weights={"subject": "high"})


def test_section_weights_reject_negative():
    with pytest.raises(ValueError, match=">= 0"):
        SectionWeights(weights={"subject": -0.1})


def test_section_weights_must_sum_to_one():
    with pytest.raises(ValueError, match="sum to 1.0"):
        SectionWeights(weights={"subject": 0.5, "motion": 0.4})


def test_qc_scale_bounds():
    with pytest.raises(ValueError, match="qc_scale"):
        MetricBlend(section_weights=SectionWeights(weights={"subject": 1.0}),
                    qc_scale=1.5)


# ── blend semantics: critique-weighted ───────────────────────────────

def test_blend_maps_sections_to_critique_fields():
    assert SECTION_CRITIQUE_MAP["style"] == "concept_encoding"
    assert SECTION_CRITIQUE_MAP["subject"] == "brief_adherence"


def test_blend_scores_perfect_match():
    blend = MetricBlend(section_weights=SectionWeights(
        weights={"subject": 0.5, "motion": 0.5}))
    f1s = {"subject": 1.0, "motion": 1.0}
    critique = {"coherence": 10, "brief_adherence": 10,
                "concept_encoding": 10}
    assert blended_score(f1s, critique, blend) == pytest.approx(1.0)


def test_blend_downweights_sections_with_low_critique():
    blend = MetricBlend(section_weights=SectionWeights(
        weights={"subject": 0.5, "motion": 0.5}))
    f1s = {"subject": 1.0, "motion": 1.0}
    good = {"coherence": 10, "brief_adherence": 10, "concept_encoding": 10}
    bad_adherence = {"coherence": 10, "brief_adherence": 0,
                     "concept_encoding": 10}
    assert blended_score(f1s, bad_adherence, blend) < \
        blended_score(f1s, good, blend)


def test_blend_qc_scale_scales_output():
    blend_full = MetricBlend(section_weights=SectionWeights(
        weights={"subject": 1.0}), qc_scale=1.0)
    blend_half = MetricBlend(section_weights=SectionWeights(
        weights={"subject": 1.0}), qc_scale=0.5)
    critique = {"coherence": 8, "brief_adherence": 8, "concept_encoding": 8}
    f1s = {"subject": 1.0}
    assert blended_score(f1s, critique, blend_half) == pytest.approx(
        0.5 * blended_score(f1s, critique, blend_full))


def test_blend_missing_sections_score_zero():
    blend = MetricBlend(section_weights=SectionWeights(
        weights={"subject": 0.5, "motion": 0.5}))
    critique = {"coherence": 10, "brief_adherence": 10,
                "concept_encoding": 10}
    assert blended_score({"subject": 1.0}, critique, blend) == \
        pytest.approx(0.5)


def test_blend_empty_weights_refused_at_construction():
    with pytest.raises(ValueError, match="sum to 1.0"):
        SectionWeights(weights={})


def test_blend_id_deterministic():
    kw = dict(section_weights=SectionWeights(weights={"subject": 1.0}))
    assert MetricBlend(**kw).blend_id == MetricBlend(**kw).blend_id


# ── artifact recording / readback ────────────────────────────────────

def test_record_and_readback_roundtrip(tmp_path):
    blend = MetricBlend(section_weights=SectionWeights(
        weights={"subject": 0.6, "motion": 0.4}))
    p = record_scores(tmp_path / "artifacts" / "scores.json",
                      baseline=0.31, validation=0.48,
                      blend=blend, n_val=9)
    data = load_scores(p)
    assert data["baseline"] == 0.31
    assert data["validation"] == 0.48
    assert data["n_val"] == 9
    assert data["blend_id"] == blend.blend_id
    assert data["blend"]["weights"] == {"subject": 0.6, "motion": 0.4}


def test_record_artifact_deterministic(tmp_path):
    blend = MetricBlend(section_weights=SectionWeights(
        weights={"subject": 1.0}))
    a = record_scores(tmp_path / "a.json", 0.1, 0.2, blend, 5)
    b = record_scores(tmp_path / "b.json", 0.1, 0.2, blend, 5)
    assert a.read_bytes() == b.read_bytes()
