#!/bin/bash
set -euo pipefail
ROOT=/home/straughter/Wan2GP
OUT=$ROOT/outputs/wd-2gyw/h3-kfi-retry
SETTINGS=$ROOT/wd_2gyw_h3_kfi_retry.source.json
mkdir -p "$OUT"
test -s "$SETTINGS"
cd "$ROOT"
PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True \
  ./venv/bin/python wgp.py --process "$SETTINGS" --profile 3 --attention sdpa \
  --output-dir "$OUT" > "$OUT/render.log" 2>&1
newest=$(find "$OUT" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
test -n "$newest"
cp "$newest" "$OUT/wd_2gyw_h3_kfi_frames_injection.mp4"
sha256sum "$OUT/wd_2gyw_h3_kfi_frames_injection.mp4" > "$OUT/wd_2gyw_h3_kfi_frames_injection.sha256"
ffprobe -v error -show_streams -show_format -of json "$OUT/wd_2gyw_h3_kfi_frames_injection.mp4" > "$OUT/ffprobe.json"
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits > "$OUT/gpu-after.txt"
printf 'source=%s\nfinal=%s\n' "$newest" "$OUT/wd_2gyw_h3_kfi_frames_injection.mp4" > "$OUT/output-path.txt"
