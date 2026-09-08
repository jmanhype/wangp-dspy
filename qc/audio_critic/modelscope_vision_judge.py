"""ModelScope Qwen-VL adapter for the blocking Ref2VA vision gate.

The public callable matches :func:`qc.audio_critic.vision_judge.run_vision_judge`:
it receives a local rendered cut plus speaker/action expectations and returns
three normalized 0..1 scores.  The adapter samples start/middle/end PNGs and
sends them as image parts to ModelScope's OpenAI-compatible chat endpoint.

No credentials are guessed.  ``MODELSCOPE_API_KEY`` (or the documented
``MODELSCOPE_TOKEN``/``MODELSCOPE_API_TOKEN`` aliases) is required; model/base URL/timeout are
environment-overridable so the operator can select the ambassador Qwen-VL
deployment without a code change.
"""
from __future__ import annotations

import base64
import json
import os
import signal
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any, Mapping, Optional

import requests


DEFAULT_MODELSCOPE_BASE_URL = "https://api-inference.modelscope.cn/v1"
# The operator's ambassador deployment exposes Qwen3.8-Max; keep this
# overrideable because ModelScope may map the same service to a model ID.
DEFAULT_MODELSCOPE_VISION_MODEL = "qwen3.8-max"
_SCORE_KEYS = ("mouth_sync", "action_match", "speaker_attribution")


class ModelScopeVisionJudgeError(ValueError):
    """Typed configuration, media extraction, or API response failure."""


class _ModelScopeDeadlineExceeded(TimeoutError):
    """Internal wall-clock deadline for a request, including upload."""


def _env_key() -> str:
    return (os.environ.get("MODELSCOPE_API_KEY") or
            os.environ.get("MODELSCOPE_TOKEN") or
            os.environ.get("MODELSCOPE_API_TOKEN") or "").strip()


