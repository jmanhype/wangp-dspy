#!/usr/bin/env python3
"""Run WD-bxhc VibeVoice plain/one-reference/two-reference operations."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import torch


HOST_REPO = Path("/home/straughter/wangp-dspy-vibevoice-20260916")
BUNDLE = HOST_REPO / "datasets" / "runs" / "maestro-parity" / "WD-bxhc"
MODEL = Path("/mnt/bulk/straughter/models/VibeVoice-7B-hf")
PRIMARY = BUNDLE / "inputs" / "voice-primary-vibe.wav"
SECONDARY = BUNDLE / "inputs" / "voice-secondary.wav"
REPORT = BUNDLE / "vibevoice-custom-report.json"
PASS_BAR = 0.8
SEED_RETRIES = 2

OPERATIONS = [
    {
        "mode": "speech",
        "text": "The portable witness speaks plainly without claiming another voice.",
        "references": [PRIMARY],
        "output": BUNDLE / "outputs" / "wd_bxhc_vibevoice_speech.wav",
        "seed": 9411,
        "target_duration_s": 3.5,
    },
    {
        "mode": "voice_clone_one_reference",
        "text": "One reference keeps this speaker on the portable anchor.",
        "references": [PRIMARY],
        "output": BUNDLE / "outputs" / "wd_bxhc_vibevoice_clone_one.wav",
        "seed": 9421,
        "target_duration_s": 3.5,
    },
    {
        "mode": "voice_clone_two_references",
        "text": "Two references keep this speaker on the portable anchor.",
        "references": [PRIMARY, SECONDARY],
        "output": BUNDLE / "outputs" / "wd_bxhc_vibevoice_clone_two.wav",
        "seed": 9431,
        "target_duration_s": 3.5,
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def runner(argv: list[str]):
    return subprocess.run(argv, capture_output=True, text=True, check=False, timeout=900)


def gpu_state() -> dict[str, object]:
    query = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.total,memory.used,memory.free",
         "--format=csv,noheader,nounits"],
        check=True, text=True, capture_output=True, timeout=30,
    )
    total, used, free = (int(value.strip()) for value in query.stdout.strip().split(","))
    apps = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid,used_memory,process_name",
         "--format=csv,noheader,nounits"],
        check=True, text=True, capture_output=True, timeout=30,
    ).stdout.strip()
    return {"total_mib": total, "used_mib": used, "free_mib": free, "compute_apps": apps}


def execution_device(model) -> str:
    device_map = getattr(model, "hf_device_map", None)
    if isinstance(device_map, dict):
        for value in device_map.values():
            if isinstance(value, int) and value >= 0:
                return f"cuda:{value}"
            text = str(value)
            if text.startswith(("cuda:", "xpu:", "npu:", "hpu:")) or text == "cuda":
                return text
    for parameter in model.parameters():
        text = str(getattr(parameter, "device", ""))
        if text.startswith(("cuda:", "xpu:", "npu:", "hpu:")) or text == "cuda":
            return text
    raise RuntimeError("no concrete accelerator placement")


def ffprobe(path: Path, destination: Path) -> dict[str, object]:
    subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True, timeout=60, stdout=destination.open("w"), stderr=subprocess.PIPE, text=True,
    )
    payload = json.loads(destination.read_text(encoding="utf-8"))
    stream = next(item for item in payload["streams"] if item.get("codec_type") == "audio")
    return {
        "codec": stream["codec_name"],
        "sample_rate_hz": int(stream["sample_rate"]),
        "channels": int(stream["channels"]),
        "duration_s": float(stream["duration"]),
    }


def reference_record(path: Path) -> dict[str, str]:
    primary = path == PRIMARY
    return {
        "path": str(path),
        "sha256": sha256(path),
        "role": "primary" if primary else "secondary",
        "source": (
            "WD-cpow operator-owned synthetic target voice, reused only as the primary reference"
            if primary else
            "WD-cpow VibeVoice-prepared synthetic output, reused only as the secondary reference"
        ),
        "license": (
            "Operator-owned synthetic WD-bxhc output; MIT Chatterbox upstream; no redistribution"
            if primary else
            "Operator-owned synthetic WD-cpow evaluation asset; authorized reference reuse only; no redistribution"
        ),
        "consent_ref": (
            "operator-authorization.md#wd-cpow-synthetic-primary"
            if primary else
            "operator-authorization.md#wd-cpow-synthetic-secondary"
        ),
    }


def main() -> int:
    os.environ["PATH"] = "/home/straughter/Wan2GP/venv/bin:" + os.environ.get("PATH", "")
    sys.path.insert(0, str(HOST_REPO))
    from predict.audio_prep import prepare_turn_audio
    from qc.audio_critic.whisper_cli import whisper_transcriber
    from qc.audio_critic.whisper_gate import run_whisper_gate
    from transformers import AutoModelForTextToWaveform, AutoProcessor, set_seed

    before = gpu_state()
    if before["free_mib"] < 14000:
        raise RuntimeError(f"insufficient free VRAM beside operator judge: {before}")
    if "llama-server" not in str(before["compute_apps"]):
        raise RuntimeError(f"operator llama-server is not the observed tenant: {before}")
    expected_paths = [REPORT]
    for operation in OPERATIONS:
        raw = operation["output"]
        prepared = raw.with_suffix(".prepared.wav")
        provenance = raw.with_name(raw.name + ".vibevoice.json")
        expected_paths.extend((raw, prepared, provenance))
        for attempt in range(1, SEED_RETRIES + 2):
            expected_paths.extend((
                raw.with_name(f"{raw.stem}.attempt-{attempt}.wav"),
                raw.with_name(f"{raw.stem}.attempt-{attempt}.prepared.wav"),
                raw.with_name(f"{raw.stem}.attempt-{attempt}.wav.vibevoice.json"),
            ))
    if any(path.exists() for path in expected_paths):
        raise RuntimeError("VibeVoice output namespace is not fresh")

    processor = AutoProcessor.from_pretrained(MODEL)
    model = AutoModelForTextToWaveform.from_pretrained(
        MODEL, device_map={"": "cpu"}, max_memory={"cpu": "26GiB"},
    )
    from quanto import freeze, qint8, quantize

    # Preserve native embedding/conv tensor shapes required by VibeVoice's
    # audio-token expansion; quantize the dominant linear projections only.
    quantizable_linears = [
        module for module in model.modules() if isinstance(module, torch.nn.Linear)
    ]
    quantize(model, modules=quantizable_linears, weights=qint8)
    freeze(model)
    model.to(torch.device("cuda"))
    device = execution_device(model)
    meta_parameters = sum(
        parameter.device.type == "meta" for parameter in model.parameters()
    )
    if meta_parameters:
        meta_names = [
            name for name, parameter in model.named_parameters()
            if parameter.device.type == "meta"
        ]
        device_counts: dict[str, int] = {}
        for value in getattr(model, "hf_device_map", {}).values():
            key = str(value)
            device_counts[key] = device_counts.get(key, 0) + 1
        print(json.dumps({
            "meta_parameter_count": len(meta_names),
            "first_meta_parameters": meta_names[:80],
            "device_map_counts": device_counts,
        }, sort_keys=True), flush=True)
        raise RuntimeError(f"model contains {meta_parameters} meta parameters")

    records = []
    for operation in OPERATIONS:
        raw = operation["output"]
        raw.parent.mkdir(parents=True, exist_ok=True)
        seed_rejections = []
        record: dict[str, object] = {
            "mode": operation["mode"],
            "text": operation["text"],
            "speaker": "Witness",
            "status": "pending",
            "output": str(raw),
        }
        for attempt_index in range(1, SEED_RETRIES + 2):
            seed = operation["seed"] + attempt_index - 1
            if len(operation["references"]) == 2:
                # VibeVoice's template emits one expanded prompt per distinct
                # speaker role. Keep the requested text on speaker 0 and bind
                # the secondary reference to a distinct prompt-only role.
                conversation = [
                    {
                        "role": "0",
                        "content": [
                            {"type": "audio", "url": str(operation["references"][0])},
                            {"type": "text", "text": operation["text"]},
                        ],
                    },
                    {
                        "role": "1",
                        "content": [
                            {"type": "audio", "url": str(operation["references"][1])},
                        ],
                    },
                ]
            else:
                conversation = [{
                    "role": "0",
                    "content": [
                        *({"type": "audio", "url": str(reference)} for reference in operation["references"]),
                        {"type": "text", "text": operation["text"]},
                    ],
                }]
            set_seed(seed)
            inputs = processor.apply_chat_template(
                conversation,
                return_dict=True,
                tokenize=True,
                add_generation_prompt=True,
            ).to(device, model.dtype)
            audio = model.generate(**inputs)
            processor.save_audio(audio, str(raw))
            prepared = raw.with_suffix(".prepared.wav")
            prepared_audio = prepare_turn_audio(
                str(raw), str(prepared), speaker_id="Witness",
                target_duration_s=operation["target_duration_s"], runner=runner,
            )
            provenance_path = raw.with_name(raw.name + ".vibevoice.json")
            provenance = {
                "schema": "wangp-dspy.wd-bxhc.vibevoice-provenance/v1",
                "mode": operation["mode"],
                "text": operation["text"],
                "model": str(MODEL),
                "model_sha256": sha256(MODEL / "model.safetensors.index.json"),
                "seed": seed,
                "attempt_index": attempt_index,
                "references": [reference_record(path) for path in operation["references"]],
                "output": str(raw),
                "output_sha256": sha256(raw),
                "prepared_path": str(prepared),
                "prepared_sha256": sha256(prepared),
                "preparation": prepared_audio.to_dict(),
            }
            provenance_path.write_text(
                json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            try:
                gate = run_whisper_gate(
                    str(prepared), operation["text"],
                    transcriber=lambda audio: whisper_transcriber(
                        audio, runner=runner, model="small",
                        output_dir=str(BUNDLE / ".vibevoice-custom-whisper" / raw.stem / f"attempt-{attempt_index}"),
                    ),
                    phase="pre", pass_bar=PASS_BAR,
                ).to_dict()
            except Exception as exc:
                evidence = getattr(exc, "evidence", None)
                gate = evidence.to_dict() if evidence is not None else {
                    "phase": "pre", "passed": False, "error": str(exc),
                    "audio_path": str(prepared), "intended_text": operation["text"],
                }
            if gate.get("passed") is True:
                record.update({
                    "status": "complete",
                    "seed": seed,
                    "attempt_index": attempt_index,
                    "output_sha256": sha256(raw),
                    "prepared_path": str(prepared),
                    "prepared_sha256": sha256(prepared),
                    "preparation": prepared_audio.to_dict(),
                    "whisper_gate": gate,
                    "seed_rejections": seed_rejections,
                    "provenance_path": str(provenance_path),
                })
                break
            preserved_raw = raw.with_name(f"{raw.stem}.attempt-{attempt_index}.wav")
            preserved_prepared = raw.with_name(f"{raw.stem}.attempt-{attempt_index}.prepared.wav")
            preserved_provenance = raw.with_name(
                f"{raw.stem}.attempt-{attempt_index}.wav.vibevoice.json")
            rejection = {
                "attempt_index": attempt_index,
                "seed": seed,
                "raw_path": str(preserved_raw),
                "prepared_path": str(preserved_prepared),
                "provenance_path": str(preserved_provenance),
                "whisper_gate": gate,
            }
            seed_rejections.append(rejection)
            record.update({
                "status": "pre_gate_failed", "seed": seed,
                "attempt_index": attempt_index, "seed_rejections": seed_rejections,
            })
            os.replace(raw, preserved_raw)
            os.replace(prepared, preserved_prepared)
            os.replace(provenance_path, preserved_provenance)
            rejection["raw_sha256"] = sha256(preserved_raw)
            rejection["prepared_sha256"] = sha256(preserved_prepared)
        records.append(record)
        if record.get("status") != "complete":
            break

    after = gpu_state()
    complete = all(record.get("status") == "complete" for record in records) and len(records) == len(OPERATIONS)
    report = {
        "schema": "wangp-dspy.wd-bxhc.vibevoice-custom-run/v1",
        "status": "complete" if complete else "failed",
        "model": str(MODEL),
        "model_sha256": sha256(MODEL / "model.safetensors.index.json"),
        "model_size_bytes": sum(
            path.stat().st_size for path in MODEL.rglob("*") if path.is_file()
        ),
        "device": device,
        "placement": "CPU load verified without meta tensors; quanto int8 weights frozen on CUDA beside the untouched operator judge",
        "quantization": "quanto qint8 nn.Linear weights; embeddings and convolutions retained in source dtype",
        "meta_parameters": meta_parameters,
        "pass_bar": PASS_BAR,
        "turns": records,
        "gpu_before": before,
        "gpu_after": after,
        "llama_server_untouched": "llama-server" in str(after["compute_apps"]),
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
