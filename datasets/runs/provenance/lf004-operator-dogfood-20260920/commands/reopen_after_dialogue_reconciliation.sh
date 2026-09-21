#!/bin/bash
set -euo pipefail

ROOT=/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-42no
PROVENANCE="$ROOT/datasets/runs/provenance/lf004-operator-dogfood-20260920"
DB="$ROOT/datasets/lf004-operator-dogfood-20260920.jobs.db"

export WANGP_ASSET_MAP="$ROOT/datasets/content_briefs/lf004-operator-dogfood/plates=/home/straughter/Wan2GP/lf004-operator-dogfood-20260920/plates;$ROOT/datasets/runs/provenance=/home/straughter/Wan2GP/lf004-operator-dogfood-20260920/datasets/runs/provenance"

cd "$ROOT"

/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python - <<'PY'
from services.jobs.queue import JobQueue

queue = JobQueue("datasets/lf004-operator-dogfood-20260920.jobs.db")
try:
    failed = queue.list_state("failed")
    assert failed == ["job-1789937516351-1da5e2de"], failed
    jid = failed[0]
    queue.set_state(jid, "dead_letter")
    attempt_id = queue.reopen_dead_letter(
        jid,
        reason="runtime dialogue_text reconciled from approved canonical plan after repeated pre-whisper prompt-target mismatch",
    )
    print(f"reopened {jid} attempt={attempt_id}")
finally:
    queue.close()
PY

export WANGP_VISION_BACKEND=local
export WANGP_WHISPER_LOCAL_FIRST=0
export WANGP_QC_URL=http://localhost:8000/health

set -o pipefail
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python scripts/run_jobs.py \
  --db "$DB" \
  2>&1 | tee -a "$PROVENANCE/execution.log"
