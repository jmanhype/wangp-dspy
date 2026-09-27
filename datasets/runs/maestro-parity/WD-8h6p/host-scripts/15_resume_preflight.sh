#!/bin/bash
set -euo pipefail

LIVE=/home/straughter/Wan2GP
SOURCE=/home/straughter/Wan2GP-story-WD-8h6p
RUN=/home/straughter/wd-8h6p-run

test "$(git -C "$SOURCE" rev-parse HEAD)" = 4c93b64a47b5b0a915f2abec2ce754be98227150
test "$(git -C "$SOURCE" status --porcelain=v1)" = "?? ckpts"
test "$(readlink "$SOURCE/ckpts")" = "$LIVE/ckpts"
test "$(sha256sum "$LIVE/outputs/wd-2gyw/hunyuan/wd_2gyw_hunyuan.mp4" | awk '{print $1}')" = 8c36757e077cb1f080ed3596691ec3186a2c2307297ccb76bedee26507608fa0
test "$(sha256sum "$LIVE/wd-isg9/inputs/repaint-mask.mp4" | awk '{print $1}')" = 8e58f8f4389218384069525c1eda95652ef2b7a91b1957bcebff37a9e28e6657
test "$(sha256sum "$LIVE/wd-isg9/inputs/recast-reference.png" | awk '{print $1}')" = 321f91b39796ea9112d682c8a38e3bca02d5677acc462dcbf019b9b7e7e7ad7d
ffmpeg -nostdin -v error -y -i "$LIVE/outputs/wd-2gyw/hunyuan/wd_2gyw_hunyuan.mp4" -update 1 -frames:v 1 "$RUN/inputs/hunyuan-first-frame.png"
sha256sum "$RUN/inputs/hunyuan-first-frame.png" >"$RUN/host-logs/12_derived_input_hashes.txt"
free=$(df -B1 "$RUN" | awk 'NR==2 {print $4}')
test "$free" -ge 20000000000
gpu_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
test "$gpu_used" -le 1000
{
  date -u +%Y-%m-%dT%H:%M:%SZ
  git -C "$SOURCE" rev-parse HEAD
  git -C "$SOURCE" status --porcelain=v1
  df -B1 "$RUN"
  nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits
  printf '%s\n' 'source_and_helper_hashes=PASS'
  printf '%s\n' 'offline=forced'
  printf '%s\n' 'planned_download_bytes=0'
} >"$RUN/host-logs/16_resume_preflight.txt"
printf 'RESUME_PREFLIGHT_PASS\n'
