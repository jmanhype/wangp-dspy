#!/bin/bash
set -euo pipefail

LIVE=/home/straughter/Wan2GP
SOURCE=/home/straughter/Wan2GP-story-WD-8h6p
RUN=/home/straughter/wd-8h6p-run

test "$(hostname)" = straughter-Z690-Steel-Legend
test -d "$LIVE"
test ! -e "$SOURCE"
test -d "$RUN/settings"
test -z "$(find "$RUN" -mindepth 1 -maxdepth 1 ! -name settings -print -quit)"
test "$(git -C "$LIVE" rev-parse HEAD)" = 4c93b64a47b5b0a915f2abec2ce754be98227150

mkdir -p "$RUN/host-logs" "$RUN/inputs"
git -C "$LIVE" worktree add --detach "$SOURCE" 4c93b64a47b5b0a915f2abec2ce754be98227150 >"$RUN/host-logs/10_worktree_deploy.txt" 2>&1
ln -s "$LIVE/ckpts" "$SOURCE/ckpts"

check_hash() {
  actual=$(sha256sum "$1" | awk '{print $1}')
  test "$actual" = "$2"
  printf '%s  %s\n' "$actual" "$1"
}

{
  date -u +%Y-%m-%dT%H:%M:%SZ
  hostname
  git -C "$SOURCE" rev-parse HEAD
  git -C "$SOURCE" status --porcelain=v1
  readlink "$SOURCE/ckpts"
  df -B1 "$RUN"
  nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits
  nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
} >"$RUN/host-logs/00_host_before.txt"

{
  check_hash "$LIVE/ckpts/hy1.5_t2v_480p_lightx2v_4step_quanto_int8_bf16.safetensors" b045f314ae1ef2fb50de8efd7aa3fbf67526ec12ce59537ec9827bd417b09b77
  check_hash "$LIVE/ckpts/hunyuan_video_1_5_VAE_fp32.safetensors" 2609ed7033c052fdf164afcac71e8a7c82afccdbb001d673444a72f194fbb918
  check_hash "$LIVE/ckpts/hunyuan_video_1_5_VAE.json" 899e63dae033b2fa14291cefbe6e1736741d816991456e96d4d497918dacf8af
  check_hash "$LIVE/ckpts/siglip_vision_model/config.json" b626aa9623e88440ce20623debc3f0d85e4ee61f38846deca16738784b8ac4e2
  check_hash "$LIVE/ckpts/siglip_vision_model/model.safetensors" d769e3a32a6a9bac72d4d93b989e44491f71b50f02bfa14cd9187758d4a68ff1
  check_hash "$LIVE/ckpts/siglip_vision_model/preprocessor_config.json" ec1f371074fb4867ea1c654e00bc5ea99d706f409aaebf8dc614d67c0735aff8
  check_hash "$LIVE/outputs/wd-2gyw/hunyuan/wd_2gyw_hunyuan.mp4" 8c36757e077cb1f080ed3596691ec3186a2c2307297ccb76bedee26507608fa0
  check_hash "$LIVE/wd-isg9/inputs/repaint-mask.mp4" 8e58f8f4389218384069525c1eda95652ef2b7a91b1957bcebff37a9e28e6657
  check_hash "$LIVE/wd-isg9/inputs/recast-reference.png" 321f91b39796ea9112d682c8a38e3bca02d5677acc462dcbf019b9b7e7e7ad7d
} >"$RUN/host-logs/11_asset_hashes_before.txt"

ffmpeg -nostdin -v error -y -i "$LIVE/outputs/wd-2gyw/hunyuan/wd_2gyw_hunyuan.mp4" -update 1 -frames:v 1 "$RUN/inputs/hunyuan-first-frame.png"
sha256sum "$RUN/inputs/hunyuan-first-frame.png" >"$RUN/host-logs/12_derived_input_hashes.txt"
free=$(df -B1 "$RUN" | awk 'NR==2 {print $4}')
test "$free" -ge 20000000000
gpu_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
test "$gpu_used" -le 1000
printf 'offline=forced\nplanned_download_bytes=0\n' >"$RUN/host-logs/13_download_boundary.txt"
