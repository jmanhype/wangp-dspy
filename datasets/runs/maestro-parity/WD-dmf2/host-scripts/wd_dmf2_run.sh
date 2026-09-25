#!/usr/bin/env bash
set -Eeuo pipefail

lane=/home/straughter/Wan2GP/wd-dmf2
python=/home/straughter/Wan2GP/venv/bin/python
mkdir -p "$lane"

"$python" "$lane/host-scripts/wd_dmf2_preflight.py" \
  > "$lane/host-preflight.json"
"$python" "$lane/host-scripts/wd_dmf2_compose.py" "$lane" \
  > "$lane/composition.stdout" 2> "$lane/composition.stderr"
cd "$lane/repo"
PYTHONPATH="$lane/repo" "$python" "$lane/host-scripts/wd_dmf2_qc.py" "$lane" \
  > "$lane/qc.stdout" 2> "$lane/qc.stderr"
"$python" "$lane/host-scripts/wd_dmf2_preflight.py" \
  > "$lane/host-final-state.json"
