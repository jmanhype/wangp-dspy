"""WD-7185 RED tests — common-actions anti-mush gate.

Doctrine: script-pass L10-18 (pass-methodology-outline.md section 4) +
RUBRIC A4.2 — "is this action common in real-life video?" ZERO-MODEL.
"""
import json
import pytest

from gates.common_actions import (
    ActionViolation, check_common_actions, load_actions_registry,
)


# ── each seeded category fires on positive samples ────────────────────

def test_physics_category_fires():
    for text in ("a pole blocks the falling crate",
                 "dominoes chain across the table",
                 "the ball ricochets off the pipe"):
        v = check_common_actions(text)
        assert any(x.category == "physics" for x in v), text


def test_micro_expression_category_fires():
    for text in ("a flicker of doubt crosses her face",
                 "a slight twitch of his eye",
                 "a barely-there smile"):
        v = check_common_actions(text)
        assert any(x.category == "micro_expression" for x in v), text


def test_fine_displacement_category_fires():
    for text in ("he moves one inch closer",
                 "she tilts her head by a degree",
                 "a subtle shift in his stance"):
        v = check_common_actions(text)
        assert any(x.category == "fine_displacement" for x in v), text


# ── case-insensitivity + word-boundary anchoring pinned ──────────────

def test_case_insensitive():
    v = check_common_actions("A FLICKER OF DOUBT")
    assert any(x.category == "micro_expression" for x in v)


def test_word_boundary_no_substring_fires():
    # risky substrings inside safe common words must NOT fire
    for text in ("walking through the marketplace",   # 'inch' absent
                 "she smiles warmly at the crowd",     # not 'barely-there'
                 "domino theory discussion",           # no domino CHAIN
                 ):
        v = check_common_actions(text)
        assert v == [], (text, v)


def test_inch_substring_does_not_fire():
    # 'inch' inside 'inches forward slowly'? — 'one inch closer' is the
    # pattern; plain 'inches' alone is not
    v = check_common_actions("the door inches open")
    assert v == []


# ── violation shape ───────────────────────────────────────────────────

def test_violation_shape():
    v = check_common_actions("a flicker of doubt")
    assert len(v) == 1
    x = v[0]
    assert isinstance(x, ActionViolation)
    assert x.id
    assert x.category in ("physics", "micro_expression",
                          "fine_displacement")
    assert x.matched_text
    assert isinstance(x.span, tuple) and len(x.span) == 2
    s, e = x.span
    assert "a flicker of doubt"[s:e] == "a flicker of doubt"[s:e]


# ── clean text: safe actions do NOT fire (SAFE list is NOT required) ─

def test_safe_actions_clean():
    for text in ("she walks to the window and sits down",
                 "he opens the door, nods, and hands over the folder",
                 "typing at a laptop, drinking coffee"):
        assert check_common_actions(text) == []


# ── empty input: typed, loud, distinct ────────────────────────────────

def test_empty_text_distinct_typed():
    from gates.common_actions import EMPTY_TEXT
    with pytest.raises(Exception) as ei:
        check_common_actions("")
    assert getattr(ei.value, "kind", None) == EMPTY_TEXT


def test_whitespace_text_distinct_typed():
    from gates.common_actions import EMPTY_TEXT
    with pytest.raises(Exception) as ei:
        check_common_actions("   \n  ")
    assert getattr(ei.value, "kind", None) == EMPTY_TEXT


# ── registry file loads + schema ──────────────────────────────────────

def test_registry_loads_and_validates():
    reg = load_actions_registry("datasets/common-actions.json")
    assert isinstance(reg.get("safe"), list) and reg["safe"]
    risky = reg["risky"]
    assert risky
    cats = {r["category"] for r in risky}
    assert cats == {"physics", "micro_expression", "fine_displacement"}
    for r in risky:
        assert r.get("id") and r.get("pattern") and r.get("rationale")


# ── brief rejection through PromptDirector's path ─────────────────────

def _brief(**over):
    from predict.prompt_director import RenderBrief
    base = dict(subject="a detective", motion="walks to the desk",
                camera="dolly in", style="16mm grain")
    base.update(over)
    return RenderBrief(**base)


def test_brief_with_risky_motion_rejected():
    with pytest.raises(ValueError, match="common.action"):
        _brief(motion="a flicker of doubt crosses his face")


def test_brief_with_risky_subject_rejected():
    with pytest.raises(ValueError, match="common.action"):
        _brief(subject="a pole blocks the crate")


def test_clean_brief_passes():
    _brief()  # no raise


def test_gate_always_active_no_disable_knob_needed():
    """Patterns are bundled with the module — the gate is always on
    (documented decision; no registry= None skip like no-names)."""
    from predict.prompt_director import RenderBrief
    b = RenderBrief(subject="x", motion="tilts by a degree",
                    camera="static", style="grain")
    with pytest.raises(ValueError):
        RenderBrief(subject="x", motion=b.motion, camera="c",
                    style="s")  # default path, no registry arg


# ── CLI ───────────────────────────────────────────────────────────────

def test_cli_inline_text_violation(capsys):
    from scripts.check_common_actions import main
    assert main(["a flicker of doubt"]) == 1
    out = capsys.readouterr().out
    assert "micro_expression" in out or "flicker" in out


def test_cli_inline_text_clean(capsys):
    from scripts.check_common_actions import main
    assert main(["she walks to the door"]) == 0


def test_cli_file_input(tmp_path, capsys):
    from scripts.check_common_actions import main
    p = tmp_path / "t.txt"
    p.write_text("he moves one inch closer")
    assert main([str(p)]) == 1


def test_cli_usage_error(capsys):
    from scripts.check_common_actions import main
    assert main(["/nonexistent/file.txt"]) == 2
