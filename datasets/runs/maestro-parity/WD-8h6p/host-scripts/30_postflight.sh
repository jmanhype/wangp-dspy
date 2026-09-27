#!/bin/bash
set -euo pipefail

LIVE=/home/straughter/Wan2GP
SOURCE=/home/straughter/Wan2GP-story-WD-8h6p
RUN=/home/straughter/wd-8h6p-run

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
  sha256sum "$LIVE/ckpts/hy1.5_t2v_480p_lightx2v_4step_quanto_int8_bf16.safetensors"
  sha256sum "$LIVE/ckpts/hunyuan_video_1_5_VAE_fp32.safetensors"
  sha256sum "$LIVE/ckpts/hunyuan_video_1_5_VAE.json"
  sha256sum "$LIVE/ckpts/siglip_vision_model/config.json"
  sha256sum "$LIVE/ckpts/siglip_vision_model/model.safetensors"
  sha256sum "$LIVE/ckpts/siglip_vision_model/preprocessor_config.json"
  sha256sum "$LIVE/outputs/wd-2gyw/hunyuan/wd_2gyw_hunyuan.mp4"
  sha256sum "$LIVE/wd-isg9/inputs/repaint-mask.mp4"
  sha256sum "$LIVE/wd-isg9/inputs/recast-reference.png"
} >"$RUN/host-logs/91_asset_hashes_after.txt"
find "$RUN" -type f -printf '%s %p\n' | sort >"$RUN/host-logs/92_run_inventory.txt"
du -sb "$RUN" >"$RUN/host-logs/93_run_size.txt"
printf 'actual_download_bytes=0\noffline_mode=forced\n' >"$RUN/host-logs/94_download_accounting.txt"
