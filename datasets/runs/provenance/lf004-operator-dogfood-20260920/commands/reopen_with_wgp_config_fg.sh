#!/bin/bash
set -euo pipefail

ROOT=/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-42no
PROVENANCE="$ROOT/datasets/runs/provenance/lf004-operator-dogfood-20260920"
DB="$ROOT/datasets/lf004-operator-dogfood-20260920.jobs.db"
REMOTE_SETTINGS=/home/straughter/Wan2GP/wgp_config.json
BACKUP="$PROVENANCE/wgp-config.before.json"
MODE_RECORD="$PROVENANCE/wgp-config-prompt-mode-reconciliation.json"
RESTORED=0

restore_settings() {
  if [[ "$RESTORED" -eq 0 ]]; then
    scp -q "3090:$REMOTE_SETTINGS" "$BACKUP.after-render.json"
    scp -q "$BACKUP" "3090:$REMOTE_SETTINGS"
    RESTORED=1
  fi
}
trap restore_settings EXIT INT TERM

export WANGP_ASSET_MAP="$ROOT/datasets/content_briefs/lf004-operator-dogfood/plates=/home/straughter/Wan2GP/lf004-operator-dogfood-20260920/plates;$ROOT/datasets/runs/provenance=/home/straughter/Wan2GP/lf004-operator-dogfood-20260920/datasets/runs/provenance"

cd "$ROOT"

/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python - <<'PY'
from services.jobs.queue import JobQueue
queue=JobQueue("datasets/lf004-operator-dogfood-20260920.jobs.db")
try:
 dead=queue.list_state("dead_letter")
 assert dead == ["job-1789937516351-1da5e2de"], dead
 attempt=queue.reopen_dead_letter(dead[0], reason="set Wan2GP process config FG for one approved single-prompt execution")
 print("reopened",dead[0],"attempt",attempt)
finally:
 queue.close()
PY

scp -q "3090:$REMOTE_SETTINGS" "$BACKUP"
before_sha=$(shasum -a 256 "$BACKUP" | awk '{print $1}')
ssh -o BatchMode=yes 3090 "python3 - <<'PY'
import json
from pathlib import Path
p=Path('/home/straughter/Wan2GP/wgp_config.json')
d=json.loads(p.read_text())
old=d.get('multi_prompts_gen_type')
d['multi_prompts_gen_type']='FG'
t=p.with_name('wgp_config.lf004-tmp.json')
t.write_text(json.dumps(d,indent=4)+'\\n')
t.replace(p)
print('prompt_mode',old,'->FG')
PY"

export WANGP_VISION_BACKEND=local
export WANGP_WHISPER_LOCAL_FIRST=0
export WANGP_QC_URL=http://localhost:8000/health

set -o pipefail
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python scripts/run_jobs.py \
  --db "$DB" \
  2>&1 | tee -a "$PROVENANCE/execution.log"

restore_settings
after_sha=$(ssh -o BatchMode=yes 3090 "sha256sum $REMOTE_SETTINGS" | awk '{print $1}')
printf '%s\n%s\n' "$before_sha" "$after_sha" > "$PROVENANCE/wgp-config-sha-transition.txt"
cat "$PROVENANCE/wgp-config-sha-transition.txt"
