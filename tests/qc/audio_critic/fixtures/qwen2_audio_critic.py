#!/usr/bin/env python3
"""Qwen2-Audio Critique Script for SGFLIX Audio Factory."""

import argparse
import os
import sys
from pathlib import Path
import torch
import soundfile as sf
import json
import librosa
from transformers import Qwen2AudioForConditionalGeneration, AutoProcessor

def main():
    parser = argparse.ArgumentParser(description="Critique audio with Qwen2-Audio-7B-Instruct")
    parser.add_argument("--audio", required=True, help="Path to raw audio file")
    parser.add_argument("--reference-audio", type=str, default="", help="Path to original/reference audio file for comparison")
    parser.add_argument("--prompt", type=str, default="Analyze this audio track. Do the vocals sound on-beat at 130 BPM? Critique the flow, timing, and vocal clarity, then give a score from 0 to 40 based on its quality.", help="Prompt for Qwen2-Audio")
    parser.add_argument("--output-json", type=str, default="", help="Path to write critique result JSON")
    args = parser.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"Error: Audio file not found at {audio_path}", file=sys.stderr)
        return 1

    print(f"[INFO] Loading Qwen2-Audio processor and model...")
    model_id = "Qwen/Qwen2-Audio-7B-Instruct"
    
    try:
        processor = AutoProcessor.from_pretrained(model_id)
        model = Qwen2AudioForConditionalGeneration.from_pretrained(
            model_id, 
            torch_dtype=torch.bfloat16, 
            device_map="auto"
        )
    except Exception as e:
        print(f"Error loading model: {e}", file=sys.stderr)
        return 1

    print(f"[INFO] Loading audio file: {audio_path.name} ...")
    try:
        sr_target = processor.feature_extractor.sampling_rate
        audio, sr = librosa.load(str(audio_path), sr=sr_target)
        
        ref_audio = None
        if args.reference_audio:
            ref_path = Path(args.reference_audio)
            if ref_path.exists():
                print(f"[INFO] Loading reference audio file: {ref_path.name} ...")
                ref_audio, _ = librosa.load(str(ref_path), sr=sr_target)
            else:
                print(f"[WARNING] Reference audio not found at {ref_path}")
    except Exception as e:
        print(f"Error loading audio: {e}", file=sys.stderr)
        return 1

    print(f"[INFO] Preparing conversation and inputs...")
    if ref_audio is not None:
        conversation = [
            {"role": "user", "content": [
                {"type": "audio", "audio_url": str(Path(args.reference_audio))},
                {"type": "audio", "audio_url": str(audio_path)},
                {"type": "text", "text": args.prompt}
            ]}
        ]
        text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
        inputs = processor(text=text, audio=[ref_audio, audio], return_tensors="pt", padding=True)
    else:
        conversation = [
            {"role": "user", "content": [
                {"type": "audio", "audio_url": str(audio_path)},
                {"type": "text", "text": args.prompt}
            ]}
        ]
        text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
        inputs = processor(text=text, audio=audio, return_tensors="pt", padding=True)
    inputs = {k: v.to("cuda") for k, v in inputs.items()}

    print(f"[INFO] Generating auditory critique...")
    with torch.no_grad():
        generate_ids = model.generate(**inputs, max_new_tokens=512)
    
    generate_ids = [oid[len(i):] for oid, i in zip(generate_ids, inputs.get("input_ids", generate_ids))]
    response = processor.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

    print("\n" + "=" * 80)
    print("QWEN2-AUDIO AUDITORY CRITIQUE RESULTS")
    print("=" * 80)
    print(response)
    print("=" * 80 + "\n")

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps({"critique": response}, indent=2))
        print(f"[INFO] Critique written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
