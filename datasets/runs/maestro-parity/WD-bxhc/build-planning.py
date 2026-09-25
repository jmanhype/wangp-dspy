#!/usr/bin/env python3
"""Build typed WD-bxhc speech requests and exact native settings."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


BUNDLE = Path(__file__).resolve().parent
SCHEMA = "wangp-dspy.speech-capability-request/v1"
CHATTERBOX_ASSETS = {
    "t3_mtl23ls_v2.safetensors": "b1237586127ce98e7800a68e49938eb5092846862aabcb6e17b2fda7889a6c75",
    "s3gen.pt": "9b9ff07e60b20c136e2b1b3d7563a24604e8d2c4c267888d1ee929dd0151d2a3",
    "ve.safetensors": "f0921cab452fa278bc25cd23ffd59d36f816d7dc5181dd1bef9751a7fb61f63c",
    "conds.pt": "6552d70568833628ba019c6b03459e77fe71ca197d5c560cef9411bee9d87f4e",
    "grapheme_mtl_merged_expanded_v1.json": "df81a7ca7c31796cbe97f7a7142d5a53b12e88e12417ebe98f66602cafaf0461",
    "Cangjie5_TC.json": "7073fd9de919443ae88e0bd2449917a65fe54898a4413ed1edcc4b67f28bce8c",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def reference(name: str, role: str, duration_s: float) -> dict[str, object]:
    path = BUNDLE / "inputs" / name
    primary = role == "primary"
    return {
        "path": str(path),
        "sha256": sha256(path),
        "role": role,
        "duration_s": duration_s,
        "source": (
            "WD-bxhc Chatterbox output generated from built-in non-human conditionals"
            if primary else
            "WD-cpow operator-owned synthetic target voice, reused only as a reference"
        ),
        "license": (
            "Operator-owned synthetic WD-bxhc output; MIT Chatterbox upstream; no redistribution"
            if primary else
            "Operator-owned synthetic WD-cpow evaluation asset; authorized reference reuse only; no redistribution"
        ),
        "consent_ref": (
            "operator-authorization.md#wd-bxhc-synthetic-primary"
            if primary else
            "operator-authorization.md#wd-cpow-synthetic-secondary"
        ),
    }


def request(
    family: str,
    preset: str,
    mode: str,
    text: str,
    output: str,
    seed: int,
    references: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA,
        "model": {"family": family, "preset": preset},
        "mode": mode,
        "text": text,
        "language": "en-US",
        "style": "clear neutral narrator",
        "references": references,
        "segment_policy": {
            "max_segment_chars": 600,
            "max_segment_duration_s": 20.0,
            "silence_s": 0.20,
            "split_on_sentence": True,
        },
        "output_path_planned": str(BUNDLE / output),
        "recipe_seed": seed,
    }


def main() -> int:
    chatterbox_anchor = hashlib.sha256(
        json.dumps(CHATTERBOX_ASSETS, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    models = {
        "models": [
            {
                "family": "vibevoice",
                "preset": "vibe_7b",
                "sha256": "183be9ae11700a9f8cee4f00ef974b9ef3e7c01f13b55457f5fe025a1e8e57eb",
                "license": "Apache-2.0 (VibeVoice upstream); operator research/evaluation limitation",
                "license_accepted": True,
                "source": "https://huggingface.co/microsoft/VibeVoice-7B (pre-existing /mnt/bulk/straughter/models/VibeVoice-7B-hf)",
                "usage_constraint": "WD-bxhc plain speech and one/two-reference synthetic-voice cloning; no training or redistribution",
                "vram_profile": "24gb",
            },
            {
                "family": "chatterbox",
                "preset": "chatterbox_multilingual",
                "sha256": chatterbox_anchor,
                "license": "MIT (ResembleAI Chatterbox upstream); operator research/evaluation only",
                "license_accepted": True,
                "source": "https://huggingface.co/DeepBeepMeep/TTS (six-file set under models/TTS/chatterbox)",
                "usage_constraint": "WD-bxhc plain speech only; no training or redistribution",
                "vram_profile": "16gb",
            },
        ]
    }
    write_json(BUNDLE / "planning" / "models.json", models)

    chatterbox_text = "Portable character evidence begins with a stable and intelligible voice."
    requests = {
        "chatterbox-speech.json": request(
            "chatterbox", "chatterbox_multilingual", "speech", chatterbox_text,
            "outputs/wd_bxhc_chatterbox_speech.wav", 9401, [],
        ),
        "vibevoice-speech.json": request(
            "vibevoice", "vibe_7b", "speech",
            "The portable witness speaks plainly without claiming another voice.",
            "outputs/wd_bxhc_vibevoice_speech.wav", 9411, [],
        ),
        "vibevoice-clone-one.json": request(
            "vibevoice", "vibe_7b", "voice_clone",
            "One reference keeps this speaker on the portable anchor.",
            "outputs/wd_bxhc_vibevoice_clone_one.wav", 9421,
            [reference("voice-primary.wav", "primary", 5.08)],
        ),
        "vibevoice-clone-two.json": request(
            "vibevoice", "vibe_7b", "voice_clone",
            "Two references keep this speaker on the portable anchor.",
            "outputs/wd_bxhc_vibevoice_clone_two.wav", 9431,
            [
                reference("voice-primary.wav", "primary", 5.08),
                reference("voice-secondary.wav", "secondary", 2.364958),
            ],
        ),
    }
    for name, payload in requests.items():
        write_json(BUNDLE / "planning" / "requests" / name, payload)

    character = {
        "character_id": "Portable Witness",
        "speaker_label": "Witness",
        "voice_binding_id": "portable-witness-v1",
        "appearance": {
            "path": str(BUNDLE / "inputs" / "appearance-native.png"),
            "sha256": sha256(BUNDLE / "inputs" / "appearance-native.png"),
        },
    }
    requests["vibevoice-clone-two.json"] = dict(requests["vibevoice-clone-two.json"])
    requests["vibevoice-clone-two.json"]["character"] = character
    write_json(BUNDLE / "planning" / "requests" / "vibevoice-clone-two.json", requests["vibevoice-clone-two.json"])

    native_manifest = {
        "schema": "wangp-dspy.vibevoice-turns/v1",
        "model": "/mnt/bulk/straughter/models/VibeVoice-7B-hf",
        "model_sha256": "183be9ae11700a9f8cee4f00ef974b9ef3e7c01f13b55457f5fe025a1e8e57eb",
        "seed": 9411,
        "turns": [
            {
                "speaker": "Witness",
                "text": "The portable witness speaks plainly without claiming another voice.",
                "voice_reference": str(BUNDLE / "inputs" / "voice-primary.wav"),
                "output": "outputs/wd_bxhc_vibevoice_speech.wav",
                "target_duration_s": 3.5,
            },
            {
                "speaker": "Witness",
                "text": "One reference keeps this speaker on the portable anchor.",
                "voice_reference": str(BUNDLE / "inputs" / "voice-primary.wav"),
                "output": "outputs/wd_bxhc_vibevoice_clone_one.wav",
                "target_duration_s": 3.5,
            },
        ],
    }
    write_json(BUNDLE / "vibevoice-turns.json", native_manifest)
    write_json(BUNDLE / "chatterbox-model-anchor.json", {
        "schema": "wangp-dspy.wd-bxhc.chatterbox-anchor/v1",
        "algorithm": "sha256(canonical-json(sorted filename -> file sha256))",
        "files": CHATTERBOX_ASSETS,
        "combined_sha256": chatterbox_anchor,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
