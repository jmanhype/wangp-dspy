import json
import hashlib
import math
import pathlib

import pytest

from qc.audio_critic.ref2va_stage import (
    Ref2VAQCStageError, run_ref2va_qc_stage,
)
from qc.audio_critic.vision_judge import VisionJudgeError, run_vision_judge


def _sync_evidence(**overrides):
    payload = {
        "method": "syncnet_v2_multicrop/v1",
        "model_sha256": (
            "961e8696f888fce4f3f3a6c3d5b3267cf5b343100b238e79b2659bff2c605442"),
        "offset_frames_25fps": 0,
        "offset_seconds": 0.0,
        "confidence": 2.0,
        "passed": True,
        "phonetic_sync_verified": False,
        "crop_results": [],
    }
    payload.update(overrides)
    return payload


def _mouth_bboxes():
    return [[.315, .205, .025, .015], [.31, .19, .02, .03],
            [.27, .19, .02, .01]]


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
        judge=lambda **_: {"mouth_activity": 0.9, "action_match": 0.8,
                           "speaker_attribution": 0.95,
                           "speaker_mouth_bboxes": _mouth_bboxes()})
    assert evidence.passed is True
    assert evidence.mouth_sync is None
    assert evidence.mouth_activity == 0.9
    assert evidence.av_sync_verified is False
    assert evidence.speaker_mouth_bboxes == tuple(
        tuple(bbox) for bbox in _mouth_bboxes())
    assert evidence.speaker_mouth_bbox == (.31, .19, .02, .015)
    assert evidence.speaker_mouth_center_spread == pytest.approx(
        (.0475, .0175))


def test_vision_judge_rejects_low_alignment():
    raw_response = '{"mouth_activity": 0.9, "action_match": 0.6, "speaker_attribution": 0.9}'
    with pytest.raises(VisionJudgeError, match="visual gate failed") as caught:
        run_vision_judge(
            "cut.mp4", expected_speaker="S1", expected_action="turns",
            judge=lambda **_: {"mouth_activity": 0.9, "action_match": 0.6,
                               "speaker_attribution": 0.9,
                               "speaker_mouth_bboxes": _mouth_bboxes(),
                               "raw_response": raw_response})
    assert caught.value.scores == {
        "mouth_activity": 0.9, "action_match": 0.6,
        "speaker_attribution": 0.9,
    }
    assert caught.value.raw_response == raw_response


def test_vision_judge_accepts_valid_moving_mouth_boxes():
    evidence = run_vision_judge(
        "cut.mp4", expected_speaker="S1", expected_action="speaks",
        judge=lambda **_: {
            "mouth_activity": 0.9, "action_match": 0.9,
            "speaker_attribution": 0.9,
            "speaker_mouth_bboxes": _mouth_bboxes()})
    assert evidence.passed is True
    assert evidence.speaker_mouth_center_spread == pytest.approx(
        (.0475, .0175))
    assert evidence.speaker_mouth_bbox == (.31, .19, .02, .015)


