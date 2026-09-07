import pathlib

import pytest

from qc.audio_critic.ref2va_stage import (
    Ref2VAQCStageError, run_ref2va_qc_stage,
)
from qc.audio_critic.vision_judge import VisionJudgeError, run_vision_judge


def _doc(tmp_path):
    paths = []
    for name in ("guide.wav", "master.wav", "stem.wav", "map.json"):
        p = pathlib.Path(tmp_path) / name
        p.write_bytes(b"x")
        paths.append(str(p))
    return {
        "audio_guide": paths[0],
        "audio_provenance": {
            "source_master": paths[1], "vocal_stem": paths[2],
            "whisper_map": paths[3], "keeper_window_s": [0.0, 2.0],
        },
        "audio_policy": {"discard_rendered_audio": True},
    }


def test_vision_judge_requires_mouth_action_and_speaker_alignment():
    evidence = run_vision_judge(
        "cut.mp4", expected_speaker="S1", expected_action="turns toward gate",
        judge=lambda **_: {"mouth_sync": 0.9, "action_match": 0.8,
                           "speaker_attribution": 0.95})
    assert evidence.passed is True
    assert evidence.mouth_sync == 0.9


def test_vision_judge_rejects_low_alignment():
    with pytest.raises(VisionJudgeError, match="visual gate failed"):
        run_vision_judge(
            "cut.mp4", expected_speaker="S1", expected_action="turns",
            judge=lambda **_: {"mouth_sync": 0.6, "action_match": 0.9,
                               "speaker_attribution": 0.9})


def test_qc_stage_persists_integrated_vision_evidence(tmp_path):
    qc = run_ref2va_qc_stage(
        _doc(tmp_path), judge=None, video_path="cut.mp4",
        expected_speaker="S1", expected_action="turns toward gate",
        vision_judge=lambda **_: {"mouth_sync": 0.9, "action_match": 0.9,
                                  "speaker_attribution": 0.9})
    assert qc.vision_judge["passed"] is True


def test_qc_stage_rejects_requested_vision_without_judge(tmp_path):
    """Supplying video expectations makes vision mandatory, not optional."""
    with pytest.raises(Ref2VAQCStageError,
                       match="vision judge is not wired; refusing ungated video"):
        run_ref2va_qc_stage(
            _doc(tmp_path), judge=None, video_path="cut.mp4",
            expected_speaker="S1", expected_action="turns", vision_judge=None)
