import json
import hashlib

import pytest

from qc.audio_critic.local_qwen_vision_judge import (
    LocalQwenVisionJudge,
    LocalQwenVisionJudgeError,
)
from qc.audio_critic.modelscope_vision_judge import ModelScopeVisionJudge
from qc.audio_critic.vision_judge import run_vision_judge


class _Host:
    def __init__(self, response=None, locator_responses=None, rc=0,
                 curl_rcs=None):
        self.identity_response = response or _model_response({
            "mouth_sync": 0.9, "action_match": 0.8,
            "speaker_attribution": 1.0})
        self.locator_responses = locator_responses or [
            _model_response({"speaker_mouth_bbox": box})
            for box in ([.2, .3, .05, .05], [.21, .31, .05, .05],
                        [.2, .32, .06, .05])
        ]
        self.rc = rc
        self.curl_rcs = curl_rcs
        self.curl_count = 0
        self.calls = []
        self.payloads = []

    def write_text(self, path, text):
        self.payloads.append(json.loads(text))
        self.calls.append(("write_text", path))
        return path

    def run_probe(self, argv, timeout=30):
        self.calls.append((list(argv), timeout))
        if argv[:1] == ["curl"]:
            request_index = self.curl_count
            self.curl_count += 1
            response = (self.identity_response if request_index == 0 else
                        self.locator_responses[request_index - 1])
            result_rc = (self.curl_rcs[request_index]
                         if self.curl_rcs is not None else self.rc)
            return result_rc, json.dumps(response), "local boom"
        return 0, "", ""


def _model_response(content):
    text = content if isinstance(content, str) else json.dumps(content)
    return {"choices": [{"message": {"content": text}}]}


def _local_judge(monkeypatch, host, **kwargs):
    monkeypatch.setattr(
        ModelScopeVisionJudge, "_extract_frames",
        staticmethod(lambda _path: [b"start", b"middle", b"end"]))
    return LocalQwenVisionJudge(host=host, **kwargs)


def _invoke(judge):
    return judge(video_path="cut.mp4", expected_speaker="Grandma", expected_action="Grandma speaks")


def test_local_judge_posts_three_frames_through_host_seam(monkeypatch):
    host = _Host()
    judge = _local_judge(monkeypatch, host, model="qwen38-local")
    result = _invoke(judge)

    assert result["mouth_activity"] == 0.9
    assert '"mouth_sync": 0.9' in result["raw_response"]
    assert result["critic"] == "local:qwen38-local"
    content = host.payloads[0]["messages"][0]["content"]
    assert len([part for part in content if part["type"] == "image_url"]) == 3
    assert host.payloads[0]["max_tokens"] >= 512
    assert host.payloads[0]["response_format"] == {"type": "json_object"}
    assert host.payloads[0]["chat_template_kwargs"] == {
        "enable_thinking": False}
    curl_calls = [call[0] for call in host.calls
                  if isinstance(call, tuple) and isinstance(call[0], list)
                  and call[0][0] == "curl"]
    assert curl_calls
    assert "-HContent-Type:application/json" in curl_calls[0]
    assert "Content-Type: application/json" not in curl_calls[0]
    assert any(call[0][0] == "rm" for call in host.calls
               if isinstance(call, tuple) and isinstance(call[0], list))
    assert len(host.payloads) == 4
    for frame_name, payload in zip(("start", "middle", "end"),
                                   host.payloads[1:]):
        content = payload["messages"][0]["content"]
        assert sum(part["type"] == "image_url" for part in content) == 1
        assert frame_name in content[0]["text"]
        assert '"speaker_mouth_bbox": [x,y,width,height]' in content[0]["text"]
    evidence = json.loads(result["mouth_bbox_raw_response"])
    assert [f["bbox"] for f in evidence["frames"]] == result["speaker_mouth_bboxes"]
    assert all(frame["status"] == "success" and len(frame["attempts"]) == 1
               for frame in evidence["frames"])
    run_vision_judge("cut.mp4", expected_speaker="Grandma",
                     expected_action="Grandma speaks",
                     judge=lambda **_: result, pass_bar=0.7)


