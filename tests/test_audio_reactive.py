"""hermes-86ad4c4a RED — typed AudioReactiveSpec/manifest contract for
the approved Ref2VA audio-reactive lane. Fails until
predict/audio_reactive.py exists.
"""
import json
import pathlib

import pytest

from predict.audio_reactive import (
    AudioReactiveSpec, AudioReactiveError, H3_AUDIO_POLICY,
)


def _mk(path, b=b"x"):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b)
    return str(p)


@pytest.fixture()
def spec(tmp_path):
    return AudioReactiveSpec(
        master_audio=_mk(tmp_path / "audio/master.wav"),
        vocal_stem=_mk(tmp_path / "audio/stems/vocals.wav"),
        vocal_map=_mk(tmp_path / "audio/vocal_map.json", b"{}"),
        audio_guide=_mk(tmp_path / "audio/guide.wav"),
        keeper_window_start_s=12.0,
        keeper_window_duration_s=8.0,
        qwen2_audio_model="qwen2-audio-7b-instruct",
    )


# ── construction IS validation (typed rejections) ────────────────────

def test_spec_is_frozen_and_defaults(spec):
    with pytest.raises(Exception):
        spec.master_audio = "x"
    assert spec.audio_prompt_type == "A"
    assert H3_AUDIO_POLICY == "discard_then_remux"
    assert spec.h3_audio_policy == H3_AUDIO_POLICY


def test_spec_rejects_missing_master_audio(spec, tmp_path):
    with pytest.raises(AudioReactiveError, match="master_audio"):
        AudioReactiveSpec(
            master_audio=str(tmp_path / "nope.wav"),
            vocal_stem=spec.vocal_stem, vocal_map=spec.vocal_map,
            audio_guide=spec.audio_guide,
            keeper_window_start_s=0.0,
            keeper_window_duration_s=8.0)


def test_spec_rejects_bad_window(spec):
    with pytest.raises(AudioReactiveError, match="keeper"):
        AudioReactiveSpec(
            master_audio=spec.master_audio, vocal_stem=spec.vocal_stem,
            vocal_map=spec.vocal_map, audio_guide=spec.audio_guide,
            keeper_window_start_s=-1.0, keeper_window_duration_s=8.0)
    with pytest.raises(AudioReactiveError, match="keeper"):
        AudioReactiveSpec(
            master_audio=spec.master_audio, vocal_stem=spec.vocal_stem,
            vocal_map=spec.vocal_map, audio_guide=spec.audio_guide,
            keeper_window_start_s=0.0, keeper_window_duration_s=0.0)


def test_spec_rejects_wrong_audio_prompt_type(spec):
    with pytest.raises(AudioReactiveError, match="A"):
        AudioReactiveSpec(
            master_audio=spec.master_audio, vocal_stem=spec.vocal_stem,
            vocal_map=spec.vocal_map, audio_guide=spec.audio_guide,
            keeper_window_start_s=0.0, keeper_window_duration_s=8.0,
            audio_prompt_type="T")


# ── manifest contract ────────────────────────────────────────────────

def test_manifest_roundtrip(spec, tmp_path):
    m = spec.to_manifest()
    json.dumps(m)  # must be plain JSON
    assert m["audio_prompt_type"] == "A"
    assert m["audio_guide"] == spec.audio_guide
    assert m["source"]["master_audio"] == spec.master_audio
    assert m["source"]["vocal_stem"] == spec.vocal_stem
    assert m["source"]["vocal_map"] == spec.vocal_map
    assert m["keeper_window"] == {"start_s": 12.0, "duration_s": 8.0}
    pol = m["policy"]
    assert pol["h3_audio"] == "discard_then_remux"
    assert pol["final_soundtrack"] == "master_audio"
    qc = m["qc"]
    for k in ("mouth_sync", "audio_quality", "visual_regression"):
        assert k in qc
    assert m["critic"]["model"] == spec.qwen2_audio_model


def test_manifest_from_doc_roundtrip(spec):
    rebuilt = AudioReactiveSpec.from_manifest(spec.to_manifest())
    assert rebuilt == spec


# ── Ref2VA settings preserve the REAL audio_guide path ───────────────

def test_ref2va_settings_carry_real_audio_guide(spec, tmp_path):
    from predict.render_profiles import Ref2VAProfile
    from predict.prompt_director import RenderBrief
    from predict.profile_selector import ProfileDecision

    refs = [_mk(tmp_path / "ref1.png")]
    brief = RenderBrief(subject="a detective", motion="walks",
                        camera="dolly in", style="16mm grain")
    dec = ProfileDecision(model="h3", resolution="768p",
                          shot_length_frames=107,
                          seed_policy="fixed_per_story",
                          wangp_profile="profile3")
    doc = Ref2VAProfile().build_settings(
        [brief], dec, image_refs=refs, audio_prompt_type="A",
        guide_duration_s=8.0, shot_duration_s=8.0, audio_spec=spec)
    assert doc["audio_prompt_type"] == "A"
    assert doc["audio_guide"] == spec.audio_guide  # the REAL path
    assert doc["audio_manifest"]["keeper_window"]["duration_s"] == 8.0
