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
import hashlib
import math
import os
import uuid
from pathlib import Path
from typing import Optional

from qc.audio_critic.modelscope_vision_judge import (
    ModelScopeVisionJudge,
    _SCORE_KEYS,
    _response_object,
    _response_text,
)


DEFAULT_LOCAL_VISION_ENDPOINT = (
    "http://localhost:8000/v1/chat/completions")
DEFAULT_LOCAL_VISION_MODEL = "q"


class LocalQwenVisionJudgeError(ValueError):
    """Typed local-host configuration, transport, or response failure."""

    def __init__(self, message: str, *, scores=None,
                 raw_response: Optional[str] = None,
                 mouth_bbox_raw_response: Optional[str] = None,
                 transport_failure: bool = False):
        super().__init__(message)
        self.scores = dict(scores or {})
        self.raw_response = (str(raw_response)
                             if raw_response is not None else None)
        self.mouth_bbox_raw_response = (str(mouth_bbox_raw_response)
                                        if mouth_bbox_raw_response is not None else None)
        self.transport_failure = bool(transport_failure)


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
                 expected_action: str, reference_image_path: Optional[str] = None) -> dict:
        return self.judge(video_path=video_path,
                          expected_speaker=expected_speaker,
                          expected_action=expected_action, reference_image_path=reference_image_path)

    def judge(self, *, video_path: str, expected_speaker: str,
              expected_action: str, reference_image_path: Optional[str] = None) -> dict:
        # Reuse the exact three-frame extraction and identity-aware prompt
        # contract; only the transport/backend differs from ModelScope.
        generated_frames = ModelScopeVisionJudge._extract_frames(video_path)
        frames = list(generated_frames)
        if reference_image_path is not None:
            ref = Path(reference_image_path)
            if not ref.is_file():
                raise ValueError(f"vision reference image missing: {ref}")
            frames.insert(0, ref.read_bytes())
        content = [{"type": "text",
                    "text": ModelScopeVisionJudge._prompt(
                        expected_speaker, expected_action)}]
        for frame in frames:
            content.append({"type": "image_url", "image_url": {
                "url": ModelScopeVisionJudge._data_url(frame)}})
        def request(content):
            remote_payload = f"/tmp/wangp-local-vision-{uuid.uuid4().hex}.json"
            writer = getattr(self.host, "write_text", None)
            if not callable(writer):
                raise LocalQwenVisionJudgeError(
                    "RenderHost must expose write_text for local vision payloads",
                    transport_failure=True)
            remote_payload = writer(
                remote_payload,
                json.dumps({
                    "model": self.model,
                    "messages": [{"role": "user", "content": content}],
                    "temperature": 0,
                    "max_tokens": self.max_tokens,
                    "response_format": {"type": "json_object"},
                    "chat_template_kwargs": {"enable_thinking": False},
                }, separators=(",", ":")))
            rc, out, err = self.host.run_probe(
                ["curl", "-fsS", "--max-time", str(int(self.timeout_s)),
                 "-HContent-Type:application/json",
                 "--data-binary", f"@{remote_payload}", self.endpoint],
                timeout=self.timeout_s + 30.0)
            try:
                self.host.run_probe(["rm", remote_payload], timeout=30)
            except Exception:
                pass
            if rc != 0:
                raise LocalQwenVisionJudgeError(
                    f"local Qwen-VL request failed (rc={rc}): "
                    f"{(err or out or '').strip()[-400:]}",
                    transport_failure=True)
            try:
                body = json.loads(out)
                message = body["choices"][0]["message"]
            except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
                raise LocalQwenVisionJudgeError(
                    "local Qwen-VL response missing choices[0].message") from exc
            if not isinstance(message, dict):
                raise LocalQwenVisionJudgeError(
                    "local Qwen-VL response choices[0].message must be an object")
            raw_response = _response_text(message)
            try:
                return _response_object(message, label="local Qwen-VL"), raw_response
            except ValueError as exc:
                raise LocalQwenVisionJudgeError(
                    str(exc), raw_response=raw_response) from exc

        result, raw_response = request(content)
        if "mouth_activity" not in result and "mouth_sync" in result:
            result["mouth_activity"] = result.pop("mouth_sync")
        for key in _SCORE_KEYS:
            try:
                value = float(result[key])
            except (KeyError, TypeError, ValueError) as exc:
                raise LocalQwenVisionJudgeError(
                    f"local Qwen-VL response missing numeric {key}",
                    raw_response=raw_response) from exc
            if not 0.0 <= value <= 1.0:
                raise LocalQwenVisionJudgeError(
                    f"local Qwen-VL score {key} must be 0..1, got {value!r}",
                    raw_response=raw_response)
            result[key] = value

        def attempt_evidence(status, raw_response, *, error=None, bbox=None):
            evidence = {
                "status": status,
                "raw_response": (str(raw_response)
                                 if raw_response is not None else None),
                "raw_response_sha256": (hashlib.sha256(
                    str(raw_response).encode()).hexdigest()
                    if raw_response is not None else None),
            }
            if error is not None:
                evidence["error"] = str(error)
            if bbox is not None:
                evidence["bbox"] = list(bbox)
            return evidence

        def valid_bbox(response):
            if not isinstance(response, dict):
                raise ValueError("mouth response must be a JSON object")
            if "speaker_mouth_bbox" not in response:
                raise ValueError("mouth response missing speaker_mouth_bbox")
            raw_bbox = response["speaker_mouth_bbox"]
            if (not isinstance(raw_bbox, (list, tuple))
                    or len(raw_bbox) != 4):
                raise ValueError("speaker_mouth_bbox must be [x,y,width,height]")
            if any(isinstance(value, bool) or
                   not isinstance(value, (int, float))
                   for value in raw_bbox):
                raise ValueError("speaker_mouth_bbox values must be numeric")
            bbox = [float(value) for value in raw_bbox]
            if (not all(math.isfinite(value) for value in bbox)
                    or any(value < 0.0 or value > 1.0 for value in bbox)
                    or bbox[2] <= 0.0 or bbox[3] <= 0.0
                    or bbox[0] + bbox[2] > 1.0
                    or bbox[1] + bbox[3] > 1.0):
                raise ValueError(
                    "speaker_mouth_bbox must be normalized and fit the frame")
            return bbox

        def canonical_evidence():
            return json.dumps(
                {"schema": "wangp-dspy.local-qwen-mouth-localizer/v1",
                 "frames": frame_evidence},
                sort_keys=True, separators=(",", ":"))

        frame_roles = ("start", "middle", "end")
        frame_evidence = []
        bboxes = []
        for frame_index, frame_role in enumerate(frame_roles):
            frame_record = {
                "frame_index": frame_index, "frame_role": frame_role,
                "status": "in_progress", "attempts": []}
            frame_evidence.append(frame_record)
            for attempt_number in (1, 2):
                locator_content = [{"type": "text", "text": (
                    f"Locate the EXPECTED SPEAKER'S MOUTH in this one "
                    f"{frame_role} generated frame. Expected speaker "
                    f"and silent counterpart: {expected_speaker}. Return "
                    "STRICT JSON only as "
                    '{"speaker_mouth_bbox": [x,y,width,height]} '
                    "with normalized 0..1 coordinates. The box tightly covers "
                    "only the speaker's lips/mouth opening—not chin, jaw, "
                    "neck, or whole face. The mouth may be closed; still "
                    "locate the lips.")},
                    {"type": "image_url", "image_url": {"url": (
                        ModelScopeVisionJudge._data_url(
                            generated_frames[frame_index]))}}]
                try:
                    locator, locator_raw = request(locator_content)
                    try:
                        bbox = valid_bbox(locator)
                    except ValueError as exc:
                        raise LocalQwenVisionJudgeError(
                            str(exc), raw_response=locator_raw) from exc
                    frame_record["attempts"].append(attempt_evidence(
                        "success", locator_raw, bbox=bbox))
                    frame_record["status"] = "success"
                    frame_record["bbox"] = bbox
                    bboxes.append(bbox)
                    break
                except LocalQwenVisionJudgeError as exc:
                    transport_failure = exc.transport_failure
                    attempt_raw_response = exc.raw_response
                    attempt_error = exc
                except Exception as exc:
                    transport_failure = True
                    attempt_raw_response = None
                    attempt_error = exc
                status = ("transport_failure" if transport_failure
                          else "malformed")
                frame_record["attempts"].append(attempt_evidence(
                    status, attempt_raw_response, error=attempt_error))
                frame_record["status"] = (
                    "transport_failure" if transport_failure
                    else "retry_exhausted")
                if transport_failure or attempt_number == 2:
                    raise LocalQwenVisionJudgeError(
                        f"frame {frame_index + 1} mouth localization "
                        f"failed: {attempt_error}",
                        scores={key: result[key] for key in _SCORE_KEYS},
                        raw_response=raw_response,
                        mouth_bbox_raw_response=canonical_evidence(),
                        transport_failure=transport_failure) from attempt_error

        result["speaker_mouth_bboxes"] = bboxes
        result["mouth_bbox_raw_response"] = canonical_evidence()
        return {**result, "critic": f"local:{self.model}",
                "raw_response": raw_response}


def build_local_qwen_vision_judge(**kwargs) -> LocalQwenVisionJudge:
    """Construct the local judge; missing host/config fails closed."""
    return LocalQwenVisionJudge(**kwargs)


__all__ = ["LocalQwenVisionJudge", "LocalQwenVisionJudgeError",
           "build_local_qwen_vision_judge", "DEFAULT_LOCAL_VISION_ENDPOINT",
           "DEFAULT_LOCAL_VISION_MODEL"]
