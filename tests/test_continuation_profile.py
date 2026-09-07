"""Grid-aligned Ref2Va continuation profile: 56 frames / ~2.33 seconds."""
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
        keeper_window_s=(0.0, 56 / 24),
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
        shot_length_frames=56,
        seed_policy="fixed_per_shot",
        wangp_profile="profile3",
        continuation=True,
    )
    return image, wav, prov, brief, decision


def test_continuation_profile_emits_grid_aligned_56_frames(tmp_path):
    from predict.render_profiles import Ref2VAProfile

    image, wav, prov, brief, decision = _inputs(tmp_path)
    doc = Ref2VAProfile().build_settings(
        [brief],
        decision,
        image_refs=[str(image)],
        audio_prompt_type="A",
        guide_duration_s=56 / 24,
        shot_duration_s=56 / 24,
        audio_guide=str(wav),
        audio_provenance=prov,
        audio_length_frames=56,
        image_start=str(image),
        continuation=True,
    )
    assert doc["requested_frames"] == 56
    assert doc["video_length"] == 56
    assert doc["frames_per_shot"] == 56


def test_continuation_frame_normalizer_snaps_48_up_and_keeps_grid_values():
    from predict.job_config import normalize_continuation_frame_count

    assert normalize_continuation_frame_count(48) == 56
    assert normalize_continuation_frame_count(56) == 56
    assert normalize_continuation_frame_count(57) == 73


def test_continuation_profile_rejects_off_grid_duration(tmp_path):
    from predict.render_profiles import ProfileError, Ref2VAProfile

    image, wav, prov, brief, decision = _inputs(tmp_path)
    with pytest.raises(ProfileError, match="grid-aligned"):
        Ref2VAProfile().build_settings(
            [brief],
            decision,
            image_refs=[str(image)],
            audio_prompt_type="A",
            guide_duration_s=2.5,
            shot_duration_s=2.5,
            audio_guide=str(wav),
            audio_provenance=prov,
            audio_length_frames=60,
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


def test_profile_decision_allows_56_frame_continuation():
    from predict.profile_selector import ProfileDecision

    decision = ProfileDecision(
        model="h3",
        resolution="768p",
        shot_length_frames=56,
        seed_policy="fixed_per_shot",
        wangp_profile="profile3",
        continuation=True,
    )
    assert decision.continuation is True
