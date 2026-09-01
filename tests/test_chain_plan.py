"""Chain Plan schema tests — H3 last-frame chaining (RED first)."""
import pytest

from services.chain.plan import (
    ChainCharacter,
    ClipAudio,
    ChainClip,
    ChainPlan,
    SchemaError,
    validate_chain_plan,
)


def _chars():
    return (
        ChainCharacter(name="Ada", sn_tag="S1", description="engineer, red jacket"),
        ChainCharacter(name="Bo", sn_tag="S2", description="pilot, gray coat"),
    )


def _clip(index, speaker_sn="S1", duration_s=2.3333333333333335, frames=56,
          start_s=0.0, prev=None):
    return ChainClip(
        index=index,
        shot_prompt=f"{speaker_sn} speaks",
        speaker_sn=speaker_sn,
        duration_s=duration_s,
        frames=frames,
        audio=ClipAudio(path=f"audio/clip{index:04d}.wav", start_s=start_s,
                        padded_duration_s=duration_s),
        seed=1000 + index,
        status="pending",
        previous_clip_end_frame=prev,
    )


class TestChainCharacter:
    def test_rejects_empty_or_duplicate_sn(self):
        with pytest.raises(SchemaError):
            ChainCharacter(name="", sn_tag="S1", description="x")
        with pytest.raises(SchemaError):
            ChainCharacter(name="A", sn_tag="S1", description="")

    def test_sn_tag_format(self):
        with pytest.raises(SchemaError):
            ChainCharacter(name="A", sn_tag="ada", description="x")  # not SN

    def test_duplicate_sn_tags_rejected(self):
        with pytest.raises(SchemaError):
            ChainPlan(global_prompt="gp", characters=(
                ChainCharacter(name="A", sn_tag="S1", description="x"),
                ChainCharacter(name="B", sn_tag="S1", description="y"),
            ), clips=())


class TestChainPlan:
    def test_minimal_valid_plan(self):
        plan = ChainPlan(global_prompt="Throughout every scene S1 wears a red jacket.",
                         characters=_chars(),
                         clips=(_clip(1, speaker_sn="S1", start_s=0.0),))
        validate_chain_plan(plan)

    def test_valid_two_clip_chain(self):
        # clip 1: 56f full; clip 2: 56f full minus 22 overlap = 34f
        c2 = _clip(2, duration_s=34 / 24, frames=34, start_s=56 / 24,
                   prev={"clip_index": 1, "frame": 55})
        plan = ChainPlan(global_prompt="gp", characters=_chars(),
                         clips=(_clip(1), c2))
        validate_chain_plan(plan)

    def test_requires_global_prompt_and_clips(self):
        with pytest.raises(SchemaError):
            ChainPlan(global_prompt="", characters=_chars(), clips=(_clip(1),))
        with pytest.raises(SchemaError):
            ChainPlan(global_prompt="gp", characters=_chars(), clips=())

    def test_json_round_trip(self):
        plan = ChainPlan(global_prompt="gp", characters=_chars(),
                         clips=(_clip(1),
                                _clip(2, duration_s=34 / 24, frames=34,
                                      start_s=56 / 24,
                                      prev={"clip_index": 1, "frame": 55})))
        doc = plan.to_json()
        assert doc["clips"][1]["previous_clip_end_frame"]["clip_index"] == 1
        revived = ChainPlan.from_json(doc)
        assert revived == plan


class TestValidateChainPlan:
    def test_sn_tags_stable_across_clips(self):
        # S1 must always mean the same character: sn tags in clips must
        # exist in characters, and one sn tag cannot map to two names.
        clip = _clip(1, speaker_sn="S9")
        plan = ChainPlan(global_prompt="gp", characters=_chars(), clips=(clip,))
        with pytest.raises(SchemaError, match="S9"):
            validate_chain_plan(plan)

    def test_audio_starts_cumulative_and_aligned(self):
        bad = ChainPlan(global_prompt="gp", characters=_chars(), clips=(
            _clip(1, duration_s=2.3333333333333335, frames=56, start_s=0.0),
            _clip(2, duration_s=34 / 24, frames=34, start_s=99.0,
                  prev={"clip_index": 1, "frame": 55}),
        ))
        with pytest.raises(SchemaError, match="start_s"):
            validate_chain_plan(bad)

    def test_audio_padded_duration_must_match_clip(self):
        clip = _clip(1)
        object.__setattr__(clip.audio, "padded_duration_s", 5.0)
        plan = ChainPlan(global_prompt="gp", characters=_chars(), clips=(clip,))
        with pytest.raises(SchemaError, match="padded"):
            validate_chain_plan(plan)

    def test_frames_match_duration_at_fps(self):
        clip = _clip(1, frames=57)  # duration says 56 frames
        plan = ChainPlan(global_prompt="gp", characters=_chars(), clips=(clip,))
        with pytest.raises(SchemaError, match="frames"):
            validate_chain_plan(plan)

    def test_first_clip_full_later_clips_overlap_adjusted(self):
        overlap = 22
        # clip 2 with FULL frame count (overlap not subtracted) must fail
        clip2 = _clip(2, duration_s=2.3333333333333335, frames=56,
                      start_s=2.3333333333333335,
                      prev={"clip_index": 1, "frame": 55})
        plan = ChainPlan(global_prompt="gp", characters=_chars(),
                         clips=(_clip(1), clip2), overlap_frames=overlap)
        with pytest.raises(SchemaError, match="overlap"):
            validate_chain_plan(plan)

    def test_chaining_fields_required_after_clip_1(self):
        clip2 = _clip(2, duration_s=34 / 24, frames=34,
                      start_s=2.3333333333333335, prev=None)
        plan = ChainPlan(global_prompt="gp", characters=_chars(),
                         clips=(_clip(1), clip2))
        with pytest.raises(SchemaError, match="previous_clip_end_frame"):
            validate_chain_plan(plan)

    def test_clip1_must_not_have_prev_ref(self):
        clip1 = _clip(1, prev={"clip_index": 0, "frame": -1})
        plan = ChainPlan(global_prompt="gp", characters=_chars(), clips=(clip1,))
        with pytest.raises(SchemaError, match="previous_clip_end_frame"):
            validate_chain_plan(plan)

    def test_prev_ref_points_at_real_end_frame(self):
        clip2 = _clip(2, duration_s=34 / 24, frames=34,
                      start_s=2.3333333333333335,
                      prev={"clip_index": 1, "frame": 999})
        plan = ChainPlan(global_prompt="gp", characters=_chars(),
                         clips=(_clip(1), clip2))
        with pytest.raises(SchemaError, match="previous_clip_end_frame"):
            validate_chain_plan(plan)

    def test_shot_prompt_is_speaker_attributed(self):
        clip = _clip(1)
        object.__setattr__(clip, "shot_prompt", "someone talks")
        plan = ChainPlan(global_prompt="gp", characters=_chars(), clips=(clip,))
        with pytest.raises(SchemaError, match="shot_prompt"):
            validate_chain_plan(plan)

    def test_status_resume_safe(self):
        clip = _clip(1)
        object.__setattr__(clip, "status", "banana")
        plan = ChainPlan(global_prompt="gp", characters=_chars(), clips=(clip,))
        with pytest.raises(SchemaError, match="status"):
            validate_chain_plan(plan)
