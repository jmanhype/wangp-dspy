"""RED tests first (paivot TDD): PromptDirector signature + module.

WD-tq6z: DSPy Signature translating user intent into H3/WanGP render
briefs — structured sections (subject, motion, camera, style), NO
editor meta-hints (those belong to H3 shots only, per flux3
conventions). All tests use a stubbed LM (dspy DummyLM) — no GPU, no
real API calls.
"""
import json
import re

import dspy
import pytest

from predict.prompt_director import (
    RenderBrief, PromptDirector, RenderBriefSignature,
)

# ── stubbed LM responses ─────────────────────────────────────────────────
# DummyLM answers each Signature field in call order; we return a
# well-formed JSON brief so the module's parsing path is exercised.

GOOD_BRIEF = {
    "subject": "a lone astronaut in a cracked visor helmet",
    "motion": "slowly turns head left to right, dust drifting off shoulder",
    "camera": "slow dolly in from wide to medium, 24fps cinematic",
    "style": "16mm Ektachrome archival film grain, warm faded tones",
}

GOOD_LM_JSON = json.dumps(GOOD_BRIEF)


def _director_with_stub(answers):
    lm = dspy.utils.DummyLM(answers)
    director = PromptDirector()
    with dspy.context(lm=lm):
        yield director


# ── 1: signature shape ───────────────────────────────────────────────────

def test_signature_has_intent_input():
    # dspy 3.x: input_fields is a name -> FieldInfo dict
    assert "intent" in RenderBriefSignature.input_fields


def test_signature_output_is_a_single_brief_field():
    fields = RenderBriefSignature.output_fields
    assert "brief" in fields
    # the brief is ONE structured JSON output, not four free fields
    assert len(fields) == 1


# ── 2: brief schema validation (RED: RenderBrief does not exist yet) ────

def test_render_brief_requires_all_four_sections():
    with pytest.raises(Exception):
        RenderBrief(subject="s", motion="m", camera="c")  # style missing


def test_render_brief_rejects_empty_sections():
    with pytest.raises(Exception):
        RenderBrief(subject="", motion="m", camera="c", style="s")


def test_render_brief_valid_instance_has_sections():
    b = RenderBrief(**GOOD_BRIEF)
    assert b.subject and b.motion and b.camera and b.style


# ── 3: module behaviour with stub LM ─────────────────────────────────────

def test_director_returns_parsed_brief():
    director = PromptDirector()
    lm = dspy.utils.DummyLM([{"reasoning": "r", "brief": GOOD_LM_JSON}])
    with dspy.context(lm=lm):
        out = director(intent="astronaut on a dust-swept plain, archival look")
    assert isinstance(out.brief, RenderBrief)
    assert out.brief.subject == GOOD_BRIEF["subject"]
    assert out.brief.style == GOOD_BRIEF["style"]


def test_director_is_chain_of_thought():
    # ChainOfThought gives the LM a reasoning field before the output
    assert isinstance(PromptDirector(), dspy.ChainOfThought) or any(
        isinstance(b, dspy.ChainOfThought)
        for b in [getattr(PromptDirector(), "_predict", None)]
        if b is not None)


# ── 4: NO editor meta-hints (flux3 convention: those live in H3 shots) ──

META_HINT_TOKENS = re.compile(
    r"\b(cut|cuts|transition\w*|dissolve|flash|beat\s*grid|B[\s-]*roll|"
    r"montage|sfx|VO|voice[\s-]*over|lower[\s-]*third|title\s*card)\b", re.I)


def test_render_brief_schema_fields():
    import dataclasses
    names = {f.name for f in dataclasses.fields(RenderBrief)}
    assert names == {"subject", "motion", "camera", "style",
                     "audio_direction", "negatives", "identity_lock",
                     "registry",
                     "canon_citations"}  # provenance tiers (WD-oyti)


