"""Audio-guide data-plane contract for the Ref2VA profile."""
from pathlib import Path

import pytest

from predict.render_profiles import ProfileError, Ref2VAProfile
from predict.prompt_director import RenderBrief
from predict.profile_selector import ProfileDecision


def _brief():
    return RenderBrief(
        subject="a singer using <Picture 1> and <Audio 1>",
        motion="sings to the reference audio",
        camera="static medium close-up",
        style="natural film grain",
    )


def _decision():
    return ProfileDecision(
        model="h3",
        resolution="768p",
        shot_length_frames=107,
        seed_policy="fixed_per_story",
        wangp_profile="profile3",
    )


def _refs(tmp_path):
    image = Path(tmp_path) / "character.png"
    image.write_bytes(b"image")
    return [str(image)]


def test_ref2va_requires_a_readable_audio_guide(tmp_path):
    with pytest.raises(ProfileError, match="audio_guide"):
        Ref2VAProfile().build_settings(
            [_brief()], _decision(), image_refs=_refs(tmp_path),
            audio_prompt_type="A", audio_guide="/missing/guide.wav",
            guide_duration_s=8.0, shot_duration_s=8.0,
        )


def test_ref2va_emits_audio_guide_in_settings(tmp_path):
    guide = Path(tmp_path) / "guide.wav"
    guide.write_bytes(b"RIFF guide")
    doc = Ref2VAProfile().build_settings(
        [_brief()], _decision(), image_refs=_refs(tmp_path),
        audio_prompt_type="A", audio_guide=str(guide),
        guide_duration_s=8.0, shot_duration_s=8.0,
    )
    assert doc["audio_prompt_type"] == "A"
    assert doc["audio_guide"] == str(guide)
