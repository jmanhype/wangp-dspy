#!/bin/bash
set -uo pipefail

ROOT=/home/straughter/Wan2GP
WORK=$ROOT/wd-9t9o
SETTINGS=$WORK/settings
LOGS=$WORK/logs
PYTHON=$ROOT/venv/bin/python

run_probe() {
  name=$1
  settings=$SETTINGS/$name.json
  out=$WORK/outputs/$name
  log=$LOGS/$name.render.log
  mkdir -p "$out"
  printf '%s\n' "$PYTHON" wgp.py --process "$settings" --profile 3 --attention auto --output-dir "$out" > "$LOGS/$name.argv.txt"
  cd "$ROOT"
  PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True \
    "$PYTHON" wgp.py --process "$settings" --profile 3 --attention auto --output-dir "$out" > "$log" 2>&1
  code=$?
  printf '%s\n' "$code" > "$LOGS/$name.exit"
  nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader > "$LOGS/$name.gpu-after.txt"
  printf 'name=%s exit=%s\n' "$name" "$code"
}

run_probe blend-probe
run_probe recast-probe
sha256sum "$ROOT/models/minimax_h3/minimax_h3_handler.py" "$ROOT/models/minimax_h3/pipeline.py" > "$WORK/boundary-source-hashes.txt"
{
  printf '%s\n' '--- FL2VA exposed guide choices and disabled outpaint control ---'
  grep -n -A18 -B2 'guide_custom_choices' "$ROOT/models/minimax_h3/minimax_h3_handler.py" | grep -E 'Generate without a Control Video|Use Control Video|Inject Frames|Reference Video|video_guide_outpainting|outpainting_quantize_margins' || true
  printf '%s\n' '--- non-Ref2VA reference rejection ---'
  grep -n -A2 -B2 'references require the Ref2VA checkpoint' "$ROOT/models/minimax_h3/pipeline.py" || true
} > "$WORK/boundary-code-evidence.txt"