def test_craft_sections_are_optional_and_flow_into_prompt():
    from host.wangp_adapter import brief_to_prompt
    b = RenderBrief(**GOOD_BRIEF)
    p = brief_to_prompt(b)
    assert "Audio:" not in p and "Do not:" not in p  # absent = omitted
    b2 = RenderBrief(**GOOD_BRIEF,
                     audio_direction="sub-bass pulse, distant surf",
                     identity_lock="grey-white newsprint hull (inferred), "
                                   "ink bleed",
                     negatives="no morphs, no extra figures")
    p2 = brief_to_prompt(b2)
    assert "Audio: sub-bass pulse" in p2
    # provenance seam (WD-oyti): marker stripped at handoff-to-prompt
    assert "(inferred)" not in p2.lower()
    assert "Preserve throughout: grey-white newsprint hull, ink bleed" in p2
    assert "Do not: no morphs" in p2


def test_good_brief_contains_no_meta_hints():
    b = RenderBrief(**GOOD_BRIEF)
    for section in (b.subject, b.motion, b.camera, b.style):
        assert not META_HINT_TOKENS.search(section), section


def test_director_rejects_meta_hint_briefs():
    """WD-y9ab re-pin: meta-hint briefs previously "raised" only via
    the fallback-brief defect (the error text echoed 'cut', so the
    fallback itself raised). Real contract (module docstring): forward
    NEVER raises on LM content — a meta-hint brief becomes a zero-score
    '(invalid brief: ...)' prediction; the hint never reaches a prompt."""
    poisoned = dict(GOOD_BRIEF)
    poisoned["motion"] = "slow dolly in, then hard cut to close-up"
    director = PromptDirector()
    lm = dspy.utils.DummyLM([{"reasoning": "r",
                              "brief": json.dumps(poisoned)}])
    with dspy.context(lm=lm):
        pred = director(intent="x")
    assert pred.brief.subject.startswith("(invalid brief:")
    assert "cut" not in pred.brief.subject.lower()


# ── 5: malformed LM output fails loudly ──────────────────────────────────

def test_director_rejects_non_json_output():
    """WD-y9ab re-pin: non-JSON output previously raised only via the
    fallback defect. Real contract: zero-score '(invalid brief:)'
    fallback, never an exception."""
    director = PromptDirector()
    lm = dspy.utils.DummyLM([{"reasoning": "r",
                              "brief": "this is not json at all"}])
    with dspy.context(lm=lm):
        pred = director(intent="x")
    assert pred.brief.subject.startswith("(invalid brief:")


def test_director_rejects_missing_section_json():
    """WD-y9ab re-pin: this used to raise — but only accidentally, via
    the fallback-brief defect (empty motion sections / meta-hint words
    echoing from the error text made the '(invalid brief)' fallback
    itself raise). The real contract: forward NEVER raises on bad LM
    JSON; it returns a zero-score '(invalid brief: ...)' fallback."""
    partial = json.dumps({"subject": "s", "motion": "m"})
    director = PromptDirector()
    lm = dspy.utils.DummyLM([{"reasoning": "r", "brief": partial}])
    with dspy.context(lm=lm):
        pred = director(intent="x")
    assert pred.brief.subject.startswith("(invalid brief:")
    assert "missing sections" in pred.brief.subject


# ── M1 (GLM): meta-hint vocabulary gaps — one RED test per pattern ──────

def test_m1_b_roll_with_space_variant_rejected():
    poisoned = dict(GOOD_BRIEF)
    poisoned["style"] = "grainy doc look with B roll inserts"
    with pytest.raises(Exception):
        RenderBrief(**poisoned)


def test_m1_broll_compound_rejected():
    poisoned = dict(GOOD_BRIEF)
    poisoned["motion"] = "subject walks; Broll of feet intercut"[:34]
    with pytest.raises(Exception):
        RenderBrief(**poisoned)


def test_m1_lower_third_with_space_rejected():
    poisoned = dict(GOOD_BRIEF)
    poisoned["subject"] = "news anchor with lower third chyron"
    with pytest.raises(Exception):
        RenderBrief(**poisoned)


