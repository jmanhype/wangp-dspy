#!/usr/bin/env bash
set -euo pipefail
ROOT=/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-cpow
BUNDLE=$ROOT/datasets/runs/maestro-parity/WD-cpow
export WANGP_ASSET_MAP="$BUNDLE=/home/straughter/wangp-dspy-vibevoice-20260916/datasets/runs/maestro-parity/WD-cpow"
cd "$ROOT"
exec "$ROOT/.venv/bin/python" -m predict.vibevoice "$BUNDLE/planning/vibevoice-turns.json" \
  --remote-target 3090 \
  --host-python /home/straughter/vb7-venv/bin/python \
  --host-repo /home/straughter/wangp-dspy-vibevoice-20260916 \
  --host-model /mnt/bulk/straughter/models/VibeVoice-7B-hf \
  --report "$BUNDLE/vibevoice-report.json" \
  --pass-bar 0.8 \
  --seed-retries 2 \
  --remote-timeout 1800 \
  --remote-gpu-lease judge
