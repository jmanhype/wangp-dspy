#!/usr/bin/env bash
set -euo pipefail

ROOT=${ROOT:-$(git rev-parse --show-toplevel)}
BUNDLE="$ROOT/datasets/runs/maestro-parity/WD-bxhc"
cd "$BUNDLE"

run_plan() {
  local name=$1
  local verb=$2
  "$ROOT/.venv/bin/wgp" voice "$verb" \
    --request "planning/requests/$name.json" \
    --models planning/models.json \
    --db "planning/databases/$name.db" \
    --json > "planning/cli/$name.json"
  "$ROOT/.venv/bin/wgp" voice plan \
    --reconstruct --db "planning/databases/$name.db" \
    --json > "planning/cli/$name.reconstruct.json"
}

run_plan chatterbox-speech generate
run_plan vibevoice-speech generate
run_plan vibevoice-clone-one clone
run_plan vibevoice-clone-two clone

"$ROOT/.venv/bin/python" - <<'PY'
import json
from pathlib import Path
root = Path('planning/cli')
for path in sorted(root.glob('*.json')):
    payload = json.loads(path.read_text())
    if 'capability_status' in payload:
        print(f"{path.name}: status={payload['capability_status']} segments={payload['segment_count']} executable={payload['records'][0]['executable']}")
    else:
        print(f"{path.name}: all_match={payload['all_match']} hidden_mutation={payload['hidden_mutation']} records={len(payload['records'])}")
PY