def test_m1_voice_over_with_space_rejected():
    poisoned = dict(GOOD_BRIEF)
    poisoned["motion"] = "talks to camera, voice over narration"
    with pytest.raises(Exception):
        RenderBrief(**poisoned)


def test_m1_transitional_word_rejected():
    """transition\w* must catch 'transitional', not just 'transition'."""
    poisoned = dict(GOOD_BRIEF)
    poisoned["camera"] = "transitional whip pan between setups"
    with pytest.raises(Exception):
        RenderBrief(**poisoned)


def test_wd9dia_lighting_vocabulary_not_flagged():
    """WD-9dia: lighting sense of 'flash'/'cut' is legitimate
    cinematography language, not an editing meta-hint."""
    from predict.prompt_director import _META_HINT_RE, RenderBrief
    legit = [
        "muzzle flash lights the alley as the shot fires",
        "lightning flash illuminates the harbor",
        "the lighthouse beam cuts through fog",  # 'cuts through' light
        "strobe flash exposure on the dance floor",
        "camera flash photography aesthetic",
    ]
    for s in legit:
        assert not _META_HINT_RE.search(s), f"false positive: {s!r}"


def test_wd9dia_editing_operations_still_flagged():
    from predict.prompt_director import _META_HINT_RE
    editing = [
        "hard cut to black",
        "jump cuts between angles",
        "cut to the wide shot",
        "cutting away to the crowd",
        "flash cut between timelines",
        "dissolve into the dream sequence",
        "montage of the city",
        "title card appears",
    ]
    for s in editing:
        assert _META_HINT_RE.search(s), f"missed editing op: {s!r}"


# ── WD-y9ab: fallback briefs must never fail validation ───────────
def test_wd_y9ab_invalid_brief_fallback_survives_meta_hint():
    """The '(invalid brief: ...)' fallback embeds the raw rejection
    message; if that message contains a meta-hint word (e.g. a gold
    'dissolve' rejection), the fallback RenderBrief itself raises and
    PromptDirector.forward's cannot-raise contract breaks (live crash
    2026-08-29, WD-y9ab baseline run). The fallback must sanitize."""
    from predict.prompt_director import PromptDirector
    d = PromptDirector()
    from dspy.utils import DummyLM as FakeLM  # noqa

    class ExplodingLM:
        """Returns valid JSON whose motion contains 'dissolve' so
        _parse_brief raises a meta-hint ValueError mentioning it."""
        def __call__(self, **kw):
            return dspy.Prediction(
                reasoning="r",
                brief='{"subject": "a paper boat", "motion": '
                      '"slow dissolve into dream logic", "camera": '
                      '"macro static", "style": "muted"}')

    d.predict = ExplodingLM()
    with dspy.context(lm=FakeLM([{}])):
        pred = d(intent="a paper boat drifting")
    s = pred.brief.subject
    assert s.startswith("(invalid brief:")
    assert "dissolve" not in s
    for f in ("motion", "camera", "style"):
        assert getattr(pred.brief, f) == "(invalid)"
    # LM-failure fallback core sections must be nonempty too (y9ab crash)
    pred2 = PromptDirector.__new__(PromptDirector)
    from predict.prompt_director import RenderBrief
    fb = RenderBrief(subject="(lm failure: X)", motion="(lm failure)",
                     camera="(lm failure)", style="(lm failure)")
    assert all(getattr(fb, f).strip() for f in
               ("subject", "motion", "camera", "style"))


def test_wd_y9ab_lm_failure_fallback_survives_meta_hint():
    """Same contract for the LM-failure fallback: exception text can
    quote meta-hint words; subject must not echo them."""
    from predict.prompt_director import PromptDirector
    from dspy.utils import DummyLM as FakeLM  # noqa
    d = PromptDirector()

    class ExplodingLM:
        def __call__(self, **kw):
            raise RuntimeError("dissolve cut montaged: boom")

    d.predict = ExplodingLM()
    with dspy.context(lm=FakeLM([{}])):
        pred = d(intent="anything")
    assert "dissolve" not in pred.brief.subject
    assert pred.brief.subject.startswith("(lm failure:")
