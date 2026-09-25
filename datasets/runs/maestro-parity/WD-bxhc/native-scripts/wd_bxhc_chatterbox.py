#!/usr/bin/env python3
"""Run the real WanGP Chatterbox multilingual plain-speech operation."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import soundfile as sf
import torch


WGP = Path("/home/straughter/Wan2GP")
ASSETS = WGP / "models" / "TTS"
OUTPUT = Path(
    "/home/straughter/wangp-dspy-vibevoice-20260916/datasets/runs/maestro-parity/"
    "WD-bxhc/outputs/wd_bxhc_chatterbox_speech.wav"
)
REPORT = OUTPUT.with_name("chatterbox-report.json")
FFPROBE = OUTPUT.with_name("ffprobe-wd_bxhc_chatterbox_speech.json")
TEXT = "Portable character evidence begins with a stable and intelligible voice."
SEED = 9401


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(argv: list[str], *, stdout: Path | None = None, timeout: int = 120) -> None:
    completed = subprocess.run(
        argv, check=False, timeout=timeout, text=True,
        stdout=subprocess.PIPE if stdout is None else stdout.open("w"),
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(argv)}: "
            f"{completed.stderr}")


def gpu_state() -> dict[str, object]:
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=memory.total,memory.used,memory.free",
            "--format=csv,noheader,nounits",
        ],
        check=True, text=True, capture_output=True, timeout=30,
    )
    total, used, free = (int(item.strip()) for item in result.stdout.strip().split(","))
    compute = subprocess.run(
        [
            "nvidia-smi", "--query-compute-apps=pid,used_memory,process_name",
            "--format=csv,noheader,nounits",
        ],
        check=True, text=True, capture_output=True, timeout=30,
    ).stdout.strip()
    return {"total_mib": total, "used_mib": used, "free_mib": free, "compute_apps": compute}


def main() -> int:
    sys.path.insert(0, str(WGP))
    from shared.utils import files_locator as fl

    fl.set_checkpoints_paths([str(ASSETS), str(WGP / "ckpts")])
    from models.TTS.chatterbox.mtl_tts import ChatterboxMultilingualTTS

    before = gpu_state()
    if before["free_mib"] < 4096:
        raise RuntimeError(f"insufficient free VRAM beside operator judge: {before}")
    if "llama-server" not in str(before["compute_apps"]):
        raise RuntimeError(f"operator llama-server is not the observed tenant: {before}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists() or REPORT.exists() or FFPROBE.exists():
        raise RuntimeError("Chatterbox output namespace is not fresh")
    torch.manual_seed(SEED)
    model = ChatterboxMultilingualTTS.from_local(ASSETS, torch.device("cuda"))
    device = torch.device("cuda")
    model.ve.to(device)
    model.t3.to(device)
    model.s3gen.to(device)
    if model.conds is not None:
        model.conds.to(device)
    waveform = model.generate(
        text=TEXT,
        language_id="en",
        audio_prompt_path=None,
        exaggeration=0.5,
        cfg_weight=0.5,
        temperature=0.8,
        repetition_penalty=2.0,
        min_p=0.05,
        top_p=1.0,
    )
    audio = waveform.detach().cpu().numpy().squeeze()
    if audio.ndim != 1:
        raise RuntimeError(f"expected mono waveform, got shape {audio.shape}")
    sf.write(OUTPUT, audio, int(model.sr), subtype="PCM_16")
    del model
    torch.cuda.empty_cache()

    run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json",
        str(OUTPUT),
    ], stdout=FFPROBE, timeout=60)
    probe = json.loads(FFPROBE.read_text(encoding="utf-8"))
    stream = next(item for item in probe["streams"] if item.get("codec_type") == "audio")
    duration = float(stream["duration"])
    if (
        int(stream["sample_rate"]) != 24000
        or int(stream["channels"]) != 1
        or duration <= 0
    ):
        raise RuntimeError(f"Chatterbox output violates 24 kHz mono contract: {stream}")

    after = gpu_state()
    report = {
        "schema": "wangp-dspy.wd-bxhc.chatterbox-run/v1",
        "status": "succeeded",
        "text": TEXT,
        "language_id": "en",
        "seed": SEED,
        "model_root": str(ASSETS),
        "model_files": {
            name: sha256(ASSETS / "chatterbox" / name)
            for name in (
                "t3_mtl23ls_v2.safetensors", "s3gen.pt", "ve.safetensors",
                "conds.pt", "grapheme_mtl_merged_expanded_v1.json",
                "Cangjie5_TC.json",
            )
        },
        "reference_mode": "built-in non-consented-human-free conditionals",
        "license": "MIT (ResembleAI Chatterbox upstream); operator research/evaluation only",
        "output": str(OUTPUT),
        "output_sha256": sha256(OUTPUT),
        "sample_rate_hz": int(stream["sample_rate"]),
        "channels": int(stream["channels"]),
        "duration_s": duration,
        "codec": stream["codec_name"],
        "gpu_before": before,
        "gpu_after": after,
        "llama_server_untouched": "llama-server" in str(after["compute_apps"]),
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
