"""H3 production-recipe module tests (2026-09-01 verified recipe).

RED->GREEN TDD for services/director/renderers/h3_recipe.py encoding the
user-eye-verified MiniMax H3 Ref2VA multi-character two-shot recipe.
"""
from __future__ import annotations

import pytest

from services.director.renderers.h3_recipe import (
    H3RecipeError,
    build_render_config,
)


def _plates():
    return [
        {"path": "/renders/charA_identity.png",
         "description": "a weathered woman with silver braids, seated left"},
        {"path": "/renders/charB_identity.png",
         "description": "a lean man with soot-streaked cheeks, standing right"},
    ]


def _build(**over):
    kw = dict(
        anchor_plate="/renders/twoshot_anchor.png",
        character_plates=_plates(),
        speaker_index=0,
        line="The lamp will hold till morning.",
        audio_path="/audio/line.wav",
        duration_s=73 / 24.0,
        scene_staging="two characters framed left and right across the table",
        listening_detail="head tilted, eyes on the speaker",
        ambience="room tone, faint brazier crackle",
    )
    kw.update(over)
    return build_render_config(**kw)


# ------------------------------------------------------------- happy path

def test_config_exact_wgp_envelope():
    out = _build()
    cfg = out["config"]
    assert cfg["image_refs"] == [
        "/renders/twoshot_anchor.png",
        "/renders/charA_identity.png",
        "/renders/charB_identity.png",
    ]
    assert cfg["width"] == 480 and cfg["height"] == 832
    assert cfg["frames"] == 73
    assert cfg["seed"] == 904
    assert cfg["profile"] == 3
    assert cfg["attention"] == "sdpa"
    assert cfg["audio_prompt_type"] == "A"
    assert cfg["audio_guide"] == "/audio/line.wav"
    assert cfg["audio_pad"] == "apad to exact grid duration"
    assert cfg["inference_steps"] == 20
    assert cfg["skip_steps_cache_type"] == "spectrum"
    assert cfg["skip_steps_multiplier"] == 0.08


def test_prompt_template_structure_exact():
    p = _build()["prompt"]
    head = (
        "<Picture 1> is the two-shot composition anchor: two characters "
        "framed left and right across the table.\n"
        "\n"
        "<Subject 1> (from <Picture 2>):\n"
        "a weathered woman with silver braids, seated left\n"
        "\n"
        "<Subject 2> (from <Picture 3>):\n"
        "a lean man with soot-streaked cheeks, standing right"
    )
    assert p.startswith(head)
    assert ("Summary: [reference generation] The composition of "
            "<Picture 1> holds: both characters in their positions. "
            "All subjects retain their exact identities from their "
            "reference pictures. <Subject 1> speaks with lively animated "
            "mouth movement: (S1) says: <d>[English] The lamp will hold "
            "till morning.</d> <Subject 2> listens, mouth closed, head "
            "tilted, eyes on the speaker.") in p
    assert p.rstrip().endswith(
        "Non-diegetic music: none. Ambient: room tone, faint brazier crackle.")


def test_prompt_speaker_tag_matches_speaker_index():
    # speaker_index=1 -> (S2) speaks, Subject 1 listens
    p = _build(speaker_index=1)["prompt"]
    assert "(S2) says: <d>[English]" in p
    assert "<Subject 2> speaks with lively animated mouth movement" in p
    assert "<Subject 1> listens, mouth closed" in p
    assert "(S1) says:" not in p


def test_anchor_is_picture_1_identities_from_pictures_2_3():
    p = _build()["prompt"]
    assert p.index("<Picture 2>") < p.index("silver braids")
    assert "<Subject 2> (from <Picture 3>)" in p


# ------------------------------------------------------------- assertions

def test_speaker_index_out_of_range_rejected():
    with pytest.raises(H3RecipeError, match="speaker_index"):
        _build(speaker_index=2)


def test_empty_line_rejected():
    with pytest.raises(H3RecipeError, match="line"):
        _build(line="   ")


def test_no_template_placeholder_leaks():
    p = _build()["prompt"]
    for token in ("<line>", "<charA description>", "<charB description>",
                  "<scene staging description>", "<listening detail>",
                  "<ambience>", "PLACEHOLDER", "TODO"):
        assert token not in p, token


def test_line_actually_bound_in_d_block():
    p = _build(line="Trust the quiet ones.")["prompt"]
    assert "<d>[English] Trust the quiet ones.</d>" in p


def test_empty_description_rejected():
    plates = _plates()
    plates[0]["description"] = " "
    with pytest.raises(H3RecipeError, match="description"):
        _build(character_plates=plates)


# ------------------------------------------------------------- grid

def test_frames_on_grid_56():
    out = _build(duration_s=56 / 24.0)
    assert out["config"]["frames"] == 56


def test_off_grid_duration_rejected():
    with pytest.raises(H3RecipeError, match="grid"):
        _build(duration_s=3.1)


# ------------------------------------------------------------- turbo gate

def test_turbo_lora_multi_ref_rejected():
    with pytest.raises(H3RecipeError, match="turbo"):
        _build(loras=["wan2gp_turbo_ckpt"])


def test_turbo_lora_single_ref_closeup_allowed():
    out = _build(character_plates=_plates()[:1], speaker_index=0,
                 loras=["wan2gp_turbo_ckpt"])
    assert "turbo" in str(out["config"]["loras"])


def test_non_turbo_lora_multi_ref_allowed():
    out = _build(loras=["style_lora_v2"])
    assert out["config"]["loras"] == ["style_lora_v2"]


# ------------------------------------------------------------- banned language

def test_retention_language_banned_in_line():
    with pytest.raises(H3RecipeError, match="fully preserved"):
        _build(line="The composition is fully preserved.")


def test_retention_language_banned_in_description():
    plates = _plates()
    plates[1]["description"] = "a man whose look continues directly"
    with pytest.raises(H3RecipeError, match="continues directly"):
        _build(character_plates=plates)


# ------------------------------------------------------------- banned assets

def test_gpt_image_anchor_rejected():
    with pytest.raises(H3RecipeError, match="gpt-image"):
        _build(anchor_plate="/renders/gpt-image-anchor.png")


def test_gpt_image_identity_plate_rejected():
    plates = _plates()
    plates[0]["path"] = "/plates/GPT-Image_charA.png"
    with pytest.raises(H3RecipeError, match="[Gg][Pp][Tt]-?[Ii]mage"):
        _build(character_plates=plates)


def test_sage_attention_rejected():
    with pytest.raises(H3RecipeError, match="sage"):
        _build(attention="sage")


# ------------------------------------------------------------- continuous

def test_continuous_lines_timestamped_attribution():
    cont = [
        {"shot": 1, "timestamp": "00:00:000", "speaker_index": 0,
         "line": "First line here."},
        {"shot": 2, "timestamp": "00:02:333", "speaker_index": 1,
         "line": "Second line back."},
    ]
    p = _build(continuous_lines=cont)["prompt"]
    assert ("[Shot 1] At 00:00:000 <Subject 1> (S1) says: "
            "<d>[English] First line here.</d>") in p
    assert ("[Shot 2] At 00:02:333 <Subject 2> (S2) says: "
            "<d>[English] Second line back.</d>") in p
    assert p.index("[Shot 1]") < p.index("[Shot 2]")


def test_continuous_line_speaker_index_validated():
    with pytest.raises(H3RecipeError, match="speaker_index"):
        _build(continuous_lines=[
            {"shot": 1, "timestamp": "00:00:000", "speaker_index": 5,
             "line": "x"}])


def test_determinism():
    assert _build() == _build()
