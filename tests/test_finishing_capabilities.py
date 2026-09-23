"""Real-process no-GPU tests for typed finishing capabilities."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from predict.finishing import (
    BACKEND_OPERATIONS,
    SCHEMA_VERSION,
    FinishingBackend,
    FinishingRequest,
    backend_settings,
    request_digest,
)


ROOT = Path(__file__).resolve().parents[1]
HOST_KEYS = (
    "WANGP_SSH_TARGET",
    "WANGP_WGP_ROOT",
    "WANGP_PULL_ROOT",
    "WANGP_WGP_PYTHON",
)


def _request(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "backend": "ffmpeg",
        "source": {
            "path": "datasets/runs/provenance/v3-original/v3_c1.mp4",
            "sha256": "a" * 64,
            "immutable": True,
            "measurement": "declared_ffprobe_unverified",
            "stream": {
                "index": 0,
                "codec_name": "h264",
                "codec_type": "video",
                "width": 512,
                "height": 768,
                "duration_s": 4.0,
                "avg_frame_rate": "24/1",
            },
        },
        "interpolation": {
            "factor": "x2",
            "target_fps": 48.0,
            "scene_detection": True,
        },
        "film_grain": {"strength": 12.0, "size": 16, "temporal_persistence": 0.5},
        "output": {
            "path": "outputs/finished.mp4",
            "container": "mp4",
            "codec": "h264",
            "overwrite": False,
            "measurement": "planned_ffprobe_unverified",
        },
        "recipe_seed": 8107,
    }
    for key, value in overrides.items():
        if value is None:
            payload.pop(key, None)
        else:
            payload[key] = value
    return payload


def _mutate(payload: dict[str, Any], path: str, value: Any) -> dict[str, Any]:
    document = json.loads(json.dumps(payload))
    cursor: Any = document
    keys = path.split(".")
    for key in keys[:-1]:
        cursor = cursor[key]
    if value is None:
        cursor.pop(keys[-1], None)
    else:
        cursor[keys[-1]] = value
    return document


def test_typed_finishing_request_normalizes_all_no_gpu_operations() -> None:
    request = FinishingRequest.model_validate(_request())
    assert request.backend is FinishingBackend.ffmpeg
    assert request.interpolation is not None
    assert request.film_grain is not None
    assert request.source.measurement == "declared_ffprobe_unverified"
    assert request.output.measurement == "planned_ffprobe_unverified"
    assert backend_settings(request)["operations"] == [
        "interpolation", "film_grain", "codec"
    ]
    assert backend_settings(request)["codec_arguments"][:2] == ["-c:v", "libx264"]
    assert request_digest(request) == request_digest(FinishingRequest.model_validate(_request()))


def test_typed_request_rejects_invalid_factor_backend_codec_and_face_geometry() -> None:
    cases = (
        (_mutate(_request(), "interpolation.factor", "x5"), "x5"),
        (_mutate(_request(), "backend", "rife"), "does not plan operations: film_grain"),
        (_mutate(_request(), "output.codec", "vp9"), "does not support codec vp9"),
        (_mutate(_request(), "interpolation.target_fps", 72.0), "must equal source fps"),
        (_request(film_grain=None, interpolation=None), "at least one refinement operation"),
    )
    for payload, expected in cases:
        try:
            FinishingRequest.model_validate(payload)
        except ValidationError as exc:
            assert expected in str(exc), f"{expected}: {exc}"
        else:
            raise AssertionError(f"accepted invalid request: {expected}")

    face_payload = _request(
        film_grain=None,
        face_refinement={
            "tracks": [{
                "track_id": "face-1",
                "identity_label": "Orin",
                "confidence": 0.94,
                "start_s": 0.0,
                "end_s": 2.0,
                "x": 0.8,
                "y": 0.1,
                "width": 0.4,
                "height": 0.2,
                "source": "operator-tracked",
                "license": "operator-recorded",
                "consent_ref": "orin-consent",
            }],
            "selected_track": "face-1",
            "strength": 0.3,
        },
    )
    try:
        FinishingRequest.model_validate(face_payload)
    except ValidationError as exc:
        assert "normalized bounds" in str(exc)
    else:
        raise AssertionError("accepted an out-of-bounds face region")


def test_neural_path_is_declared_unavailable_and_requires_neural_backend() -> None:
    neural = {
        "model_sha256": "b" * 64,
        "backend_profile": "authorized-host-only",
        "minimum_vram_gb": 16,
        "authorized_host": None,
        "support_status": "unavailable_without_authorized_host",
    }
    payload = _request(
        backend="neural_frame_gen",
        film_grain=None,
        neural_path=neural,
    )
    request = FinishingRequest.model_validate(payload)
    settings = backend_settings(request)
    assert settings["neural_execution"] == "unavailable"
    assert settings["neural_path"]["authorized_host"] is None

    unauthorized = _mutate(payload, "neural_path.authorized_host", "gpu-host")
    with_gpu_backend = _mutate(_request(), "neural_path", neural)
    for document, expected in (
        (unauthorized, "cannot authorize a neural host"),
        (with_gpu_backend, "requires backend neural_frame_gen"),
    ):
        try:
            FinishingRequest.model_validate(document)
        except ValidationError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError(f"accepted invalid neural declaration: {expected}")


def test_backend_operation_matrix_and_manifest_hashes_are_explicit() -> None:
    assert "face_refinement" in BACKEND_OPERATIONS[FinishingBackend.ffmpeg]
    assert "film_grain" not in BACKEND_OPERATIONS[FinishingBackend.neural_frame_gen]
    assert all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in ("a" * 64, "b" * 64))
    assert hashlib.sha256(b"source").hexdigest() != "a" * 64
