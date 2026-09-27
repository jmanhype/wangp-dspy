#!/bin/bash
set -uo pipefail

SOURCE=/home/straughter/Wan2GP-story-WD-ycjg
RUN=/home/straughter/wd-ycjg-run
PY=/home/straughter/Wan2GP/venv/bin/python
LOG=$RUN/host-logs
OUT=$RUN/boundaries/blend-retry
mkdir -p "$OUT"

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

record_output() {
  src=$(find "$OUT" -maxdepth 1 -type f -name '*seed3508*.mp4' -print -quit)
  if test -n "$src"; then
    out=$RUN/outputs/blend
    mkdir -p "$out"
    cp "$src" "$out/wd_ycjg_blend.mp4"
    sha256sum "$out/wd_ycjg_blend.mp4" >"$out/wd_ycjg_blend.sha256"
    ffprobe -v error -show_streams -show_format -of json "$out/wd_ycjg_blend.mp4" >"$out/wd_ycjg_blend.ffprobe.json"
    ffmpeg -nostdin -v error -y -i "$out/wd_ycjg_blend.mp4" -vf fps=3,scale=240:-1,tile=3x3 -frames:v 1 "$out/contact-sheet.jpg"
    ffmpeg -nostdin -v error -y -i "$out/wd_ycjg_blend.mp4" -update 1 -frames:v 1 "$out/first-frame.png"
    printf 'source=%s\nfinal=%s\n' "$src" "$out/wd_ycjg_blend.mp4" >"$out/output-path.txt"
  fi
  printf 'blend_retry_output=%s\n' "$src"
}

snapshot "$LOG/blend-retry.host-before.txt"
printf '%s\n' "$PY" wgp.py --process "$RUN/settings/blend-retry.json" --profile 3 --attention sdpa --output-dir "$OUT" >"$LOG/blend-retry.argv.txt"
(
  cd "$SOURCE"
  PYTHONPATH="$RUN/python-deps/packages:$SOURCE" PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True \
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    timeout 1800 "$PY" wgp.py --process "$RUN/settings/blend-retry.json" --profile 3 --attention sdpa --output-dir "$OUT" >"$LOG/blend-retry.render.log" 2>&1
)
code=$?
printf '%s\n' "$code" >"$LOG/blend-retry.exit"
find "$OUT" -maxdepth 1 -type f -printf '%s %p\n' | sort >"$LOG/blend-retry.output-inventory.txt"
record_output
snapshot "$LOG/blend-retry.host-after.txt"
git -C "$SOURCE" restore -- shared/gradio/hierarchy_selector/hierarchy_selector.pyi 2>/dev/null || true
git -C "$SOURCE" status --porcelain=v1 >"$LOG/blend-retry.source-final-status.txt"
printf 'blend_retry_exit=%s\n' "$code"
test "$code" -eq 0