@pytest.mark.parametrize(
    ("bboxes", "message"),
    [
        (None, "must include three speaker_mouth_bboxes"),
        ([.2, .3, .05, .05], "must include three speaker_mouth_bboxes"),
        ([[.2, .3, .05, .05], [.21, .31, .05, .05]],
         "must include three speaker_mouth_bboxes"),
        ([[.2, .3, .05, .05], [.21, "bad", .05, .05],
          [.2, .32, .06, .05]], "values must be numeric"),
        ([[.2, .3, True, .05], [.21, .31, .05, .05],
          [.2, .32, .06, .05]], "values must be numeric"),
        ([[.2, .3, math.inf, .05], [.21, .31, .05, .05],
          [.2, .32, .06, .05]], "must be normalized and fit inside the frame"),
        ([[.2, .3, math.nan, .05], [.21, .31, .05, .05],
          [.2, .32, .06, .05]], "must be normalized and fit inside the frame"),
        ([[.2, .3, .05, .05], [-.21, .31, .05, .05],
          [.2, .32, .06, .05]], "must be normalized and fit inside the frame"),
        ([[.2, .3, 0, .05], [.21, .31, .05, .05],
          [.2, .32, .06, .05]], "must be normalized and fit inside the frame"),
        ([[.2, .3, .05, 0], [.21, .31, .05, .05],
          [.2, .32, .06, .05]], "must be normalized and fit inside the frame"),
        ([[.2, 1.01, .05, .05], [.21, .31, .05, .05],
          [.2, .32, .06, .05]], "must be normalized and fit inside the frame"),
        ([[.2, .3, 1.05, .05], [.21, .31, .05, .05],
          [.2, .32, .06, .05]], "must be normalized and fit inside the frame"),
        ([[.98, .3, .05, .05], [.21, .31, .05, .05],
          [.2, .32, .06, .05]], "must be normalized and fit inside the frame"),
        ([[.2, .98, .05, .05], [.21, .31, .05, .05],
          [.2, .32, .06, .05]], "must be normalized and fit inside the frame"),
        ([[.98, .3, .0201, .05], [.21, .31, .05, .05],
          [.2, .32, .06, .05]], "must be normalized and fit inside the frame"),
        ([[.2, .98, .05, .0201], [.21, .31, .05, .05],
          [.2, .32, .06, .05]], "must be normalized and fit inside the frame"),
    ],
)
def test_vision_judge_preserves_malformed_locator_evidence(bboxes, message):
    identity_raw = '{"action_match": 0.9}'
    locator_raw = '{"speaker_mouth_bboxes": "malformed"}'

    with pytest.raises(VisionJudgeError, match=message) as caught:
        run_vision_judge(
            "cut.mp4", expected_speaker="S1", expected_action="speaks",
            judge=lambda **_: {
                "mouth_activity": 0.9, "action_match": 0.9,
                "speaker_attribution": 0.9,
                "speaker_mouth_bboxes": bboxes,
                "raw_response": identity_raw,
                "mouth_bbox_raw_response": locator_raw,
            })

    assert caught.value.scores == {
        "mouth_activity": 0.9, "action_match": 0.9,
        "speaker_attribution": 0.9,
    }
    assert caught.value.raw_response == identity_raw
    assert caught.value.mouth_bbox_raw_response == locator_raw


def test_still_mouth_activity_is_descriptive_not_blocking():
    evidence = run_vision_judge(
        "cut.mp4", expected_speaker="S1", expected_action="speaks",
        judge=lambda **_: {
            "mouth_activity": 0.1, "action_match": 0.95,
            "speaker_attribution": 0.98,
            "speaker_mouth_bboxes": _mouth_bboxes()})
    assert evidence.passed is True
    assert evidence.mouth_activity == 0.1
    assert evidence.av_sync_verified is False


def test_wd_v66o_diagnostic_replay_accepts_recorded_motion():
    artifact = pathlib.Path(__file__).parents[1] / (
        "datasets/diagnostics/WD-v66o/"
        "lf003-cut3-per-frame-localizer-diagnostic.json")
    payload = json.loads(artifact.read_text())
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == (
        "bb6f0c97ed24cbada1a19c7e352d2ccd1bbc07bbb2594765d802d6cce19e8664")
    localizer = payload["localizer"]
    evidence = run_vision_judge(
        payload["source"]["video_path"],
        expected_speaker=payload["source"]["expected_speaker"],
        expected_action=payload["source"]["expected_action"],
        judge=lambda **_: {
            **localizer["scores"],
            "speaker_mouth_bboxes": localizer["speaker_mouth_bboxes"],
            "raw_response": localizer["identity_raw_response"],
            "mouth_bbox_raw_response": localizer[
                "mouth_bbox_raw_response"],
        })
    assert evidence.passed is True
    assert evidence.speaker_mouth_center_spread == pytest.approx(
        (.0475, .0175))
    assert evidence.speaker_mouth_bbox == (.31, .19, .02, .015)


def test_qc_stage_persists_integrated_vision_evidence(tmp_path):
    evidence_path = tmp_path / "qc.json"
    syncnet_calls = []

    def syncnet_judge(**kwargs):
        syncnet_calls.append(kwargs)
        return _sync_evidence()

    qc = run_ref2va_qc_stage(
        _doc(tmp_path), judge=None, video_path="cut.mp4",
        expected_speaker="S1", expected_action="turns toward gate",
        vision_judge=lambda **_: {"mouth_activity": 0.9, "action_match": 0.9,
                                  "speaker_attribution": 0.9,
                                  "speaker_mouth_bboxes": _mouth_bboxes()},
        evidence_path=str(evidence_path),
        av_sync_judge=syncnet_judge)
    assert qc.vision_judge["passed"] is True
    assert qc.av_sync_gate["passed"] is True
    assert qc.vision_judge["speaker_mouth_center_spread"] == pytest.approx(
        [.0475, .0175])
    assert syncnet_calls == [{
        "video_path": "cut.mp4",
        "speaker_mouth_bbox": [.31, .19, .02, .015],
    }]
    payload = json.loads(evidence_path.read_text())
    assert payload["av_sync_gate"]["passed"] is True
    assert payload["vision_judge"]["speaker_mouth_center_spread"] == (
        pytest.approx([.0475, .0175]))


