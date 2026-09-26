#!/bin/bash
set -uo pipefail

ROOT=/home/straughter/Wan2GP
WORK=$ROOT/wd-isg9
SETTINGS=$WORK/settings
LOGS=$WORK/logs
PYTHON=$ROOT/venv/bin/python

mkdir -p "$WORK/outputs" "$LOGS"

snapshot_host() {
  label=$1
  file=$2
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
  snapshot_host "before" "$LOGS/$name.host-before.txt"
  printf '%s\n' "$PYTHON" wgp.py --process "$settings" --profile 3 --attention sdpa --output-dir "$out" > "$LOGS/$name.argv.txt"
  cd "$ROOT"
  PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True \
    "$PYTHON" wgp.py --process "$settings" --profile 3 --attention sdpa --output-dir "$out" > "$log" 2>&1
  code=$?
  printf '%s\n' "$code" > "$LOGS/$name.exit"
  newest=$(find "$out" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
  if test -n "$newest"; then
    cp "$newest" "$out/wd_isg9_$name.mp4"
    sha256sum "$out/wd_isg9_$name.mp4" > "$out/wd_isg9_$name.sha256"
    ffprobe -v error -show_streams -show_format -of json "$out/wd_isg9_$name.mp4" > "$out/wd_isg9_$name.ffprobe.json"
    printf 'source=%s\nfinal=%s\n' "$newest" "$out/wd_isg9_$name.mp4" > "$out/output-path.txt"
  fi
  snapshot_host "after" "$LOGS/$name.host-after.txt"
  printf 'name=%s exit=%s output=%s\n' "$name" "$code" "$newest" | tee -a "$LOGS/render-status.txt"
}

record_postprocess() {
  name=$1
  settings=$SETTINGS/$name.json
  out=$WORK/outputs/$name
  log=$LOGS/$name.render.log
  mkdir -p "$out"
  rm -f "$out"/*.mp4
  snapshot_host "before" "$LOGS/$name.host-before.txt"
  printf '%s\n' "$PYTHON" wgp.py --process "$settings" --output-dir "$out" > "$LOGS/$name.argv.txt"
  cd "$ROOT"
  PYTHONUNBUFFERED=1 "$PYTHON" wgp.py --process "$settings" --output-dir "$out" > "$log" 2>&1
  code=$?
  printf '%s\n' "$code" > "$LOGS/$name.exit"
  newest=$(find "$out" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
  if test -n "$newest"; then
    cp "$newest" "$out/wd_isg9_$name.mp4"
    sha256sum "$out/wd_isg9_$name.mp4" > "$out/wd_isg9_$name.sha256"
    ffprobe -v error -show_streams -show_format -of json "$out/wd_isg9_$name.mp4" > "$out/wd_isg9_$name.ffprobe.json"
    printf 'source=%s\nfinal=%s\n' "$newest" "$out/wd_isg9_$name.mp4" > "$out/output-path.txt"
  fi
  snapshot_host "after" "$LOGS/$name.host-after.txt"
  printf 'name=%s exit=%s output=%s\n' "$name" "$code" "$newest" | tee -a "$LOGS/render-status.txt"
}

rm -f "$LOGS/render-status.txt"
snapshot_host batch "$WORK/host-before.txt"
record_generation extend
record_generation retake
record_generation edit
record_generation repaint
record_postprocess upscale
snapshot_host batch "$WORK/host-after.txt"

find "$WORK/outputs" -type f -name 'wd_isg9_*.mp4' -print0 | sort -z | xargs -0 sha256sum > "$WORK/output-hashes.txt"
find "$WORK/outputs" -type f -name 'wd_isg9_*.mp4' -print0 | sort -z | xargs -0 du -b > "$WORK/output-sizes.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$WORK/completed-at.txt"

python3 - <<'PY'
import json
from pathlib import Path
root = Path('/home/straughter/Wan2GP/wd-isg9')
rows = []
for name in ('extend', 'retake', 'edit', 'repaint', 'upscale'):
    exit_path = root / 'logs' / f'{name}.exit'
    output = root / 'outputs' / name / f'wd_isg9_{name}.mp4'
    rows.append({
        'operation': name,
        'exit': int(exit_path.read_text().strip()) if exit_path.exists() else None,
        'output': str(output),
        'exists': output.is_file(),
        'bytes': output.stat().st_size if output.is_file() else 0,
    })
(root / 'render-summary.json').write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps(rows, indent=2))
PY

test -s "$WORK/outputs/extend/wd_isg9_extend.mp4"
test -s "$WORK/outputs/retake/wd_isg9_retake.mp4"
test -s "$WORK/outputs/edit/wd_isg9_edit.mp4"
test -s "$WORK/outputs/repaint/wd_isg9_repaint.mp4"
test -s "$WORK/outputs/upscale/wd_isg9_upscale.mp4"
