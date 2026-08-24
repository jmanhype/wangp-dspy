"""WD-t6i7 wiring slice RED tests: production critic constructor.

No live LM calls: the LM is stubbed/faked everywhere; dspy.context is
inspected, never pointed at a real endpoint."""
import dspy
import pytest

from evaluate.critic import (
    DEFAULT_CRITIC_MODEL, configure_critic, critic_lm,
)
from predict.prompt_director import RenderBrief
from predict.profile_selector import ProfileDecision
from evaluate.render_qc import RenderQC


BRIEF = RenderBrief(subject="astronaut, cracked visor",
                    motion="slow head turn", camera="dolly in",
                    style="16mm archival grain")
DECISION = ProfileDecision(model="h3", resolution="768p",
                           shot_length_frames=96,
                           seed_policy="fixed_per_story",
                           wangp_profile="profile3")
CRIT = ('{"coherence": 8, "brief_adherence": 8, "concept_encoding": 8, '
        '"scores": {}, "notes": ""}')


def test_default_model_is_local_critic():
    assert DEFAULT_CRITIC_MODEL == "ollama_chat/q38u-v2"


def test_renderqc_unconfigured_fails_typed():
    qc = RenderQC("surreal")
    with pytest.raises(Exception, match="[Nn]o LM is loaded"):
        qc.run(BRIEF, DECISION, video="/renders/x.mp4")


def test_configure_critic_builds_lm_and_wires_dspy(monkeypatch):
    built = {}

    class FakeLM(dspy.LM):
        def __init__(self, model, **kw):
            built["model"] = model
            built["kw"] = kw
            super().__init__(model, **kw)

    monkeypatch.setattr("evaluate.critic._lm_cls", FakeLM)
    lm = configure_critic(api_base="http://localhost:11434")
    assert built["model"] == "ollama_chat/q38u-v2"
    assert built["kw"]["api_base"] == "http://localhost:11434"
    assert lm is critic_lm()
    # wired into dspy context
    assert dspy.settings.lm is lm or dspy.get_lm() is lm


def test_configure_critic_rejects_bad_inputs(monkeypatch):
    with pytest.raises(ValueError):
        configure_critic(model="", api_base="http://x:1")
    with pytest.raises(ValueError):
        configure_critic(api_base="")            # no default endpoint guess
    with pytest.raises(ValueError):
        configure_critic(api_base="not a url")
    with pytest.raises(ValueError):
        configure_critic(api_base="http://x:1", timeout_secs=0)


def test_renderqc_run_uses_configured_critic(monkeypatch):
    class FakeLM(dspy.utils.DummyLM):
        def __init__(self, model="fake", **kw):
            super().__init__([{"reasoning": "r", "critique": CRIT}])

    monkeypatch.setattr("evaluate.critic._lm_cls", FakeLM)
    configure_critic(api_base="http://localhost:11434")
    qc = RenderQC("surreal")
    from evaluate.render_qc import Verdict
    v = qc.run(BRIEF, DECISION, video="/renders/x.mp4")
    assert v.verdict is Verdict.PASS
