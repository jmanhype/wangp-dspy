#!/bin/bash
set -uo pipefail

test "$#" -eq 1
operation=$1
SOURCE=/home/straughter/Wan2GP-story-WD-m7xw
RUN=/home/straughter/wd-m7xw-run
PY=/home/straughter/Wan2GP/venv/bin/python
SETTINGS=$RUN/settings/$operation.json
OUT=$RUN/outputs/$operation
LOG=$RUN/host-logs-resumed
mkdir -p "$OUT" "$LOG"
test -s "$SETTINGS"
test "$(git -C "$SOURCE" rev-parse HEAD)" = faea82d15bf10b3479c42c0ea430892aae975870
test "$(git -C "$SOURCE" status --porcelain=v1)" = "?? ckpts"

snapshot() {
  label=$1
  file=$2
  {
    date -u +%Y-%m-%dT%H:%M:%SZ
    git -C "$SOURCE" rev-parse HEAD
    git -C "$SOURCE" status --porcelain=v1
    df -B1 "$RUN"
    nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
    cat /proc/net/dev
  } > "$file"
}

snapshot before "$LOG/$operation.host-before.txt"
printf '%s\n' "$PY" wgp.py --process "$SETTINGS" --profile 3 --attention sdpa --output-dir "$OUT" > "$LOG/$operation.argv.txt"
cd "$SOURCE" || exit 1
PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  timeout 1800 "$PY" wgp.py --process "$SETTINGS" --profile 3 --attention sdpa --output-dir "$OUT" \
  > "$LOG/$operation.render.log" 2>&1
code=$?
printf '%s\n' "$code" > "$LOG/$operation.exit"
newest=$(find "$OUT" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
if test -n "$newest"; then
  if test "$(readlink -f "$newest")" != "$(readlink -f "$OUT/wd_m7xw_$operation.mp4")"; then
    cp "$newest" "$OUT/wd_m7xw_$operation.mp4"
  fi
  sha256sum "$OUT/wd_m7xw_$operation.mp4" > "$OUT/wd_m7xw_$operation.sha256"
  ffprobe -v error -show_streams -show_format -of json "$OUT/wd_m7xw_$operation.mp4" > "$OUT/wd_m7xw_$operation.ffprobe.json"
  ffmpeg -nostdin -v error -y -i "$OUT/wd_m7xw_$operation.mp4" -vf "select=eq(n\,0)" -frames:v 1 "$OUT/first-frame.png"
  ffmpeg -nostdin -v error -y -i "$OUT/wd_m7xw_$operation.mp4" -vf "fps=6,scale=240:-1,tile=4x2" -frames:v 1 "$OUT/contact-sheet.jpg"
  printf 'source=%s\nfinal=%s\n' "$newest" "$OUT/wd_m7xw_$operation.mp4" > "$OUT/output-path.txt"
fi
snapshot after "$LOG/$operation.host-after.txt"
printf 'operation=%s exit=%s output=%s\n' "$operation" "$code" "$newest" | tee -a "$LOG/render-status.txt"
test "$code" -eq 0
test -s "$OUT/wd_m7xw_$operation.mp4"
