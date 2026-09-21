"""Blocking temporal audio/video synchrony gate.

The production backend is SyncNet v2 running on the model-equipped render
host.  The repository wrapper validates the mouth-box input, dispatches
through RenderHost.run_argv, and preserves the full SyncNet evidence object.
This method measures audio/lip embedding synchrony; it does not claim
phoneme-level correctness.
"""
from __future__ import annotations

import json
import math
import os
import hashlib
from pathlib import Path
from typing import Callable, Mapping, Sequence

from qc.audio_critic.syncnet_runner import (
    SYNCNET_METHOD, SYNCNET_MODEL_SHA256,
)


class AVSyncGateError(ValueError):
    """Typed rejection carrying complete SyncNet evidence."""

    def __init__(self, message: str, *, evidence=None):
        super().__init__(message)
        self.evidence = dict(evidence) if isinstance(evidence, Mapping) else None


def _parse_bbox(value: object) -> tuple[float, float, float, float]:
    if (not isinstance(value, Sequence) or isinstance(value, (str, bytes))
            or len(value) != 4):
        raise AVSyncGateError(
            "speaker_mouth_bbox: expected [x, y, width, height]")
    try:
        bbox = tuple(float(item) for item in value)
    except (TypeError, ValueError) as exc:
        raise AVSyncGateError(
            "speaker_mouth_bbox: numeric values required") from exc
    if not all(math.isfinite(value) for value in bbox):
        raise AVSyncGateError("speaker_mouth_bbox: finite values required")
    if (any(value < 0.0 or value > 1.0 for value in bbox)
            or bbox[2] <= 0.0 or bbox[3] <= 0.0
            or bbox[0] + bbox[2] > 1.0001
            or bbox[1] + bbox[3] > 1.0001):
        raise AVSyncGateError(
            "speaker_mouth_bbox: must be normalized and fit inside the frame")
    return bbox


def _validate_evidence(payload: object, video_path: str,
                       bbox: tuple[float, float, float, float]) -> dict:
    if not isinstance(payload, Mapping):
        raise AVSyncGateError("SyncNet judge must return an object")
    evidence = dict(payload)
    required = (
        "method", "model_sha256", "offset_frames_25fps", "offset_seconds",
        "confidence", "passed", "phonetic_sync_verified", "crop_results")
    missing = [name for name in required if name not in evidence]
    if missing:
        raise AVSyncGateError(
            f"SyncNet evidence missing field(s): {missing}")
    if evidence["method"] != SYNCNET_METHOD:
        raise AVSyncGateError(
            f"SyncNet method mismatch: {evidence['method']!r}")
    if evidence["model_sha256"] != SYNCNET_MODEL_SHA256:
        raise AVSyncGateError("SyncNet model SHA-256 mismatch")
    if not isinstance(evidence["crop_results"], list):
        raise AVSyncGateError("SyncNet crop_results must be an array")
    try:
        offset = int(evidence["offset_frames_25fps"])
        confidence = float(evidence["confidence"])
    except (TypeError, ValueError) as exc:
        raise AVSyncGateError(
            "SyncNet offset/confidence must be numeric") from exc
    if not math.isfinite(confidence):
        raise AVSyncGateError("SyncNet confidence must be finite")
    evidence["offset_frames_25fps"] = offset
    evidence["confidence"] = confidence
    evidence["video_path"] = video_path
    evidence["speaker_mouth_bbox"] = list(bbox)
    return evidence


