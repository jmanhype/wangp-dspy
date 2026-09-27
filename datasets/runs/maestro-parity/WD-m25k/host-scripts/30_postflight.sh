#!/bin/bash
set -euo pipefail

LIVE=/home/straughter/Wan2GP
SOURCE=/home/straughter/Wan2GP-story-WD-m25k
RUN=/home/straughter/wd-m25k-run

{
  date -u +%Y-%m-%dT%H:%M:%SZ
  hostname
  git -C "$SOURCE" rev-parse HEAD
  git -C "$SOURCE" status --porcelain=v1
  git -C "$LIVE" rev-parse HEAD
  git -C "$LIVE" status --porcelain=v1 | sha256sum
  df -B1 "$RUN"
  nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits
  nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
} >"$RUN/host-logs/90_final_postflight.txt"

{
  sha256sum "$LIVE/ckpts/MiniMax-H3-FL2VA-pruned_rank8_int8_convrot.safetensors"
  sha256sum "$LIVE/ckpts/MiniMax-H3-video_vae_fp16.safetensors"
  sha256sum "$LIVE/ckpts/MiniMax-H3-audio_vae_fp32.safetensors"
  sha256sum "$LIVE/ckpts/Qwen3-VL-32B-Instruct/Qwen3-VL-32B-Instruct-layer50_quanto_bf16_int8.safetensors"
  sha256sum "$LIVE/outputs/wd-2gyw/h3-kfi-retry/wd_2gyw_h3_kfi_frames_injection.mp4"
  sha256sum "$LIVE/outputs/wd-2gyw/h3-specialized/wd_2gyw_h3_audio_refinement.mp4"
  sha256sum "$LIVE/wd-isg9/inputs/repaint-mask.mp4"
  sha256sum "$LIVE/wd-isg9/inputs/recast-reference.png"
} >"$RUN/host-logs/91_asset_hashes_after.txt"

find "$RUN" -type f -printf '%s %p\n' | sort >"$RUN/host-logs/92_run_inventory.txt"
du -sb "$RUN" >"$RUN/host-logs/93_run_size.txt"
printf 'actual_download_bytes=0\noffline_mode=forced\n' >"$RUN/host-logs/94_download_accounting.txt"
