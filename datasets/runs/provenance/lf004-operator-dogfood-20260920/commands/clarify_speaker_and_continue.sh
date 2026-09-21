#!/bin/bash
set -euo pipefail

ROOT=/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-42no
PROVENANCE="$ROOT/datasets/runs/provenance/lf004-operator-dogfood-20260920"
DB="$ROOT/datasets/lf004-operator-dogfood-20260920.jobs.db"
REMOTE_SETTINGS=/home/straughter/Wan2GP/wgp_config.json
BACKUP="$PROVENANCE/wgp-config.speaker-clarify.before.json"
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
import json
from pathlib import Path
from services.jobs.queue import JobQueue

root=Path.cwd()
queue=JobQueue("datasets/lf004-operator-dogfood-20260920.jobs.db")
records=[]
try:
    ids=[]
    for state in ("failed","dead_letter","pending","rendered_pending_qc","qc"):
        ids.extend(queue.list_state(state))
    jobs=sorted((queue.get(jid) for jid in ids), key=lambda j:j.clips[0]["clip_index"])
    assert [j.clips[0]["clip_index"] for j in jobs] == [1,2,3,4]
    descriptions={
        1:"Tess (S1), the woman on the LEFT; not Rho (S2) on the RIGHT",
        2:"Rho (S2), the man on the RIGHT; not Tess (S1) on the LEFT",
        3:"Tess (S1), the woman on the LEFT; not Rho (S2) on the RIGHT",
        4:"Rho (S2), the man on the RIGHT; not Tess (S1) on the LEFT",
    }
    for job in jobs:
        clips=list(job.clips); clip=clips[0]
        old=clip.get("speaker_description")
        clip["speaker_description"]=descriptions[int(clip["clip_index"])]
        queue.update_clips(job.job_id, clips)
        records.append({"job_id":job.job_id,"clip_index":clip["clip_index"],"before":old,"after":clip["speaker_description"]})
    dead=queue.list_state("dead_letter") + queue.list_state("failed")
    assert dead == ["job-1789937516351-1da5e2de"], dead
    if queue.get(dead[0]).state != "dead_letter":
        queue.set_state(dead[0], "dead_letter")
    attempt=queue.reopen_dead_letter(dead[0], reason="clarify expected speaker side after verified localizer returned normalized boxes in independent re-judge")
finally:
    queue.close()

payload={"schema_version":1,"reason":"long speaker roster text caused localizer pixel-coordinate/speaker confusion; concise side-anchored expected speaker verified independently on rendered cut 1","canonical_plan_sha256":"70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86","reopened_attempt_id":attempt,"jobs":records}
out=root/"datasets/runs/provenance/lf004-operator-dogfood-20260920/speaker-clarification.json"
out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
print(json.dumps(payload,indent=2,sort_keys=True))
PY

scp -q "3090:$REMOTE_SETTINGS" "$BACKUP"
ssh -o BatchMode=yes 3090 "python3 - <<'PY'
import json
from pathlib import Path
p=Path('/home/straughter/Wan2GP/wgp_config.json'); d=json.loads(p.read_text()); d['multi_prompts_gen_type']='FG'
t=p.with_name('wgp_config.lf004-speaker-tmp.json'); t.write_text(json.dumps(d,indent=4)+'\\n'); t.replace(p)
PY"

export WANGP_VISION_BACKEND=local
export WANGP_WHISPER_LOCAL_FIRST=0
export WANGP_QC_URL=http://localhost:8000/health

set -o pipefail
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python scripts/run_jobs.py \
  --db "$DB" \
  2>&1 | tee -a "$PROVENANCE/execution.log"

restore_settings
ssh -o BatchMode=yes 3090 "sha256sum $REMOTE_SETTINGS" > "$PROVENANCE/wgp-config-after-speaker-clarify.sha256"
cat "$PROVENANCE/wgp-config-after-speaker-clarify.sha256"