def test_qc_stage_blocks_on_syncnet_failure_after_moving_vision_passes(
        tmp_path):
    evidence_path = tmp_path / "qc.json"
    rejected = _sync_evidence(passed=False, confidence=.2)
    with pytest.raises(Ref2VAQCStageError, match="SyncNet gate failed") as caught:
        run_ref2va_qc_stage(
            _doc(tmp_path), judge=None, video_path="cut.mp4",
            expected_speaker="S1", expected_action="turns toward gate",
            vision_judge=lambda **_: {
                "mouth_activity": 0.9, "action_match": 0.9,
                "speaker_attribution": 0.9,
                "speaker_mouth_bboxes": _mouth_bboxes()},
            evidence_path=str(evidence_path),
            av_sync_judge=lambda **_: rejected)
    assert caught.value.av_sync_evidence["confidence"] == .2
    payload = json.loads(evidence_path.read_text())
    assert payload["vision_judge"]["passed"] is True
    assert payload["av_sync_gate"]["passed"] is False


def test_qc_stage_rejects_requested_vision_without_judge(tmp_path):
    """Supplying video expectations makes vision mandatory, not optional."""
    with pytest.raises(Ref2VAQCStageError,
                       match="vision judge is not wired; refusing ungated video"):
        run_ref2va_qc_stage(
            _doc(tmp_path), judge=None, video_path="cut.mp4",
            expected_speaker="S1", expected_action="turns", vision_judge=None)


def test_qc_stage_preserves_vision_rejection_evidence(tmp_path):
    raw_response = '{"mouth_activity": 0.1, "action_match": 0.8, "speaker_attribution": 0.2}'

    def reject(**_):
        return {"mouth_activity": 0.1, "action_match": 0.8,
                "speaker_attribution": 0.2,
                "speaker_mouth_bboxes": _mouth_bboxes(),
                "raw_response": raw_response}

    with pytest.raises(Ref2VAQCStageError) as caught:
        run_ref2va_qc_stage(
            _doc(tmp_path), judge=None, video_path="cut.mp4",
            expected_speaker="S1", expected_action="turns",
            vision_judge=reject)
    assert caught.value.vision_scores == {
        "mouth_activity": 0.1, "action_match": 0.8,
        "speaker_attribution": 0.2,
    }
    assert caught.value.vision_raw_response == raw_response


def test_qc_stage_preserves_malformed_locator_evidence_after_whisper(tmp_path):
    evidence_path = tmp_path / "qc.json"
    identity_raw = '{"action_match": 0.9}'
    locator_raw = '{"speaker_mouth_bboxes": [["bad"]]}'

    def malformed_locator(**_):
        return {"mouth_activity": 0.9, "action_match": 0.9,
                "speaker_attribution": 0.9,
                "speaker_mouth_bboxes": [["bad"]],
                "raw_response": identity_raw,
                "mouth_bbox_raw_response": locator_raw}

    with pytest.raises(Ref2VAQCStageError,
                       match="must include three speaker_mouth_bboxes") as caught:
        run_ref2va_qc_stage(
            _doc(tmp_path), judge=None, pre_audio_path="pre.wav",
            post_audio_path="post.wav", intended_text="the gate is open",
            whisper_transcriber=lambda _: "the gate is open",
            video_path="cut.mp4", expected_speaker="S1",
            expected_action="turns", vision_judge=malformed_locator,
            evidence_path=str(evidence_path))

    assert caught.value.vision_scores == {
        "mouth_activity": 0.9, "action_match": 0.9,
        "speaker_attribution": 0.9,
    }
    assert caught.value.vision_raw_response == identity_raw
    assert caught.value.vision_mouth_bbox_raw_response == locator_raw
    payload = json.loads(evidence_path.read_text())
    assert payload["whisper_gates"]["pre"]["passed"] is True
    assert payload["whisper_gates"]["post"]["passed"] is True
    assert payload["vision_judge"] is None
    assert payload["vision_rejection"] == {
        "failure_detail": (
            "vision result must include three speaker_mouth_bboxes [x,y,w,h]"),
        "scores": {"mouth_activity": 0.9, "action_match": 0.9,
                   "speaker_attribution": 0.9},
        "pass_bar": 0.7,
        "raw_response": identity_raw,
        "mouth_bbox_raw_response": locator_raw,
    }
