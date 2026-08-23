"""Audio critic slice 1 RED tests: schema, profiles, extractor.

Contract: docs/PROPOSAL_audio_critic_service.md.
Music prompt must be BYTE-IDENTICAL to the factory script default
(fetched from 3090:.../qwen2_audio_critic.py into a fixture).
"""
import json
import pathlib

import pytest

from qc.audio_critic.extract import extract_structured
from qc.audio_critic.profiles import PROFILES, MUSIC_SYSTEM_PROMPT
from qc.audio_critic.schema import (
    AudioCriticError, build_critique, validate_critique,
)

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


# ── schema: validation cases ──────────────────────────────────────

def _music_fields(**over):
    d = dict(schema="audio-critic/1", profile="music", score=31,
             score_scale=[0, 40], flags=["timing_drift"],
             reason="vocals slightly off-beat",
             decision="keeper_candidate",
             model="Qwen/Qwen2-Audio-7B-Instruct", parse_ok=True)
    d.update(over)
    return d


def test_valid_music_critique_passes():
    c = validate_critique(_music_fields())
    assert c["decision"] == "keeper_candidate"


def test_wrong_schema_string_rejected():
    with pytest.raises(AudioCriticError, match="schema"):
        validate_critique(_music_fields(schema="audio-critic/2"))


def test_missing_field_rejected():
    d = _music_fields()
    del d["reason"]
    with pytest.raises(AudioCriticError, match="reason"):
        validate_critique(d)


def test_score_out_of_profile_bounds_rejected():
    with pytest.raises(AudioCriticError, match="score"):
        validate_critique(_music_fields(score=41))
    with pytest.raises(AudioCriticError, match="score"):
        validate_critique(_music_fields(score=-1))


def test_score_scale_must_echo_profile():
    with pytest.raises(AudioCriticError, match="scale"):
        validate_critique(_music_fields(score_scale=[0, 100]))


def test_unknown_flag_closed_vocab_rejected():
    with pytest.raises(AudioCriticError, match="flag"):
        validate_critique(_music_fields(flags=["shiny_vocals"]))


def test_music_decision_enum():
    assert validate_critique(
        _music_fields(decision="reject"))["decision"] == "reject"
    with pytest.raises(AudioCriticError, match="decision"):
        validate_critique(_music_fields(decision="pass"))


def test_delivery_profile_decision_enum():
    d = dict(_music_fields(profile="delivery", decision="revise",
                           score_scale=[0, 40],
                           flags=["rushed_pacing"]))
    assert validate_critique(d)["decision"] == "revise"
    with pytest.raises(AudioCriticError, match="decision"):
        validate_critique(
            dict(d, decision="keeper_candidate"))


def test_unknown_profile_rejected():
    with pytest.raises(AudioCriticError, match="profile"):
        validate_critique(_music_fields(profile="poetry"))


def test_parse_ok_false_is_valid():
    assert validate_critique(
        _music_fields(parse_ok=False))["parse_ok"] is False


# ── profiles ──────────────────────────────────────────────────────

def test_both_profiles_registered_with_data():
    for name in ("music", "delivery"):
        p = PROFILES[name]
        assert p["system_prompt"]
        assert p["score_scale"] == [0, 40]
        assert p["flags"]  # closed vocab non-empty
        assert p["decisions"]


def test_music_prompt_byte_identical_to_factory_default():
    """The compatibility invariant (proposal, 'Music lane adoption
    WITHOUT behavior change'): same prompt text byte-for-byte."""
    script = (FIXTURES / "qwen2_audio_critic.py").read_text()
    # the argparse default, extracted the same way python would parse it
    import ast
    tree = ast.parse(script)
    default = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in getattr(node, "keywords", []):
                if kw.arg == "default" and \
                        isinstance(kw.value, ast.Constant) and \
                        isinstance(kw.value.value, str) and \
                        "0 to 40" in kw.value.value:
                    default = kw.value.value
    assert default is not None, "factory default prompt not found"
    assert MUSIC_SYSTEM_PROMPT.encode() == default.encode()


# ── extractor on recorded critiques ──────────────────────────────

def _prose(name):
    return json.loads(
        (FIXTURES / f"neonhearts_batch_{name}.json").read_text()
    )["critique"]


def test_extractor_001_offbeat_flags():
    out = extract_structured("music", _prose("001"))
    assert out["score_scale"] == [0, 40]
    assert "timing_drift" in out["flags"]  # "slightly off-beat"
    # recorded reality: 001's prose HEDGES ("challenging to give an
    # accurate score") — no score present, so parse_ok is correctly
    # False with the neutral fallback. This is the corpus teaching
    # us the parser's honesty contract.
    assert out["parse_ok"] is False


def test_extractor_002_score_and_flags():
    out = extract_structured("music", _prose("002"))
    assert out["score"] == 35               # "35 out of 40"
    assert "timing_drift" in out["flags"]    # "slight off-beat issue"
    assert out["decision"] in ("keeper_candidate", "reject")


def test_extractor_003_score_approx_keyword():
    out = extract_structured("music", _prose("003"))
    assert out["score"] == 38               # "approximately 38 out of 40"
    assert "timing_drift" in out["flags"]


def test_extractor_unknown_profile_typed_error():
    with pytest.raises(AudioCriticError):
        extract_structured("nope", "text")


def test_extractor_no_score_is_parse_not_ok():
    out = extract_structured("music", "no numbers here at all")
    assert out["parse_ok"] is False
    # build_critique must still produce a schema-valid record
    c = build_critique(out, model="Qwen/Qwen2-Audio-7B-Instruct")
    validate_critique(c)
