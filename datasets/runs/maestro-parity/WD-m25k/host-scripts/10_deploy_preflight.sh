#!/bin/bash
set -euo pipefail

LIVE=/home/straughter/Wan2GP
SOURCE=/home/straughter/Wan2GP-story-WD-m25k
RUN=/home/straughter/wd-m25k-run
PY=$LIVE/venv/bin/python

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
  path=$1
  expected=$2
  actual=$(sha256sum "$path" | awk '{print $1}')
  test "$actual" = "$expected"
  printf '%s  %s\n' "$actual" "$path"
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
  check_hash "$LIVE/ckpts/MiniMax-H3-FL2VA-pruned_rank8_int8_convrot.safetensors" 30ff400f974b11a1ef13d216c5d9f6439a9c10322a3988b0374a39672ce286f0
  check_hash "$LIVE/ckpts/MiniMax-H3-video_vae_fp16.safetensors" 455010492bb59a9cc7b8f1ee23905b22a10079f89490adbf820a1728efcaea6b
  check_hash "$LIVE/ckpts/MiniMax-H3-audio_vae_fp32.safetensors" 37dddc2f3e6d5d5139d823d5ea283bbf304dadcb885b1ccda818aa13dade5ea2
  check_hash "$LIVE/ckpts/Qwen3-VL-32B-Instruct/Qwen3-VL-32B-Instruct-layer50_quanto_bf16_int8.safetensors" 4df8fc5237746b3b058745d6ec8fe1e54a9721bdc663d35d2d1806952672f301
  check_hash "$LIVE/outputs/wd-2gyw/h3-kfi-retry/wd_2gyw_h3_kfi_frames_injection.mp4" b75cca624728675d5de5851098de0b0227f86384f29785348262dcb4bc4efb86
  check_hash "$LIVE/outputs/wd-2gyw/h3-specialized/wd_2gyw_h3_audio_refinement.mp4" 9fd0ab632a7b66d9be911cb86a20b746a15bb6557e2300e47a80993524d2f0d0
  check_hash "$LIVE/wd-isg9/inputs/repaint-mask.mp4" 8e58f8f4389218384069525c1eda95652ef2b7a91b1957bcebff37a9e28e6657
  check_hash "$LIVE/wd-isg9/inputs/recast-reference.png" 321f91b39796ea9112d682c8a38e3bca02d5677acc462dcbf019b9b7e7e7ad7d
} >"$RUN/host-logs/11_asset_hashes_before.txt"

ffmpeg -nostdin -v error -y -i "$LIVE/outputs/wd-2gyw/h3-kfi-retry/wd_2gyw_h3_kfi_frames_injection.mp4" -update 1 -frames:v 1 "$RUN/inputs/kfi-first-frame.png"
ffmpeg -nostdin -v error -y -i "$LIVE/outputs/wd-2gyw/h3-specialized/wd_2gyw_h3_audio_refinement.mp4" -update 1 -frames:v 1 "$RUN/inputs/audio-first-frame.png"
sha256sum "$RUN/inputs/kfi-first-frame.png" "$RUN/inputs/audio-first-frame.png" >"$RUN/host-logs/12_derived_input_hashes.txt"

free=$(df -B1 "$RUN" | awk 'NR==2 {print $4}')
test "$free" -ge 20000000000
gpu_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
test "$gpu_used" -le 1000
"$PY" -m pip check >"$RUN/host-logs/13_python_pip_check.txt" 2>&1
printf 'offline=forced\nplanned_download_bytes=0\n' >"$RUN/host-logs/14_download_boundary.txt"
