#!/bin/bash
set -euo pipefail

ROOT=/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-42no
PROVENANCE="$ROOT/datasets/runs/provenance/lf004-operator-dogfood-20260920"
DB="$ROOT/datasets/lf004-operator-dogfood-20260920.jobs.db"
REMOTE_SETTINGS=/home/straughter/Wan2GP/wgp_config.json
BACKUP="$PROVENANCE/wgp-config.runtime-fields.before.json"
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
plan=json.loads((root/"datasets/content_briefs/lf004-operator-dogfood/plan.json").read_text())
characters={c["sn_tag"]:c for c in plan["characters"]}
queue=JobQueue("datasets/lf004-operator-dogfood-20260920.jobs.db")
records=[]
try:
    ids=[]
    for state in ("failed","dead_letter","pending","rendered_pending_qc","qc"):
        ids.extend(queue.list_state(state))
    jobs=sorted((queue.get(jid) for jid in ids), key=lambda j:j.clips[0]["clip_index"])
    assert [j.clips[0]["clip_index"] for j in jobs] == [1,2,3,4]
    for job in jobs:
        clips=list(job.clips); clip=clips[0]
        speaker=characters[clip["speaker_sn"]]
        others=[c for sn,c in characters.items() if sn != clip["speaker_sn"]]
        clip["model_type"]="minimax_h3_ref2va_pruned"
        clip["audio_prompt_type"]="A"
        clip["video_prompt_type"]="I"
        clip["image_prompt_type"]="S" if clip["chain"]["re_anchor"] else "I"
        clip["image_start"]=clip["image_refs"][0] if clip["chain"]["re_anchor"] else None
        clip["action"]="subtle natural listening and speaking motion"
        clip["speaker_description"]=(
            f"{speaker['sn_tag']} ({speaker['name']}): {speaker['description']}; "
            + "; ".join(f"silent {c['sn_tag']} ({c['name']}): {c['description']}" for c in others)
        )
        clip["premise_id"]="lf004-operator-dogfood"
        clip["resolution"]=[480,832]
        clip["requested_frames"]=107
        clip["video_length"]=107
        clip["force_fps"]=24
        clip["steps"]=20
        clip["audio"]={
            "path": clip["audio_guide"],
            "apad": True,
            "start_s": 0.0,
            "padded_duration_s": 4.458333333333333,
        }
        queue.update_clips(job.job_id, clips)
        records.append({
            "job_id": job.job_id,
            "clip_index": clip["clip_index"],
            "status": clip.get("status"),
            "model_type": clip["model_type"],
            "action": clip["action"],
            "speaker_description": clip["speaker_description"],
        })
    failed=queue.list_state("failed") + queue.list_state("dead_letter")
    assert failed == ["job-1789937516351-1da5e2de"], failed
    queue.set_state(failed[0], "dead_letter")
    attempt=queue.reopen_dead_letter(
        failed[0],
        reason="reconcile Ref2VA model/action/speaker runtime metadata from approved plan without changing rendered bytes",
    )
finally:
    queue.close()

payload={
    "schema_version": 1,
    "reason": "content-brief queue path omitted QC/runtime fields present in accepted Ref2VA jobs; reconciled from approved plan and rendered settings",
    "canonical_plan_sha256": "70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86",
    "reopened_attempt_id": attempt,
    "jobs": records,
}
out=root/"datasets/runs/provenance/lf004-operator-dogfood-20260920/runtime-fields-reconciliation.json"
out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
print(json.dumps(payload,indent=2,sort_keys=True))
PY

scp -q "3090:$REMOTE_SETTINGS" "$BACKUP"
ssh -o BatchMode=yes 3090 "python3 - <<'PY'
import json
from pathlib import Path
p=Path('/home/straughter/Wan2GP/wgp_config.json'); d=json.loads(p.read_text()); d['multi_prompts_gen_type']='FG'
t=p.with_name('wgp_config.lf004-runtime-tmp.json'); t.write_text(json.dumps(d,indent=4)+'\\n'); t.replace(p)
PY"

export WANGP_VISION_BACKEND=local
export WANGP_WHISPER_LOCAL_FIRST=0
export WANGP_QC_URL=http://localhost:8000/health

set -o pipefail
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python scripts/run_jobs.py \
  --db "$DB" \
  2>&1 | tee -a "$PROVENANCE/execution.log"

restore_settings
ssh -o BatchMode=yes 3090 "sha256sum $REMOTE_SETTINGS" > "$PROVENANCE/wgp-config-after-runtime-fields.sha256"
cat "$PROVENANCE/wgp-config-after-runtime-fields.sha256"
