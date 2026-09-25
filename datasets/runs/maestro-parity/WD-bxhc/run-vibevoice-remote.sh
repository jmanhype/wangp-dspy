#!/usr/bin/env bash
set -euo pipefail

ROOT=${ROOT:-$(git rev-parse --show-toplevel)}
BUNDLE="$ROOT/datasets/runs/maestro-parity/WD-bxhc"
export WANGP_ASSET_MAP="$BUNDLE=/home/straughter/wangp-dspy-vibevoice-20260916/datasets/runs/maestro-parity/WD-bxhc"
cd "$ROOT"

exec "$ROOT/.venv/bin/python" -m predict.vibevoice "$BUNDLE/vibevoice-turns.json" \
  --remote-target 3090 \
  --host-python /home/straughter/vb7-venv/bin/python \
  --host-repo /home/straughter/wangp-dspy-vibevoice-20260916 \
  --host-model /mnt/bulk/straughter/models/VibeVoice-7B-hf \
  --report "$BUNDLE/vibevoice-report.json" \
  --pass-bar 0.8 \
  --seed-retries 2 \
  --remote-timeout 2400 \
  --remote-gpu-lease none