def test_local_judge_retries_one_malformed_frame_once_and_preserves_attempts(
        monkeypatch):
    malformed = _model_response({"speaker_mouth_bboxes": [[.2, .3, .05, .05]]})
    good = _model_response({"speaker_mouth_bbox": [.2, .3, .05, .05]})
    host = _Host(locator_responses=[malformed, good, good, good])
    result = _invoke(_local_judge(monkeypatch, host))

    evidence = json.loads(result["mouth_bbox_raw_response"])
    attempts = evidence["frames"][0]["attempts"]
    assert [attempt["status"] for attempt in attempts] == ["malformed", "success"]
    assert [len(frame["attempts"]) for frame in evidence["frames"]] == [2, 1, 1]
    for attempt in evidence["frames"][0]["attempts"]:
        assert attempt["raw_response_sha256"] == hashlib.sha256(
            attempt["raw_response"].encode()).hexdigest()
    assert json.dumps(evidence, sort_keys=True, separators=(
        ",", ":")) == result["mouth_bbox_raw_response"]


def test_local_judge_fails_closed_after_malformed_retry_exhaustion(
        monkeypatch):
    malformed = _model_response("not json")
    host = _Host(locator_responses=[malformed, malformed])

    with pytest.raises(LocalQwenVisionJudgeError,
                       match="frame 1 mouth localization failed") as caught:
        _invoke(_local_judge(monkeypatch, host))

    evidence = json.loads(caught.value.mouth_bbox_raw_response)
    assert evidence["frames"][0]["status"] == "retry_exhausted"
    attempts = evidence["frames"][0]["attempts"]
    assert [attempt["status"] for attempt in attempts] == ["malformed"] * 2
    assert len(host.payloads) == 3


@pytest.mark.parametrize("bbox", [
    [.2, .3], [.2, .3, "bad", .05], [.2, .3, .05],
    [-.01, .3, .05, .05], [.2, .3, 1.05, .05], [.98, .3, .05, .05],
])
def test_local_judge_rejects_invalid_mouth_bbox_after_one_retry(
        monkeypatch, bbox):
    response = _model_response({"speaker_mouth_bbox": bbox})
    host = _Host(locator_responses=[response, response])

    with pytest.raises(LocalQwenVisionJudgeError,
                       match="frame 1 mouth localization failed") as caught:
        _invoke(_local_judge(monkeypatch, host))

    evidence = json.loads(caught.value.mouth_bbox_raw_response)
    assert "speaker_mouth_bbox" in evidence["frames"][0]["attempts"][0]["error"]


def test_local_judge_rejects_remote_transport_failure(monkeypatch):
    host = _Host(rc=28)

    with pytest.raises(LocalQwenVisionJudgeError, match="request failed"):
        _invoke(_local_judge(monkeypatch, host))


def test_local_judge_locator_transport_failure_fails_closed_with_evidence(
        monkeypatch):
    host = _Host(curl_rcs=[0, 28])

    with pytest.raises(LocalQwenVisionJudgeError,
                       match="frame 1 mouth localization failed") as caught:
        _invoke(_local_judge(monkeypatch, host))

    evidence = json.loads(caught.value.mouth_bbox_raw_response)
    assert (evidence["frames"][0]["status"] == "transport_failure"
            and len(host.payloads) == 2)


def test_local_judge_falls_back_to_reasoning_content(monkeypatch):
    host = _Host(response={
        "choices": [{"finish_reason": "length", "message": {
            "content": "",
            "reasoning_content": (
                "Visual evidence is clear. Final answer: "
                "{\"mouth_sync\": 0.6, \"action_match\": 0.7, "
                "\"speaker_attribution\": 0.8}")
        }}],
    })
    result = _invoke(_local_judge(monkeypatch, host))

    assert result["mouth_activity"] == 0.6
    assert result["action_match"] == 0.7
    assert result["speaker_attribution"] == 0.8
    assert "Final answer" in result["raw_response"]
