"""Exact Ref2Va continuation profile: 48 frames / 2 seconds."""
from __future__ import annotations

import pytest


def _inputs(tmp_path):
    from predict.audio_dataplane import AudioGuideProvenance
    from predict.prompt_director import RenderBrief
    from predict.profile_selector import ProfileDecision

    image = tmp_path / "frame.png"
    wav = tmp_path / "turn.wav"
    for path in (image, wav):
        path.write_bytes(b"fixture")
    prov = AudioGuideProvenance(
        source_master=str(wav),
        vocal_stem=str(wav),
        whisper_map=str(wav),
        keeper_window_s=(0.0, 2.0),
    )
    brief = RenderBrief(
        subject="a silent character",
        motion="listens while the speaker talks",
        camera="static medium shot",
        style="cinematic",
    )
    decision = ProfileDecision(
        model="h3",
        resolution="768p",
        shot_length_frames=48,
        seed_policy="fixed_per_shot",
        wangp_profile="profile3",
        continuation=True,
    )
    return image, wav, prov, brief, decision


def test_continuation_profile_emits_exact_48_frames(tmp_path):
    from predict.render_profiles import Ref2VAProfile

    image, wav, prov, brief, decision = _inputs(tmp_path)
    doc = Ref2VAProfile().build_settings(
        [brief],
        decision,
        image_refs=[str(image)],
        audio_prompt_type="A",
        guide_duration_s=2.0,
        shot_duration_s=2.0,
        audio_guide=str(wav),
        audio_provenance=prov,
        audio_length_frames=48,
        continuation=True,
    )
    assert doc["requested_frames"] == 48
    assert doc["video_length"] == 48
    assert doc["frames_per_shot"] == 48


def test_continuation_profile_rejects_non_48_frame_duration(tmp_path):
    from predict.render_profiles import ProfileError, Ref2VAProfile

    image, wav, prov, brief, decision = _inputs(tmp_path)
    with pytest.raises(ProfileError, match="exactly 48"):
        Ref2VAProfile().build_settings(
            [brief],
            decision,
            image_refs=[str(image)],
            audio_prompt_type="A",
            guide_duration_s=2.333,
            shot_duration_s=2.333,
            audio_guide=str(wav),
            audio_provenance=prov,
            audio_length_frames=56,
            continuation=True,
        )


def test_generic_job_config_still_rejects_sub_floor_48():
    from predict.job_config import JobConfigError, WanGPJobConfig

    with pytest.raises(JobConfigError, match="floor"):
        WanGPJobConfig(
            model_type="minimax_h3_fl2va_pruned",
            script="one shot",
            frames_per_shot=48,
        )
