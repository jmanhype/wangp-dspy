import json
import subprocess

import pytest

from qc.audio_critic.modelscope_vision_judge import (
    ModelScopeVisionJudge, ModelScopeVisionJudgeError,
)


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class _Session:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return _Response(self.payload)


def _fake_ffmpeg(monkeypatch):
    def run(argv, **kwargs):
        if argv[0] == "ffprobe":
            return subprocess.CompletedProcess(argv, 0, "2.333333\n", "")
        output = argv[-1]
        with open(output, "wb") as fh:
            fh.write(b"png")
        return subprocess.CompletedProcess(argv, 0, "", "")
    monkeypatch.setattr(subprocess, "run", run)


def test_modelscope_judge_extracts_three_frames_and_parses_scores(
        tmp_path, monkeypatch):
    _fake_ffmpeg(monkeypatch)
    video = tmp_path / "cut.mp4"
    video.write_bytes(b"video")
    session = _Session({
        "choices": [{"message": {"content": json.dumps({
            "mouth_sync": 0.9, "action_match": 0.8,
            "speaker_attribution": 1.0, "notes": "identity holds",
        })}}],
    })
    judge = ModelScopeVisionJudge(
        api_key="test-key", model="Qwen/test", session=session)

    result = judge(
        video_path=str(video),
        expected_speaker=("S1 (Grandma): elderly grandmother with round "
                          "glasses; silent other S2 (Soul): flaming skeleton"),
        expected_action="Grandma speaks while Soul remains still",
    )

    assert result["mouth_sync"] == 0.9
    assert result["speaker_attribution"] == 1.0
    assert result["critic"] == "modelscope:Qwen/test"
    assert len(session.calls) == 1
    payload = session.calls[0][1]["json"]
    assert payload["model"] == "Qwen/test"
    content = payload["messages"][0]["content"]
    assert len([part for part in content if part["type"] == "image_url"]) == 3
    assert "elderly grandmother with round glasses" in content[0]["text"]
    assert "flaming skeleton" in content[0]["text"]


def test_modelscope_judge_requires_api_key(monkeypatch):
    monkeypatch.delenv("MODELSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("MODELSCOPE_TOKEN", raising=False)
    with pytest.raises(ModelScopeVisionJudgeError, match="MODELSCOPE_API_KEY"):
        ModelScopeVisionJudge()


def test_modelscope_judge_rejects_out_of_range_score(
        tmp_path, monkeypatch):
    _fake_ffmpeg(monkeypatch)
    video = tmp_path / "cut.mp4"
    video.write_bytes(b"video")
    session = _Session({
        "choices": [{"message": {"content": (
            '{"mouth_sync": 2, "action_match": 0.8, '
            '"speaker_attribution": 0.8}') }}],
    })
    judge = ModelScopeVisionJudge(api_key="test-key", session=session)
    with pytest.raises(ModelScopeVisionJudgeError, match="must be 0..1"):
        judge(video_path=str(video), expected_speaker="Grandma",
              expected_action="speaks")
