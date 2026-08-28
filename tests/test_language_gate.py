"""WD-c4gw RED tests — two-class language split + registry fold-in.

Doctrine: language-split-contract.md — engine-bound fields LOCKED
ENGLISH (profile-pass.md:16), evidence NEVER translated (:26),
bidirectional gates ("设定英文混进中文…都拦"). ZERO-MODEL.
"""
import pytest

from gates.language_gate import (
    LanguageViolation, check_language_class, ENGINE_BOUND, HUMAN_REVIEW,
)


# ── engine-bound fields: non-English fails LOUDLY ─────────────────────

def test_engine_bound_english_clean():
    v = check_language_class("16mm Ektachrome grain, warm halation",
                             field_class=ENGINE_BOUND)
    assert v == []


def test_engine_bound_chinese_fires():
    v = check_language_class("16mm 胶片颗粒", field_class=ENGINE_BOUND)
    assert len(v) == 1
    assert v[0].field_class == ENGINE_BOUND
    assert v[0].matched_text


def test_engine_bound_accented_fires():
    v = check_language_class("café lighting, éclair glow",
                             field_class=ENGINE_BOUND)
    assert any(x.field_class == ENGINE_BOUND for x in v)


# ── human-review fields: any language accepted ────────────────────────

def test_human_review_chinese_clean():
    assert check_language_class("浓雾中的怪兽剪影",
                                field_class=HUMAN_REVIEW) == []


def test_human_review_english_clean():
    assert check_language_class("kaiju silhouette in fog",
                                field_class=HUMAN_REVIEW) == []


# ── bidirectional: English leaking into a LANG-SCOPED human field ─────

def test_bidirectional_english_in_scoped_field():
    # when a workflow lang is set (e.g. zh) and the field is
    # lang-scoped, English MIXING is flagged like theirs
    v = check_language_class("the kaiju rises 雾中",
                             field_class=HUMAN_REVIEW, workflow_lang="zh")
    assert any(x.field_class == HUMAN_REVIEW for x in v)
    # but pure-target-lang stays clean
    assert check_language_class("怪兽在雾中升起",
                                field_class=HUMAN_REVIEW,
                                workflow_lang="zh") == []
    # and English-only is fine when lang is en
    assert check_language_class("kaiju rises",
                                field_class=HUMAN_REVIEW,
                                workflow_lang="en") == []


# ── evidence class: verbatim, never translated ────────────────────────

def test_evidence_verbatim_match_passes():
    from gates.language_gate import EVIDENCE
    assert check_language_class(
        "「静止した街」", field_class=EVIDENCE,
        source_text="「静止した街」") == []


def test_evidence_translation_rejected():
    from gates.language_gate import EVIDENCE
    # translated evidence != source -> violation (it's not evidence)
    v = check_language_class("the silent city", field_class=EVIDENCE,
                             source_text="「静止した街」")
    assert any(x.field_class == EVIDENCE for x in v)


def test_evidence_without_source_loud_skip():
    """No source available to compare -> typed loud skip, never a
    silent pass."""
    from gates.language_gate import EVIDENCE, LanguageGateError, NO_SOURCE
    with pytest.raises(LanguageGateError) as ei:
        check_language_class("anything", field_class=EVIDENCE)
    assert ei.value.kind == NO_SOURCE


# ── empty input: typed, loud, distinct ────────────────────────────────

def test_empty_text_loud_skip():
    from gates.language_gate import LanguageGateError, EMPTY_TEXT
    with pytest.raises(LanguageGateError) as ei:
        check_language_class("", field_class=ENGINE_BOUND)
    assert ei.value.kind == EMPTY_TEXT
    with pytest.raises(LanguageGateError):
        check_language_class("  \n ", field_class=ENGINE_BOUND)


# ── field-class maps on the three signatures ──────────────────────────

def test_render_brief_field_classes_documented():
    from gates.language_gate import FIELD_CLASSES
    m = FIELD_CLASSES["RenderBrief"]
    # engine-bound: these feed the render engine
    for f in ("subject", "motion", "camera", "style",
              "audio_direction", "negatives", "identity_lock"):
        assert m[f] == ENGINE_BOUND, f


def test_profile_selector_field_classes():
    from gates.language_gate import FIELD_CLASSES
    m = FIELD_CLASSES["ProfileSelector"]
    assert m["decision"] == ENGINE_BOUND


def test_qc_field_classes():
    from gates.language_gate import FIELD_CLASSES
    m = FIELD_CLASSES["RenderQC"]
    # critique is engine/pipeline-bound JSON; notes is human-review
    assert m["critique"] == ENGINE_BOUND
    assert m["notes"] == HUMAN_REVIEW


def test_no_language_named_fields():
    """'never name a multilingual field after one language' — no
    *Zh/*En/*Local field names in the class maps (promptZh lesson)."""
    from gates.language_gate import FIELD_CLASSES
    for sig, m in FIELD_CLASSES.items():
        for f in m:
            assert not f.lower().endswith(("zh", "en", "local", "cn"))


# ── RenderBrief validation wiring ─────────────────────────────────────

def _brief(**over):
    from predict.prompt_director import RenderBrief
    base = dict(subject="a detective in fog", motion="walks forward",
                camera="dolly in", style="16mm grain")
    base.update(over)
    return RenderBrief(**base)


def test_brief_engine_bound_chinese_rejected():
    with pytest.raises(ValueError, match="engine-bound|English"):
        _brief(style="16mm 胶片")


def test_brief_english_clean():
    _brief()  # no raise


# ── registry fold-in: Pipeline -> PromptDirector.forward ──────────────

def test_director_forward_accepts_registry():
    from predict.prompt_director import PromptDirector
    import dspy

    class FakeLM(dspy.utils.DummyLM):
        pass

    lm = dspy.utils.DummyLM([
        {"reasoning": "r",
         "brief": ('{"subject":"a kaiju in fog","motion":"rises",'
                   '"camera":"slow push in","style":"16mm grain"}')}])
    d = PromptDirector()
    with dspy.settings.context(lm=lm):
        out = d.forward(intent="kaiju video", registry={"entities": []})
    assert out.brief.subject == "a kaiju in fog"


def test_pipeline_registry_passthrough():
    """Pipeline accepts a registry, threads it to director.forward so
    the no-names gate FIRES on the LM path."""
    from predict.pipeline import Pipeline
    import dspy

    lm = dspy.utils.DummyLM([
        {"reasoning": "r",
         "brief": ('{"subject":"Mira Chen looks at the fog",'
                   '"motion":"turns","camera":"push in",'
                   '"style":"16mm grain"}')}])
    registry = {"entities": [
        {"id": "e1", "name": "Mira Chen",
         "type": "character", "aliases": []}]}
    pipe = Pipeline(genre="surreal", director=None, selector=None,
                    registry=registry)
    pipe.creative_lm = lm
    # briefs stage: the LM brief carries a registry name -> the
    # no-names gate must fire (typed failure) rather than pass through
    with pytest.raises(Exception, match="proper noun|Mira"):
        pipe("a video about the detective")


def test_pipeline_no_registry_backward_compat():
    """No registry = current behavior (gate skips LOUDLY, warning)."""
    from predict.pipeline import Pipeline
    pipe = Pipeline(genre="surreal", director=None, selector=None)
    assert pipe.registry is None
