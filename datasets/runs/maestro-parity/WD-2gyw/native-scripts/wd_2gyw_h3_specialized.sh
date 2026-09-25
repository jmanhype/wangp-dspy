#!/bin/bash
set -euo pipefail
ROOT=/home/straughter/Wan2GP
OUT=$ROOT/outputs/wd-2gyw/h3-specialized
SETTINGS=$ROOT/wd_2gyw_h3_specialized.source.json
mkdir -p "$OUT"
cp /home/straughter/Wan2GP/wd_2gyw_h3_specialized.source.json "$SETTINGS"
ffmpeg -y -v error -i "$ROOT/outputs/wd-2gyw/h3-standard/wd_2gyw_h3_standard.mp4" -update 1 -frames:v 1 "$ROOT/outputs/wd-2gyw/h3-standard/wd_2gyw_h3_standard_first_frame.png"
cd "$ROOT"
find "$OUT" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort > "$OUT/before.txt"
PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True \
  ./venv/bin/python wgp.py --process "$SETTINGS" --profile 3 --attention auto \
  --output-dir "$OUT" > "$OUT/render.log" 2>&1
find "$OUT" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort > "$OUT/after.txt"
count=$(find "$OUT" -maxdepth 1 -type f -name '*.mp4' | wc -l)
test "$count" -ge 3
i=0
while IFS= read -r line; do
  i=$((i+1)); p=${line#* }; test -n "$p"; cp "$p" "$OUT/h3_specialized_${i}.mp4"; sha256sum "$OUT/h3_specialized_${i}.mp4";
done < <(find "$OUT" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort -nr | head -3 | tac)
for f in "$OUT"/h3_specialized_*.mp4; do ffprobe -v error -show_streams -show_format -of json "$f" > "$f.ffprobe.json"; done
sha256sum "$ROOT/outputs/wd-2gyw/h3-standard/wd_2gyw_h3_standard_first_frame.png" > "$OUT/reference-frame.sha256"
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits > "$OUT/gpu-after.txt"
