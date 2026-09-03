import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_film import (  # noqa: E402
    LM_CHOICES, RunFilmError, build_lm, _plan_with_lm,
)

PASS1_JSON = json.dumps({
    "beats": [
        {"speaker": "Grandma", "text": "Hello in there."},
        {"speaker": "Prisoner", "text": "The devil expected you."},
    ]})


def test_lm_choices_glm_present():
    assert "glm" in LM_CHOICES
    assert "none" in LM_CHOICES


def test_build_lm_none():
    assert build_lm("none") is None


def test_build_lm_unknown_rejects():
    with pytest.raises(ValueError):
        build_lm("modelscope")  # NEVER a choice


def test_build_lm_glm_requires_key(monkeypatch):
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    with pytest.raises(RunFilmError):
        build_lm("glm")


def test_build_lm_glm_shape(monkeypatch):
    """glm -> real dspy.LM on the z.ai OpenAI endpoint, chat mode."""
    monkeypatch.setenv("ZAI_API_KEY", "sk-test-fake")
    import dspy
    lm = build_lm("glm")
    assert isinstance(lm, dspy.LM)
    assert "glm-5.3" in lm.model
    assert lm.model.startswith("openai/")
    # provider kwargs land on the LM (readable regardless of layout)
    blob = str(lm.__dict__) + str(getattr(lm, "kwargs", ""))
    assert "api.z.ai" in blob or "https://api.z.ai/v1" in blob
    assert "model_type" in blob
    assert "modelscope" not in blob.lower()


def test_plan_with_lm_none_is_deterministic():
    rows = [{"speaker": "A", "text": "hi"}]
    out = _plan_with_lm(rows, [{"name": "A"}], lm=None)
    assert out == rows


def test_plan_with_lm_routes_through_dspy_context():
    """A DummyLM ambient drives pass1 (Signature path, no network)."""
    import dspy
    fake = dspy.utils.DummyLM([{"beats": PASS1_JSON}])
    rows = [{"speaker": "Grandma", "text": "Hello in there."}]
    chars = [{"name": "Grandma",
              "description": "elderly woman with a lantern"}]
    beats = _plan_with_lm(rows, chars, lm=fake)
    assert beats and beats[0]["speaker"] == "Grandma"
