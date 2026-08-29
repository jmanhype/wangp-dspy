"""Regression tests for the WD-y9ab baseline wiring."""

import dspy

from predict import lm_wiring
from predict.prompt_director import PromptDirector


def test_creative_lm_budget_cannot_truncate_structured_brief(monkeypatch):
    captured = {}

    class FakeLM:
        def __init__(self, *args, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(dspy, "LM", FakeLM)
    monkeypatch.setenv("GLM_API_KEY", "test-key")

    lm_wiring.creative_lm()

    assert captured["max_tokens"] >= 8192


def test_prompt_director_keeps_registry_for_optimizer_calls():
    registry = {"entities": []}
    director = PromptDirector(registry=registry)

    assert director.registry is registry

def test_load_examples_marks_pre_convention_identity_locks():
    """WD-y9ab: banked golds predate the (inferred)-marker convention;
    load_examples must normalize them so gold demos don't teach
    gate-violating briefs (fallback storm 2026-08-29: 26/26 violate)."""
    from gates.provenance_gate import (check_provenance_tier,
                                         MARKER_RE)
    from metrics.qc_feedback import load_examples
    train, val = load_examples("datasets/runs")
    locks = [(ex.brief or {}).get("identity_lock", "")
             for ex in train + val]
    locks = [l for l in locks if l.strip()]
    assert locks, "expected some banked gold identity_locks"
    for lock in locks:
        # passes the tier gate exactly as a produced brief must
        assert check_provenance_tier(lock, field="identity_lock",
                                     has_canon_citation=False) == []
        # exactly one marker, never double
        assert len(MARKER_RE.findall(lock)) == 1


def test_director_language_gate_rejection_becomes_fallback():
    """WD-y9ab: non-English LM content must become a zero-score
    fallback, NEVER an exception out of forward (cannot-raise
    contract; live crash attempt 3: 'é' in audio_direction)."""
    import json as _json
    import dspy
    from predict.prompt_director import PromptDirector
    poisoned = {"subject": "a detective in fog", "motion": "walks",
                "camera": "dolly in", "style": "16mm grain",
                "audio_direction": "musique haute fr\u00e9quence"}
    lm = dspy.utils.DummyLM([{"reasoning": "r",
                              "brief": _json.dumps(poisoned)}])
    d = PromptDirector()
    with dspy.context(lm=lm):
        pred = d.forward(intent="x")
    assert pred.brief.subject.startswith("(invalid brief:")
    assert pred.brief.motion == "(invalid)"
