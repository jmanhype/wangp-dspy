#!/bin/bash
set -uo pipefail

SOURCE=/home/straughter/Wan2GP-story-WD-28i5
RUN=/home/straughter/wd-28i5-run
PY=/home/straughter/Wan2GP/venv/bin/python
LOG=$RUN/host-logs
OUT=$RUN/outputs/create
mkdir -p "$OUT" "$LOG"

snapshot() {
  {
    date -u +%Y-%m-%dT%H:%M:%SZ
    git -C "$SOURCE" rev-parse HEAD
    git -C "$SOURCE" status --porcelain=v1
    df -B1 "$RUN"
    nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
  } >"$1"
}

snapshot "$LOG/create.host-before.txt"
printf '%s\n' "$PY" wgp.py --process "$RUN/settings/create.json" --profile 3 --attention sdpa --output-dir "$OUT" >"$LOG/create.argv.txt"
(
  cd "$SOURCE"
  PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    timeout 2400 "$PY" wgp.py --process "$RUN/settings/create.json" --profile 3 --attention sdpa --output-dir "$OUT" >"$LOG/create.render.log" 2>&1
)
code=$?
printf '%s\n' "$code" >"$LOG/create.exit"
newest=$(find "$OUT" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
if test -n "$newest"; then
  cp "$newest" "$OUT/wd_28i5_create.mp4"
  sha256sum "$OUT/wd_28i5_create.mp4" >"$OUT/wd_28i5_create.sha256"
  ffprobe -v error -show_streams -show_format -of json "$OUT/wd_28i5_create.mp4" >"$OUT/wd_28i5_create.ffprobe.json"
  ffmpeg -nostdin -v error -y -i "$OUT/wd_28i5_create.mp4" -vf fps=3,scale=240:-1,tile=3x3 -frames:v 1 "$OUT/contact-sheet.jpg"
  ffmpeg -nostdin -v error -y -i "$OUT/wd_28i5_create.mp4" -update 1 -frames:v 1 "$OUT/first-frame.png"
  printf 'source=%s\nfinal=%s\n' "$newest" "$OUT/wd_28i5_create.mp4" >"$OUT/output-path.txt"
fi
snapshot "$LOG/create.host-after.txt"
git -C "$SOURCE" restore -- shared/gradio/hierarchy_selector/hierarchy_selector.pyi 2>/dev/null || true
git -C "$SOURCE" status --porcelain=v1 >"$LOG/create.source-final-status.txt"
printf 'create_exit=%s output=%s\n' "$code" "$newest"
test "$code" -eq 0
test -s "$OUT/wd_28i5_create.mp4"
