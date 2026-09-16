"""Tests for predict/continuation_lane.py — validated Mode A/B fields + transcript judge."""
import pytest

from predict.continuation_lane import (
    ContinuationExtras, transcript_match_score, transcript_wer,
    transcript_judge, JobConfigError)


class TestContinuationExtras:
    def test_mode_b_valid(self):
        e = ContinuationExtras(image_start="/x/seed.png", image_refs=["/x/seed.png"],
                               audio_guide="/x/t1.wav")
        d = e.to_extra()
        assert d["image_prompt_type"] == "S"
        assert d["audio_policy"]["discard_rendered_audio"] is False

    def test_mode_a_valid(self):
        e = ContinuationExtras(audio_prompt_type="", image_start="/x/plate.png",
                               video_prompt_type="")
        d = e.to_extra()
        assert "audio_guide" not in d

    def test_persisted_envelope_round_trips_through_canonical_loader(self):
        original = ContinuationExtras(
            image_start="/x/seed.png",
            image_refs=["/x/seed.png", "/x/silent.png"],
            audio_guide="/x/t1.wav",
        )
        persisted = original.to_extra()
        restored = ContinuationExtras.from_dict(persisted)
        assert restored == original
        assert restored.to_extra() == persisted

    def test_audio_without_guide_rejected(self):
        with pytest.raises(JobConfigError):
            ContinuationExtras(audio_prompt_type="A", image_start="/x/s.png").validate()

    def test_g4_violation_rejected(self):
        with pytest.raises(JobConfigError):
            ContinuationExtras(image_start="/x/s.png", audio_guide="/x/a.wav",
                               audio_policy_discard_rendered=True).validate()

    def test_bad_image_prompt_type(self):
        with pytest.raises(JobConfigError):
            ContinuationExtras(image_prompt_type="TSEVL").validate()


class TestTranscriptJudge:
    def test_perfect_match(self):
        assert transcript_match_score("have a cookie", "Have a cookie!") == 1.0

    def test_partial(self):
        s = transcript_match_score("hush now dear suffering breakfast cookie",
                                   "Oh hush now, dear. Have a cookie.")
        assert 0.3 <= s <= 0.8

    def test_empty_intended(self):
        assert transcript_match_score("anything", "") == 0.0

    def test_repetition_insertions_are_penalized(self):
        intended = "This is the last rain we have."
        repeated = "This is the last, this is the last grain we have."
        assert transcript_wer(repeated, intended) > 0.5
        assert transcript_match_score(repeated, intended) < 0.5

    def test_validated_whisper_mishears_still_pass(self):
        assert transcript_match_score(
            "matey, I am on fight!", "Lady, I am on fire!") >= 0.6
        assert transcript_match_score(
            "Who hushed now, dear? Have a cookie.",
            "Oh hush now, dear. Have a cookie.") >= 0.6

    def test_judge_pass_and_fail(self):
        turns = ["the water is leaving the harbor", "say again post six"]
        good = transcript_judge({}, said="the water is leaving the harbor say again post six",
                                intended_turns=turns)
        assert good["passes"] is True
        bad = transcript_judge({}, said="completely unrelated gibberish",
                               intended_turns=turns)
        assert bad["passes"] is False