def _json_object(text: str) -> dict:
    """Extract the final JSON object from a model response.

    Reasoning-model responses can contain prose (and even earlier example
    objects) before the answer.  ``JSONDecoder.raw_decode`` lets us inspect
    every object-looking position without relying on a greedy regular
    expression that can join two unrelated objects together.
    """
    raw = str(text or "").strip()
    if not raw:
        raise ModelScopeVisionJudgeError(
            "ModelScope vision response did not contain a JSON object")

    decoder = json.JSONDecoder()
    candidates: list[dict] = []
    for index, char in enumerate(raw):
        if char != "{":
            continue
        try:
            value, _end = decoder.raw_decode(raw[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            candidates.append(value)
    if candidates:
        # The final object is the model's answer when the reasoning trace
        # contains examples or intermediate JSON snippets.
        scored = [candidate for candidate in candidates
                  if any(key in candidate for key in _SCORE_KEYS)]
        return (scored[-1] if scored else candidates[-1])

    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ModelScopeVisionJudgeError(
            f"ModelScope vision response JSON is invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise ModelScopeVisionJudgeError(
            "ModelScope vision response must be a JSON object")
    return value


def _part_text(value: Any) -> str:
    """Normalize OpenAI text content, including multimodal part arrays."""
    if isinstance(value, list):
        return "".join(
            part.get("text", "") if isinstance(part, Mapping) else str(part)
            for part in value
        ).strip()
    return str(value or "").strip()


def _response_object(message: Mapping[str, Any], *, label: str) -> dict:
    """Parse a score object from final content or reasoning fallback.

    Qwen reasoning models may spend the whole generation budget in
    ``reasoning_content`` and leave OpenAI-compatible ``content`` empty.
    Content remains authoritative when present; the reasoning field is only
    consulted when content is empty or contains no parseable JSON.
    """
    content = _part_text(message.get("content"))
    reasoning = _part_text(message.get("reasoning_content"))
    candidates = [text for text in (content, reasoning) if text]
    if not candidates:
        raise ModelScopeVisionJudgeError(
            f"{label} vision response missing content and reasoning_content")
    last_error: Optional[Exception] = None
    for text in candidates:
        try:
            return _json_object(text)
        except ModelScopeVisionJudgeError as exc:
            last_error = exc
    raise ModelScopeVisionJudgeError(
        f"{label} vision response did not contain a JSON object") from last_error


class ModelScopeVisionJudge:
    """Callable production judge backed by ModelScope Qwen-VL."""

    def __init__(self, *, api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 model: Optional[str] = None,
                 timeout_s: float = 180.0,
                 max_tokens: Optional[int] = None,
                 session=None):
        self.api_key = (api_key or _env_key()).strip()
        if not self.api_key:
            raise ModelScopeVisionJudgeError(
                "MODELSCOPE_API_KEY (or MODELSCOPE_TOKEN/MODELSCOPE_API_TOKEN) is required; "
                "refusing to run an ungated vision judge")
        self.base_url = (base_url or
                         os.environ.get("MODELSCOPE_VISION_BASE_URL") or
                         os.environ.get("MODELSCOPE_BASE_URL") or
                         DEFAULT_MODELSCOPE_BASE_URL).rstrip("/")
        self.model = (model or
                      os.environ.get("MODELSCOPE_VISION_MODEL") or
                      os.environ.get("MODELSCOPE_MODEL") or
                      DEFAULT_MODELSCOPE_VISION_MODEL)
        try:
            self.timeout_s = float(timeout_s)
        except (TypeError, ValueError) as exc:
            raise ModelScopeVisionJudgeError("timeout_s must be numeric") from exc
        if self.timeout_s <= 0:
            raise ModelScopeVisionJudgeError("timeout_s must be positive")
        raw_max_tokens = (max_tokens if max_tokens is not None else
                          os.environ.get("MODELSCOPE_VISION_MAX_TOKENS", "512"))
        try:
            self.max_tokens = int(raw_max_tokens)
        except (TypeError, ValueError) as exc:
            raise ModelScopeVisionJudgeError(
                "max_tokens must be an integer") from exc
        if self.max_tokens <= 0:
            raise ModelScopeVisionJudgeError("max_tokens must be positive")
        self.session = session or requests

    def __call__(self, *, video_path: str, expected_speaker: str,
                 expected_action: str) -> dict:
        return self.judge(video_path=video_path,
                          expected_speaker=expected_speaker,
                          expected_action=expected_action)

    def judge(self, *, video_path: str, expected_speaker: str,
              expected_action: str) -> dict:
        frames = self._extract_frames(video_path)
        prompt = self._prompt(expected_speaker, expected_action)
        content = [{"type": "text", "text": prompt}]
        for frame in frames:
            content.append({"type": "image_url", "image_url": {
                "url": self._data_url(frame)}})
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0,
            "max_tokens": self.max_tokens,
        }
        try:
            response = self._post_with_deadline(payload)
            response.raise_for_status()
            body = response.json()
        except _ModelScopeDeadlineExceeded as exc:
            raise ModelScopeVisionJudgeError(
                f"ModelScope vision request timed out after "
                f"{self.timeout_s:.3g}s (including upload)") from exc
        except (requests.exceptions.Timeout, TimeoutError) as exc:
            raise ModelScopeVisionJudgeError(
                f"ModelScope vision request timed out after "
                f"{self.timeout_s:.3g}s (including upload/read)") from exc
        except Exception as exc:  # requests + malformed fake responses
            raise ModelScopeVisionJudgeError(
                f"ModelScope vision request failed: {type(exc).__name__}: {exc}") from exc
        try:
            message = body["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelScopeVisionJudgeError(
                "ModelScope vision response missing choices[0].message") from exc
        if not isinstance(message, Mapping):
            raise ModelScopeVisionJudgeError(
                "ModelScope vision response choices[0].message must be an object")
        result = _response_object(message, label="ModelScope")
        for key in _SCORE_KEYS:
            try:
                value = float(result[key])
            except (KeyError, TypeError, ValueError) as exc:
                raise ModelScopeVisionJudgeError(
                    f"ModelScope vision response missing numeric {key}") from exc
            if not 0.0 <= value <= 1.0:
                raise ModelScopeVisionJudgeError(
                    f"ModelScope vision score {key} must be 0..1, got {value!r}")
            result[key] = value
        return {**result, "critic": f"modelscope:{self.model}"}

    def _post_with_deadline(self, payload: dict):
        """POST with a real wall-clock bound around connect, upload, and read.

        ``requests``' socket timeout does not reliably interrupt a blocked TLS
        ``sendall`` while a large multimodal body is being uploaded.  The
        production runner is synchronous, so a main-thread ``ITIMER_REAL``
        guard provides the hard deadline without leaving a worker thread
        behind.  Non-main-thread callers still receive the requests connect /
        read timeout (and can provide their own process-level deadline).
        """
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}",
                   "Content-Type": "application/json"}
        timeout = max(0.1, float(self.timeout_s))

        def post():
            # A tuple bounds connection and response waits; the surrounding
            # signal bounds body upload too.
            return self.session.post(
                url, headers=headers, json=payload,
                timeout=(min(timeout, 30.0), timeout))

        if (threading.current_thread() is not threading.main_thread()
                or not hasattr(signal, "setitimer")
                or not hasattr(signal, "SIGALRM")):
            return post()

        previous = signal.getsignal(signal.SIGALRM)

        def alarm_handler(_signum, _frame):
            raise _ModelScopeDeadlineExceeded

        signal.signal(signal.SIGALRM, alarm_handler)
        signal.setitimer(signal.ITIMER_REAL, timeout)
        try:
            return post()
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)

    @staticmethod
    def _prompt(expected_speaker: str, expected_action: str) -> str:
        return (
            "Visual QC for three frames (start, middle, end). Expected "
            f"speaking identity and silent counterpart: {expected_speaker}. "
            f"Expected action: {expected_action}. Score whether the expected "
            "identity is the mouth-moving character, the counterpart stays "
            "silent, and the action is visible. Do not explain or expose "
            "reasoning. Respond with exactly one JSON object and nothing else: "
            '{"mouth_sync": 0.0, "action_match": 0.0, '
            '"speaker_attribution": 0.0}. Use 1.0 only for clear evidence.'
        )

    @staticmethod
    def _data_url(data: bytes) -> str:
        encoded = base64.b64encode(data).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    @staticmethod
    def _extract_frames(video_path: str) -> list[bytes]:
        path = Path(video_path)
        if not path.is_file():
            raise ModelScopeVisionJudgeError(
                f"vision video artifact is missing: {video_path}")
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                capture_output=True, text=True, check=False, timeout=60)
            if probe.returncode != 0:
                raise RuntimeError(probe.stderr.strip()[:200])
            duration = float(probe.stdout.strip())
        except Exception as exc:
            raise ModelScopeVisionJudgeError(
                f"unable to probe vision video duration: {exc}") from exc
        if duration <= 0:
            raise ModelScopeVisionJudgeError("vision video duration must be positive")
        times = (0.0, duration / 2.0, max(0.0, duration - 1.0 / 24.0))
        frames: list[bytes] = []
        with tempfile.TemporaryDirectory(prefix="wangp-vision-") as tmp:
            root = Path(tmp)
            for index, timestamp in enumerate(times):
                output = root / f"frame-{index}.png"
                proc = subprocess.run(
                    ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                     "-ss", f"{timestamp:.6f}", "-i", str(path),
                     "-frames:v", "1", str(output)],
                    capture_output=True, text=True, check=False, timeout=120)
                if proc.returncode != 0 or not output.is_file():
                    raise ModelScopeVisionJudgeError(
                        f"frame extraction failed at {timestamp:.3f}s: "
                        f"{proc.stderr.strip()[:200]}")
                # Copy bytes out of TemporaryDirectory before it is cleaned.
                frames.append(output.read_bytes())
        return frames


def build_modelscope_vision_judge(**kwargs) -> ModelScopeVisionJudge:
    """Construct the default production judge, failing closed without a key."""
    return ModelScopeVisionJudge(**kwargs)


__all__ = ["ModelScopeVisionJudge", "ModelScopeVisionJudgeError",
           "build_modelscope_vision_judge", "DEFAULT_MODELSCOPE_BASE_URL",
           "DEFAULT_MODELSCOPE_VISION_MODEL"]
