#!/bin/bash
set -euo pipefail

ROOT=/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-42no
PROVENANCE="$ROOT/datasets/runs/provenance/lf004-operator-dogfood-20260920"
BRIEF="$ROOT/datasets/content_briefs/lf004-operator-dogfood"
DB="$ROOT/datasets/lf004-operator-dogfood-20260920.jobs.db"

export WANGP_VISION_BACKEND=local
export WANGP_WHISPER_LOCAL_FIRST=0
export WANGP_QC_URL=http://localhost:8000/health
export WANGP_ASSET_MAP="$BRIEF/plates=/home/straughter/Wan2GP/lf004-operator-dogfood-20260920/plates;$ROOT/datasets/runs/provenance=/home/straughter/Wan2GP/lf004-operator-dogfood-20260920/datasets/runs/provenance"

cd "$ROOT"
mkdir -p "$PROVENANCE"

set -o pipefail
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python scripts/run_film.py \
  --script "$BRIEF/run/script.txt" \
  --plates "$BRIEF/plates" \
  --characters \
    'Tess:S1:a sleepless young observatory astronomer with short dark hair, navy jacket, silver star pin, standing on the LEFT inside a glass-dome control room' \
    'Rho:S2:a pragmatic bearded station caretaker with red knit cap and olive work jacket, standing on the RIGHT inside the same glass-dome observatory control room' \
  --db "$DB" \
  --duration-s 4.458333333333333 \
  --duration-s 4.458333333333333 \
  --duration-s 4.458333333333333 \
  --duration-s 4.458333333333333 \
  --audio "$ROOT/datasets/runs/provenance/lf003-vibevoice-audition-20260917/audio/tess.prepared.wav" \
  --audio "$ROOT/datasets/runs/provenance/lf003-vibevoice-rho-strong-20260918/audio/rho.prepared.wav" \
  --audio "$ROOT/datasets/runs/provenance/lf003-four-cut-fullgate-20260919/audio/tess-cut3.prepared.wav" \
  --audio "$ROOT/datasets/runs/provenance/lf003-four-cut-fullgate-20260919/audio/rho-cut4.prepared.wav" \
  2>&1 | tee "$PROVENANCE/execution.log"
