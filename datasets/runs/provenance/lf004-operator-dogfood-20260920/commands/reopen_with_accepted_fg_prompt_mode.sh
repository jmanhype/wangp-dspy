#!/bin/bash
set -euo pipefail

ROOT=/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-42no
PROVENANCE="$ROOT/datasets/runs/provenance/lf004-operator-dogfood-20260920"
DB="$ROOT/datasets/lf004-operator-dogfood-20260920.jobs.db"
REMOTE_SETTINGS=/home/straughter/Wan2GP/models/_settings.json
BACKUP="$PROVENANCE/wan2gp-models-settings.before.json"
MODE_RECORD="$PROVENANCE/prompt-mode-reconciliation.json"
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

queue = JobQueue("datasets/lf004-operator-dogfood-20260920.jobs.db")
try:
    dead_letter = queue.list_state("dead_letter")
    assert dead_letter == ["job-1789937516351-1da5e2de"], dead_letter
    attempt_id = queue.reopen_dead_letter(
        dead_letter[0],
        reason="restore accepted Wan2GP FG single-prompt runtime mode while preserving approved prompt bytes",
    )
    print(f"reopened {dead_letter[0]} attempt={attempt_id}")
finally:
    queue.close()
PY

scp -q "3090:$REMOTE_SETTINGS" "$BACKUP"
before_sha=$(shasum -a 256 "$BACKUP" | awk '{print $1}')

ssh -o BatchMode=yes 3090 "python3 - <<'PY'
import json
from pathlib import Path
p=Path('/home/straughter/Wan2GP/models/_settings.json')
data=json.loads(p.read_text())
old=data.get('multi_prompts_gen_type')
data['multi_prompts_gen_type']='FG'
tmp=p.with_suffix('.json.lf004-tmp')
tmp.write_text(json.dumps(data, indent=4) + '\\n')
tmp.replace(p)
print(f'prompt_mode {old}->FG')
PY"

export WANGP_VISION_BACKEND=local
export WANGP_WHISPER_LOCAL_FIRST=0
export WANGP_QC_URL=http://localhost:8000/health

set -o pipefail
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python scripts/run_jobs.py \
  --db "$DB" \
  2>&1 | tee -a "$PROVENANCE/execution.log"

restore_settings
after_restore_sha=$(ssh -o BatchMode=yes 3090 "sha256sum $REMOTE_SETTINGS" | awk '{print $1}')
python3 - "$before_sha" "$after_restore_sha" > "$MODE_RECORD" <<'PY'
import hashlib,json,sys
before,after=sys.argv[1:]
backup=hashlib.sha256(open('datasets/runs/provenance/lf004-operator-dogfood-20260920/wan2gp-models-settings.before.json','rb').read()).hexdigest()
print(json.dumps({
  'schema_version': 1,
  'reason': 'temporarily restored the accepted Wan2GP FG all-lines-one-prompt mode because the current global PG default parsed the approved multiline prompt as five tasks',
  'settings_path': '/home/straughter/Wan2GP/models/_settings.json',
  'before_sha256': before,
  'render_time_value': 'FG',
  'restored_sha256': after,
  'restored_equal_before': before == after,
  'backup_sha256': backup,
}, indent=2, sort_keys=True))
PY
cat "$MODE_RECORD"
