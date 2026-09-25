#!/usr/bin/env python3
"""Run the bounded WD-rous ACE-Step 1.5 native operations."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path("/mnt/bulk/straughter/ACE-Step-1.5")
sys.path.insert(0, str(ROOT))
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from acestep.handler import AceStepHandler
from acestep.llm_inference import LLMHandler
from acestep.inference import GenerationConfig, GenerationParams, generate_music


def generate(target: Path) -> None:
    handler = AceStepHandler()
    message, ok = handler.initialize_service(
        project_root=str(ROOT),
        config_path="acestep-v15-turbo",
        device="auto",
        offload_to_cpu=False,
    )
    if not ok:
        raise RuntimeError(message)
    params = GenerationParams(
        task_type="text2music",
        thinking=False,
        use_cot_metas=False,
        use_cot_caption=False,
        use_cot_language=False,
        caption="Bright analog chamber electro swing with crisp hand percussion, warm upright bass, and a clear 120 BPM 4/4 pulse",
        lyrics="[Instrumental]",
        instrumental=True,
        bpm=120,
        keyscale="C major",
        timesignature="4",
        vocal_language="unknown",
        duration=10.0,
        inference_steps=8,
        guidance_scale=1.0,
        seed=1901,
        shift=1.0,
    )
    result = generate_music(
        handler,
        LLMHandler(),
        params=params,
        config=GenerationConfig(batch_size=1, use_random_seed=False, seeds=[1901], audio_format="wav"),
        save_dir=str(target.parent),
    )
    if not result.success or not result.audios:
        raise RuntimeError(result.status_message)
    source = Path(result.audios[0]["path"])
    shutil.copyfile(source, target)
    print(json.dumps({"operation": "ace_generate", "source": str(source), "target": str(target)}, sort_keys=True))


def adapt(target: Path, before: Path, reference: Path) -> None:
    handler = AceStepHandler()
    message, ok = handler.initialize_service(
        project_root=str(ROOT),
        config_path="acestep-v15-turbo",
        device="auto",
        offload_to_cpu=False,
    )
    if not ok:
        raise RuntimeError(message)
    params = GenerationParams(
        task_type="cover",
        thinking=False,
        use_cot_metas=False,
        use_cot_caption=False,
        use_cot_language=False,
        caption="Restyle toward soft neon synth jazz with mellow electric piano, brushed drums, and a relaxed 112 BPM feel while preserving the source structure",
        lyrics="[Instrumental]",
        instrumental=True,
        reference_audio=str(reference),
        src_audio=str(before),
        audio_cover_strength=0.2,
        inference_steps=8,
        guidance_scale=1.0,
        seed=3901,
        shift=1.0,
    )
    result = generate_music(
        handler,
        LLMHandler(),
        params=params,
        config=GenerationConfig(batch_size=1, use_random_seed=False, seeds=[3901], audio_format="wav"),
        save_dir=str(target.parent),
    )
    if not result.success or not result.audios:
        raise RuntimeError(result.status_message)
    source = Path(result.audios[0]["path"])
    shutil.copyfile(source, target)
    print(json.dumps({"operation": "ace_style_adapt", "source": str(source), "target": str(target)}, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="operation", required=True)
    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("target", type=Path)
    adapt_parser = subparsers.add_parser("adapt")
    adapt_parser.add_argument("target", type=Path)
    adapt_parser.add_argument("before", type=Path)
    adapt_parser.add_argument("reference", type=Path)
    args = parser.parse_args()
    if args.operation == "generate":
        generate(args.target.resolve())
    else:
        adapt(args.target.resolve(), args.before.resolve(), args.reference.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
