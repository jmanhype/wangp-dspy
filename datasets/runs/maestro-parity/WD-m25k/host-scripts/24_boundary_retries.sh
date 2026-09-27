#!/bin/bash
set -uo pipefail

SOURCE=/home/straughter/Wan2GP-story-WD-m25k
RUN=/home/straughter/wd-m25k-run
PY=/home/straughter/Wan2GP/venv/bin/python
LOG=$RUN/host-logs

for name in kfi-create-retry-probe kfi-blend-retry-probe kfi-outpaint-retry-probe; do
  out=$RUN/boundaries/$name
  mkdir -p "$out"
  printf '%s\n' "$PY" wgp.py --process "$RUN/settings/$name.json" --profile 3 --attention sdpa --output-dir "$out" >"$LOG/$name.argv.txt"
  (
    cd "$SOURCE"
    PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
      timeout 300 "$PY" wgp.py --process "$RUN/settings/$name.json" --profile 3 --attention sdpa --output-dir "$out" >"$LOG/$name.render.log" 2>&1
  )
  code=$?
  printf '%s\n' "$code" >"$LOG/$name.exit"
  find "$out" -maxdepth 1 -type f -printf '%s %p\n' | sort >"$LOG/$name.output-inventory.txt"
  printf 'boundary_retry=%s exit=%s\n' "$name" "$code" | tee -a "$LOG/render-status.txt"
done
