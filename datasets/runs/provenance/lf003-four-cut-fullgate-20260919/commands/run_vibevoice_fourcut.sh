#!/bin/bash
set -euo pipefail
ROOT=/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-rij6
ASSETS=$ROOT/assets/acceptance/lf003-v3
SUPPLY=$ROOT/datasets/runs/pull/lf003-four-cut-fullgate-20260919
export WANGP_ASSET_MAP="$ASSETS=/home/straughter/wangp-dspy-vibevoice-20260916/assets/acceptance/lf003-v3;$SUPPLY=/home/straughter/wangp-dspy-vibevoice-20260916/datasets/runs/pull/lf003-four-cut-fullgate-20260919"
cd "$ROOT"
exec /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m predict.vibevoice \
  "$SUPPLY/vibevoice-turns.json" \
  --remote-target 3090 \
  --host-python /home/straughter/vb7-venv/bin/python \
  --host-repo /home/straughter/wangp-dspy-vibevoice-20260916 \
  --host-model /home/straughter/models/VibeVoice-7B-hf \
  --report "$SUPPLY/vibevoice-report.json" \
  --pass-bar 0.8 \
  --seed-retries 2 \
  --remote-timeout 3600 \
  --remote-gpu-lease judge
