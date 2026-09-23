"""Real-process no-GPU coverage for typed sound-effect planning."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from predict.audio_post import (
    AudioPostOperation,
    AudioPostRequest,
    attach_manifest_model,
    load_audio_post_model_manifest,
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_sound_effect_request_normalizes_typed_duration_and_format() -> None:
    root = Path(__file__).resolve().parents[1]
    source = root / "datasets/runs/provenance/lf002-vibevoice-film-20260917/cut1.mp4"
    models = Path(__file__).resolve().parent / "sfx-models.fixture.json"
    request = Path(__file__).resolve().parent / "sfx-request.fixture.json"
    models.write_text(json.dumps({"models": [{
        "family": "stable_audio", "preset": "sound_effect", "sha256": "a" * 64,
        "license": "operator-recorded license", "license_accepted": True,
        "source": "operator inventory", "usage_constraint": "recorded constraint",
        "vram_profile": "16gb",
    }]}), encoding="utf-8")
    request.write_text(json.dumps({
        "schema_version": "wangp-dspy.audio-post-request/v1",
        "model": {"family": "stable_audio", "preset": "sound_effect"},
        "operation": "sfx",
        "prompt": "distant metal gate latch with dry room tail",
        "duration_s": 2.3,
        "source": {
            "path": str(source), "sha256": _hash(source), "immutable": True,
            "video": {"index": 0, "codec_type": "video", "duration_s": 2.333333},
            "audio": {"index": 1, "codec_type": "audio", "duration_s": 2.304},
        },
        "output": {"container": "wav", "codec": "pcm_s16le", "sample_rate_hz": 48000, "channels": 2},
        "output_path_planned": str(Path(__file__).resolve().parent / "planned-effect.wav"),
        "recipe_seed": 907,
    }), encoding="utf-8")
    payload = json.loads(request.read_text(encoding="utf-8"))
    normalized = attach_manifest_model(payload, load_audio_post_model_manifest(models))
    assert isinstance(normalized, AudioPostRequest)
    assert normalized.operation is AudioPostOperation.sfx
    assert normalized.duration_s == 2.3
    assert normalized.source.immutable is True
    models.unlink()
    request.unlink()
