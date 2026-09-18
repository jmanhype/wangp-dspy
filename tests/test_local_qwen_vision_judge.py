import json

import pytest

from qc.audio_critic.local_qwen_vision_judge import (
    LocalQwenVisionJudge,
    LocalQwenVisionJudgeError,
)
from qc.audio_critic.modelscope_vision_judge import ModelScopeVisionJudge


class _Host:
    def __init__(self, response=None, rc=0):
        self.response = response or {
            "choices": [{"message": {"content": json.dumps({
                "mouth_sync": 0.9, "action_match": 0.8,
                "speaker_attribution": 1.0,
                "speaker_mouth_bbox": [.2, .3, .05, .05],
            })}}]
        }
        self.rc = rc
        self.calls = []
        self.payload = None

    def write_text(self, path, text):
        self.payload = json.loads(text)
        self.calls.append(("write_text", path))
        return path

    def run_probe(self, argv, timeout=30):
        self.calls.append((list(argv), timeout))
        if argv[:1] == ["curl"]:
            return self.rc, json.dumps(self.response), "local boom"
        return 0, "", ""


def test_local_judge_posts_three_frames_through_host_seam(monkeypatch):
    monkeypatch.setattr(
        ModelScopeVisionJudge, "_extract_frames",
        staticmethod(lambda _path: [b"start", b"middle", b"end"]))
    host = _Host()
    judge = LocalQwenVisionJudge(host=host, model="qwen38-local")

    result = judge(video_path="cut.mp4", expected_speaker="Grandma",
                   expected_action="Grandma speaks")

    assert result["mouth_activity"] == 0.9
    assert '"mouth_sync": 0.9' in result["raw_response"]
    assert result["critic"] == "local:qwen38-local"
    content = host.payload["messages"][0]["content"]
    assert len([part for part in content if part["type"] == "image_url"]) == 3
    assert host.payload["max_tokens"] >= 512
    assert host.payload["response_format"] == {"type": "json_object"}
    assert host.payload["chat_template_kwargs"] == {"enable_thinking": False}
    curl_calls = [call[0] for call in host.calls
                  if isinstance(call, tuple) and isinstance(call[0], list)
                  and call[0][0] == "curl"]
    assert curl_calls
    assert "-HContent-Type:application/json" in curl_calls[0]
    assert "Content-Type: application/json" not in curl_calls[0]
    assert any(call[0][0] == "rm" for call in host.calls
               if isinstance(call, tuple) and isinstance(call[0], list))


def test_local_judge_rejects_remote_transport_failure(monkeypatch):
    monkeypatch.setattr(
        ModelScopeVisionJudge, "_extract_frames",
        staticmethod(lambda _path: [b"start", b"middle", b"end"]))
    host = _Host(rc=28)
    judge = LocalQwenVisionJudge(host=host)

    with pytest.raises(LocalQwenVisionJudgeError, match="request failed"):
        judge(video_path="cut.mp4", expected_speaker="Grandma",
              expected_action="Grandma speaks")


def test_local_judge_falls_back_to_reasoning_content(monkeypatch):
    monkeypatch.setattr(
        ModelScopeVisionJudge, "_extract_frames",
        staticmethod(lambda _path: [b"start", b"middle", b"end"]))
    host = _Host(response={
        "choices": [{"finish_reason": "length", "message": {
            "content": "",
            "reasoning_content": (
                "Visual evidence is clear. Final answer: "
                "{\"mouth_sync\": 0.6, \"action_match\": 0.7, "
                "\"speaker_attribution\": 0.8, "
                "\"speaker_mouth_bbox\": [0.2, 0.3, 0.05, 0.05]}")
        }}],
    })
    judge = LocalQwenVisionJudge(host=host)

    result = judge(video_path="cut.mp4", expected_speaker="Grandma",
                   expected_action="Grandma speaks")

    assert result["mouth_activity"] == 0.6
    assert result["action_match"] == 0.7
    assert result["speaker_attribution"] == 0.8
    assert "Final answer" in result["raw_response"]
