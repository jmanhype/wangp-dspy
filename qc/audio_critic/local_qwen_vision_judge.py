"""Local 3090 Qwen-VL adapter for the blocking Ref2VA vision gate.

The adapter talks to the llama-server running on the render host through the
repo's :class:`host.render_host.SshHost` seam.  No API credential or direct
SSH/curl wrapper is needed: the request JSON is staged with ``write_text`` and
posted with ``run_probe`` on the host.  Three local PNG frames are sent as
base64 image parts and the response must carry the same strict 0..1 score
contract as the ModelScope adapter.
"""
from __future__ import annotations

import json
import os
import uuid
from typing import Optional

from qc.audio_critic.modelscope_vision_judge import (
    ModelScopeVisionJudge,
    _SCORE_KEYS,
    _response_object,
)


DEFAULT_LOCAL_VISION_ENDPOINT = (
    "http://localhost:8000/v1/chat/completions")
DEFAULT_LOCAL_VISION_MODEL = "q"


class LocalQwenVisionJudgeError(ValueError):
    """Typed local-host configuration, transport, or response failure."""


class LocalQwenVisionJudge:
    """Callable judge backed by the 3090's local llama-server Qwen-VL."""

    def __init__(self, *, host, endpoint: Optional[str] = None,
                 model: Optional[str] = None, timeout_s: float = 180.0,
                 max_tokens: Optional[int] = None):
        if host is None or not callable(getattr(host, "run_probe", None)):
            raise LocalQwenVisionJudgeError(
                "a RenderHost with run_probe is required for local vision")
        self.host = host
        self.endpoint = (endpoint or
                         os.environ.get("WANGP_LOCAL_VISION_ENDPOINT") or
                         DEFAULT_LOCAL_VISION_ENDPOINT).strip()
        self.model = (model or
                      os.environ.get("WANGP_LOCAL_VISION_MODEL") or
                      DEFAULT_LOCAL_VISION_MODEL).strip()
        try:
            self.timeout_s = float(
                os.environ.get("WANGP_LOCAL_VISION_TIMEOUT", timeout_s))
        except (TypeError, ValueError) as exc:
            raise LocalQwenVisionJudgeError(
                "WANGP_LOCAL_VISION_TIMEOUT must be numeric") from exc
        if not self.endpoint:
            raise LocalQwenVisionJudgeError("local vision endpoint is required")
        if not self.model:
            raise LocalQwenVisionJudgeError("local vision model is required")
        if self.timeout_s <= 0:
            raise LocalQwenVisionJudgeError("local vision timeout must be positive")
        raw_max_tokens = (max_tokens if max_tokens is not None else
                          os.environ.get("WANGP_LOCAL_VISION_MAX_TOKENS", "1024"))
        try:
            self.max_tokens = int(raw_max_tokens)
        except (TypeError, ValueError) as exc:
            raise LocalQwenVisionJudgeError(
                "WANGP_LOCAL_VISION_MAX_TOKENS must be an integer") from exc
        if self.max_tokens <= 0:
            raise LocalQwenVisionJudgeError(
                "local vision max_tokens must be positive")

    def __call__(self, *, video_path: str, expected_speaker: str,
                 expected_action: str) -> dict:
        return self.judge(video_path=video_path,
                          expected_speaker=expected_speaker,
                          expected_action=expected_action)

    def judge(self, *, video_path: str, expected_speaker: str,
              expected_action: str) -> dict:
        # Reuse the exact three-frame extraction and identity-aware prompt
        # contract; only the transport/backend differs from ModelScope.
        frames = ModelScopeVisionJudge._extract_frames(video_path)
        content = [{"type": "text",
                    "text": ModelScopeVisionJudge._prompt(
                        expected_speaker, expected_action)}]
        for frame in frames:
            content.append({"type": "image_url", "image_url": {
                "url": ModelScopeVisionJudge._data_url(frame)}})
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0,
            "max_tokens": self.max_tokens,
            # llama-server supports the OpenAI JSON-object grammar.  This
            # prevents a visually uncertain cut from spending its entire
            # budget on prose before emitting the required score object.
            "response_format": {"type": "json_object"},
            # llama-server's Qwen chat template supports disabling the
            # reasoning trace so the score JSON is emitted in content.
            "chat_template_kwargs": {"enable_thinking": False},
        }
        remote_payload = f"/tmp/wangp-local-vision-{uuid.uuid4().hex}.json"
        writer = getattr(self.host, "write_text", None)
        if not callable(writer):
            raise LocalQwenVisionJudgeError(
                "RenderHost must expose write_text for local vision payloads")
        try:
            remote_payload = writer(
                remote_payload,
                json.dumps(payload, separators=(",", ":")))
            rc, out, err = self.host.run_probe(
                ["curl", "-fsS", "--max-time", str(int(self.timeout_s)),
                 # SshHost transmits argv through the remote command line;
                 # keep the header as one token so the space in its value is
                 # not re-tokenized by the remote shell.
                 "-HContent-Type:application/json",
                 "--data-binary", f"@{remote_payload}", self.endpoint],
                timeout=self.timeout_s + 30.0)
            if rc != 0:
                raise LocalQwenVisionJudgeError(
                    f"local Qwen-VL request failed (rc={rc}): "
                    f"{(err or out or '').strip()[-400:]}")
            try:
                body = json.loads(out)
                message = body["choices"][0]["message"]
            except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
                raise LocalQwenVisionJudgeError(
                    "local Qwen-VL response missing "
                    "choices[0].message") from exc
            if not isinstance(message, dict):
                raise LocalQwenVisionJudgeError(
                    "local Qwen-VL response choices[0].message must be an object")
            try:
                result = _response_object(message, label="local Qwen-VL")
            except ValueError as exc:
                raise LocalQwenVisionJudgeError(str(exc)) from exc
            for key in _SCORE_KEYS:
                try:
                    value = float(result[key])
                except (KeyError, TypeError, ValueError) as exc:
                    raise LocalQwenVisionJudgeError(
                        f"local Qwen-VL response missing numeric {key}") from exc
                if not 0.0 <= value <= 1.0:
                    raise LocalQwenVisionJudgeError(
                        f"local Qwen-VL score {key} must be 0..1, got {value!r}")
                result[key] = value
            return {**result, "critic": f"local:{self.model}"}
        finally:
            # Cleanup is best effort; a failed cleanup never turns a real
            # visual result into a KEEP and never masks the original failure.
            try:
                self.host.run_probe(["rm", remote_payload], timeout=30)
            except Exception:
                pass


def build_local_qwen_vision_judge(**kwargs) -> LocalQwenVisionJudge:
    """Construct the local judge; missing host/config fails closed."""
    return LocalQwenVisionJudge(**kwargs)


__all__ = ["LocalQwenVisionJudge", "LocalQwenVisionJudgeError",
           "build_local_qwen_vision_judge", "DEFAULT_LOCAL_VISION_ENDPOINT",
           "DEFAULT_LOCAL_VISION_MODEL"]
