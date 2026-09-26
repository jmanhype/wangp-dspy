#!/bin/bash
set -uo pipefail

ROOT=/home/straughter/Wan2GP
WORK=$ROOT/wd-9t9o
SETTINGS=$WORK/settings
LOGS=$WORK/logs
PYTHON=$ROOT/venv/bin/python

snapshot_host() {
  file=$1
  {
    date -u +%Y-%m-%dT%H:%M:%SZ
    df -B1 "$ROOT"
    nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
    pgrep -af 'wgp.py --process' || true
  } > "$file"
}

record_generation() {
  name=$1
  settings=$SETTINGS/$name.json
  out=$WORK/outputs/$name
  log=$LOGS/$name.render.log
  mkdir -p "$out"
  rm -f "$out"/*.mp4
  snapshot_host "$LOGS/$name.host-before.txt"
  printf '%s\n' "$PYTHON" wgp.py --process "$settings" --profile 3 --attention auto --output-dir "$out" > "$LOGS/$name.argv.txt"
  cd "$ROOT"
  PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True \
    "$PYTHON" wgp.py --process "$settings" --profile 3 --attention auto --output-dir "$out" > "$log" 2>&1
  code=$?
  printf '%s\n' "$code" > "$LOGS/$name.exit"
  newest=$(find "$out" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
  if test -n "$newest"; then
    cp "$newest" "$out/wd_9t9o_$name.mp4"
    sha256sum "$out/wd_9t9o_$name.mp4" > "$out/wd_9t9o_$name.sha256"
    ffprobe -v error -show_streams -show_format -of json "$out/wd_9t9o_$name.mp4" > "$out/wd_9t9o_$name.ffprobe.json"
    printf 'source=%s\nfinal=%s\n' "$newest" "$out/wd_9t9o_$name.mp4" > "$out/output-path.txt"
  fi
  snapshot_host "$LOGS/$name.host-after.txt"
  printf 'name=%s exit=%s output=%s\n' "$name" "$code" "$newest" | tee -a "$LOGS/render-status.txt"
}

record_postprocess() {
  name=$1
  settings=$SETTINGS/$name.json
  out=$WORK/outputs/$name
  log=$LOGS/$name.render.log
  mkdir -p "$out"
  rm -f "$out"/*.mp4
  snapshot_host "$LOGS/$name.host-before.txt"
  printf '%s\n' "$PYTHON" wgp.py --process "$settings" --output-dir "$out" > "$LOGS/$name.argv.txt"
  cd "$ROOT"
  PYTHONUNBUFFERED=1 "$PYTHON" wgp.py --process "$settings" --output-dir "$out" > "$log" 2>&1
  code=$?
  printf '%s\n' "$code" > "$LOGS/$name.exit"
  newest=$(find "$out" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
  if test -n "$newest"; then
    cp "$newest" "$out/wd_9t9o_$name.mp4"
    sha256sum "$out/wd_9t9o_$name.mp4" > "$out/wd_9t9o_$name.sha256"
    ffprobe -v error -show_streams -show_format -of json "$out/wd_9t9o_$name.mp4" > "$out/wd_9t9o_$name.ffprobe.json"
    printf 'source=%s\nfinal=%s\n' "$newest" "$out/wd_9t9o_$name.mp4" > "$out/output-path.txt"
  fi
  snapshot_host "$LOGS/$name.host-after.txt"
  printf 'name=%s exit=%s output=%s\n' "$name" "$code" "$newest" | tee -a "$LOGS/render-status.txt"
}

rm -f "$LOGS/render-status.txt"
snapshot_host "$WORK/host-before.txt"
record_generation extend
record_generation retake
record_generation edit
record_generation repaint
record_postprocess upscale
snapshot_host "$WORK/host-after.txt"

find "$WORK/outputs" -type f -name 'wd_9t9o_*.mp4' -print0 | sort -z | xargs -0 sha256sum > "$WORK/output-hashes.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$WORK/completed-at.txt"
for name in edit repaint; do grep -q 'Sol-Attn enabled' "$LOGS/$name.render.log" || exit 1; done
for name in extend retake; do test "$(cat "$LOGS/$name.exit")" = 1 || exit 1; done
test -s "$WORK/outputs/edit/wd_9t9o_edit.mp4"
test -s "$WORK/outputs/repaint/wd_9t9o_repaint.mp4"
test -s "$WORK/outputs/upscale/wd_9t9o_upscale.mp4"
