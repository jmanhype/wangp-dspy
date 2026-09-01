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