class RemoteSyncNetAVSyncJudge:
    """Dispatch the repo SyncNet runner through RenderHost argv."""

    def __init__(self, *, host, model_path: str | None = None,
                 host_python: str | None = None,
                 host_repo: str | None = None, timeout_s: float = 300.0):
        if host is None or not callable(getattr(host, "run_argv", None)):
            raise AVSyncGateError(
                "a RenderHost with run_argv is required for SyncNet")
        if not callable(getattr(host, "map_path", None)):
            raise AVSyncGateError(
                "a RenderHost with map_path is required for SyncNet")
        if not callable(getattr(host, "makedirs", None)):
            raise AVSyncGateError(
                "a RenderHost with makedirs is required for SyncNet")
        if not callable(getattr(host, "push_file", None)):
            raise AVSyncGateError(
                "a RenderHost with push_file is required for SyncNet")
        self.host = host
        self.model_path = (
            model_path or os.environ.get("WANGP_SYNCNET_MODEL") or
            "/home/straughter/models/syncnet_v2/syncnet_v2.model")
        resolved_python = host_python or os.environ.get("WANGP_SYNCNET_PYTHON")
        if resolved_python is None:
            from wangp.config import (
                HostConfigError,
                load_host_config,
                require_wgp_python,
            )

            try:
                configured_python = require_wgp_python(
                    load_host_config(environ=os.environ)
                )
            except HostConfigError as exc:
                raise AVSyncGateError(str(exc)) from exc
            resolved_python = configured_python.value
        self.host_python = (
            host_python or os.environ.get("WANGP_SYNCNET_PYTHON") or
            resolved_python)
        self.host_repo = (
            host_repo or os.environ.get("WANGP_SYNCNET_REPO") or
            "/home/straughter/wangp-dspy-vibevoice-20260916")
        try:
            self.timeout_s = float(
                os.environ.get("WANGP_SYNCNET_TIMEOUT", timeout_s))
        except (TypeError, ValueError) as exc:
            raise AVSyncGateError(
                "WANGP_SYNCNET_TIMEOUT must be numeric") from exc
        if self.timeout_s <= 0:
            raise AVSyncGateError("SyncNet timeout must be positive")
        for label, value in (
                ("model_path", self.model_path),
                ("host_python", self.host_python),
                ("host_repo", self.host_repo)):
            if not isinstance(value, str) or not value.strip():
                raise AVSyncGateError(f"SyncNet {label} is required")

    def __call__(self, *, video_path: str,
                 speaker_mouth_bbox: object) -> dict:
        bbox = _parse_bbox(speaker_mouth_bbox)
        local_video = Path(video_path)
        if not local_video.is_file():
            raise AVSyncGateError(
                f"local SyncNet video artifact is missing: {video_path}")
        video_sha256 = hashlib.sha256(local_video.read_bytes()).hexdigest()
        remote_video = self.host.map_path(video_path)
        # The native final/remux artifact is produced in the local pull
        # namespace.  The remote worker directory may contain only raw.mp4;
        # never silently score a different host-side file.  Publish the exact
        # final artifact and make the remote runner verify its hash.
        self.host.makedirs(str(Path(remote_video).parent))
        pushed = self.host.push_file(str(local_video), str(remote_video))
        if pushed != str(remote_video):
            raise AVSyncGateError(
                "SyncNet host video staging path mismatch: "
                f"{pushed!r} != {str(remote_video)!r}")
        command = [
            self.host_python, "-m", "qc.audio_critic.syncnet_runner",
            "--video", str(remote_video),
            "--bbox", *(str(value) for value in bbox),
            "--model", self.model_path,
            "--video-sha256", video_sha256,
        ]
        result = self.host.run_argv(
            command, cwd=self.host_repo, timeout=self.timeout_s)
        stdout = str(getattr(result, "stdout", "") or "")
        stderr = str(getattr(result, "stderr", "") or "")
        candidates = [line for line in stdout.splitlines() if line.strip()]
        payload = None
        try:
            payload = json.loads(candidates[-1]) if candidates else None
        except json.JSONDecodeError:
            payload = None
        if getattr(result, "returncode", None) != 0 or not isinstance(
                payload, Mapping) or payload.get("status") != "complete":
            detail = (stderr or stdout).strip()[-4000:]
            raise AVSyncGateError(
                f"remote SyncNet execution failed "
                f"(rc={getattr(result, 'returncode', None)}): {detail}",
                evidence=payload)
        evidence = _validate_evidence(payload, video_path, bbox)
        evidence["video_sha256"] = video_sha256
        evidence["remote_video_path"] = str(remote_video)
        return evidence


def build_remote_syncnet_judge(host, **kwargs) -> RemoteSyncNetAVSyncJudge:
    return RemoteSyncNetAVSyncJudge(host=host, **kwargs)


def run_av_sync_gate(
    video_path: str,
    *,
    speaker_mouth_bbox: object,
    judge: Callable[..., Mapping],
) -> dict:
    """Run the mandatory temporal AV gate and preserve its evidence."""
    if not isinstance(video_path, str) or not video_path:
        raise AVSyncGateError("video_path: required")
    bbox = _parse_bbox(speaker_mouth_bbox)
    if judge is None:
        raise AVSyncGateError(
            "SyncNet judge is not wired; refusing ungated audiovisual artifact")
    try:
        raw = judge(
            video_path=video_path,
            speaker_mouth_bbox=list(bbox))
    except AVSyncGateError:
        raise
    except Exception as exc:
        raise AVSyncGateError(
            f"SyncNet judge failed: {exc}",
            evidence=getattr(exc, "evidence", None)) from exc
    evidence = _validate_evidence(raw, video_path, bbox)
    if evidence.get("passed") is not True:
        raise AVSyncGateError(
            "audiovisual SyncNet gate failed", evidence=evidence)
    if evidence.get("phonetic_sync_verified") is not False:
        raise AVSyncGateError(
            "SyncNet evidence must not claim phonetic verification")
    return evidence


__all__ = [
    "AVSyncGateError", "RemoteSyncNetAVSyncJudge",
    "build_remote_syncnet_judge", "run_av_sync_gate",
]
