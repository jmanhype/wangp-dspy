import pathlib

import pytest

from predict.continuation_lane import (
    JobConfigError, build_picture_n_speaker_prompt,
)
from services.chain.controller import build_chain_plan, emit_render_manifest


def _chars(tmp_path):
    # The controller only carries paths in this stage; adapter/profile gates
    # perform the file readback at render time.
    return [
        {"name": "Ada", "sn_tag": "S1", "description": "a pilot"},
        {"name": "Bo", "sn_tag": "S2", "description": "a mechanic"},
    ]


def test_builder_binds_one_speaker_and_one_silent_picture():
    prompt = build_picture_n_speaker_prompt(
        speaker_sn="S1", silent_sn="S2", line="The lights are back.")
    assert "S1 (Picture 1)" in prompt
    assert "S2 (Picture 2)" in prompt
    assert "only speaker" in prompt
    assert "lips closed" in prompt
    assert "<d>[English] The lights are back.</d>" in prompt


def test_builder_rejects_same_character_or_empty_line():
    with pytest.raises(JobConfigError, match="different"):
        build_picture_n_speaker_prompt(speaker_sn="S1", silent_sn="S1",
                                       line="hello")
    with pytest.raises(JobConfigError, match="non-empty"):
        build_picture_n_speaker_prompt(speaker_sn="S1", silent_sn="S2",
                                       line=" ")


def test_continuation_manifest_emits_typed_prompt(tmp_path):
    plan = build_chain_plan(
        [{"speaker": "Ada", "text": "The lights are back."}],
        _chars(tmp_path), [2.0], continuation_mode=True)
    manifest = emit_render_manifest(plan)
    assert "S1 (Picture 1)" in manifest[0]["prompt"]
    assert "S2 (Picture 2)" in manifest[0]["prompt"]
    assert "lips closed" in manifest[0]["prompt"]
