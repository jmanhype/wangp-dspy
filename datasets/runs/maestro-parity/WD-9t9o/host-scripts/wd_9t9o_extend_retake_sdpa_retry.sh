#!/bin/bash
set -uo pipefail
ROOT=/home/straughter/Wan2GP
WORK=$ROOT/wd-9t9o
PYTHON=$ROOT/venv/bin/python
run_one() {
  name=$1
  out=$WORK/outputs/$name-sdpa-retry
  mkdir -p "$out"
  cd "$ROOT"
  PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True \
    "$PYTHON" wgp.py --process "$WORK/settings/$name.json" --profile 3 --attention sdpa --output-dir "$out" > "$WORK/logs/$name-sdpa-retry.render.log" 2>&1
  code=$?
  printf '%s\n' "$code" > "$WORK/logs/$name-sdpa-retry.exit"
  newest=$(find "$out" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
  if test -n "$newest"; then
    cp "$newest" "$out/wd_9t9o_${name}.mp4"
    sha256sum "$out/wd_9t9o_${name}.mp4" > "$out/wd_9t9o_${name}.sha256"
    ffprobe -v error -show_streams -show_format -of json "$out/wd_9t9o_${name}.mp4" > "$out/wd_9t9o_${name}.ffprobe.json"
  fi
  printf 'name=%s exit=%s output=%s\n' "$name" "$code" "$newest"
}
run_one extend
run_one retake
