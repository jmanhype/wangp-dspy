#!/bin/bash
set -euo pipefail
ROOT=/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-rij6
export WANGP_VISION_BACKEND=local
export WANGP_WHISPER_LOCAL_FIRST=0
export WANGP_ASSET_MAP="$ROOT/assets/acceptance/lf003-v3=/home/straughter/Wan2GP/lf003-four-cut-fullgate-20260919/assets/lf003-v3;$ROOT/datasets/runs/provenance=/home/straughter/Wan2GP/lf003-four-cut-fullgate-20260919/datasets/runs/provenance"
cd "$ROOT"
exec /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python scripts/run_jobs.py \
  --db datasets/lf003-four-cut-fullgate-20260919.jobs.db \
  --retry-failed
