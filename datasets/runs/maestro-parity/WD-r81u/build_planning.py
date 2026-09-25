#!/usr/bin/env python3
"""Emit typed no-GPU requests for the operations actually attempted."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


BUNDLE = Path(__file__).resolve().parent
SOURCE = BUNDLE / "inputs/source.mp4"
MODEL_HASH_LINE = (BUNDLE / "realesrgan-model-hashes.txt").read_text(encoding="utf-8").splitlines()[0]
MODEL_SHA256 = MODEL_HASH_LINE.split()[0]
SOURCE_SHA256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()

BASE = {
    "schema_version": "wangp-dspy.finishing-request/v1",
    "source": {
        "path": str(SOURCE),
        "sha256": SOURCE_SHA256,
        "immutable": True,
        "measurement": "declared_ffprobe_unverified",
        "stream": {
            "index": 0,
            "codec_name": "h264",
            "codec_type": "video",
            "width": 480,
            "height": 832,
            "duration_s": 2.333333,
            "avg_frame_rate": "24/1",
        },
    },
    "output": {
        "path": "",
        "container": "mp4",
        "codec": "h264",
        "overwrite": False,
        "measurement": "planned_ffprobe_unverified",
    },
    "recipe_seed": 8107,
}

SPECS = {
    "ffmpeg-interpolation": ("ffmpeg", {"interpolation": {"factor": "x2", "target_fps": 48.0, "scene_detection": True}}),
    "ffmpeg-spatial": ("ffmpeg", {"spatial_upscale": {"scale": "x2", "model_sha256": None}}),
    "ffmpeg-grain": ("ffmpeg", {"film_grain": {"strength": 12.0, "size": 16, "temporal_persistence": 0.5}}),
    "rife-interpolation": ("rife", {"interpolation": {"factor": "x2", "target_fps": 48.0, "scene_detection": True}}),
    "film-grain": ("film", {"film_grain": {"strength": 12.0, "size": 16, "temporal_persistence": 0.5}}),
    "real-esrgan-spatial": ("real_esrgan", {"spatial_upscale": {"scale": "x2", "model_sha256": MODEL_SHA256}}),
}


def main() -> int:
    request_root = BUNDLE / "planning/requests"
    request_root.mkdir(parents=True, exist_ok=True)
    for name, (backend, operation) in SPECS.items():
        payload = json.loads(json.dumps(BASE))
        payload["backend"] = backend
        payload.update(operation)
        payload["output"]["path"] = str(BUNDLE / f"planning/planned-{name}.mp4")
        (request_root / f"{name}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps({"requests": len(SPECS), "real_esrgan_model_sha256": MODEL_SHA256}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
