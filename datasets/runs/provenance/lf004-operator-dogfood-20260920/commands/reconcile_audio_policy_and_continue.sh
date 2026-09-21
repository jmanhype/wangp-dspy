#!/bin/bash
set -euo pipefail

ROOT=/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-42no
PROVENANCE="$ROOT/datasets/runs/provenance/lf004-operator-dogfood-20260920"
DB="$ROOT/datasets/lf004-operator-dogfood-20260920.jobs.db"
REMOTE_SETTINGS=/home/straughter/Wan2GP/wgp_config.json
BACKUP="$PROVENANCE/wgp-config.audio-policy-continue.before.json"
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
queue=JobQueue("datasets/lf004-operator-dogfood-20260920.jobs.db")
records=[]
try:
    ids=[]
    for state in ("failed","dead_letter","pending","rendered_pending_qc","qc"):
        ids.extend(queue.list_state(state))
    jobs=sorted((queue.get(jid) for jid in ids), key=lambda j:j.clips[0]["clip_index"])
    assert [j.clips[0]["clip_index"] for j in jobs] == [1,2,3,4], jobs
    for job, dialogue, character_by_sn in zip(
            jobs, plan["dialogue"],
            [{c["sn_tag"]: c for c in plan["characters"]} for _ in jobs],
            strict=True):
        clips=list(job.clips)
        clip=clips[0]
        keeper=clip["audio_provenance"]["keeper_window_s"]
        sn=clip["speaker_sn"]
        clip["audio_policy"]={
            "discard_rendered_audio": False,
            "remux_source": "source_master",
            "remux_window": keeper,
        }
        clip["audio_carrier"]="native_h3"
        clip["speaker_manifest"]={
            "schema": "wangp-dspy.speaker-manifest/v1",
            "turns": [{
                "turn_index": int(clip["clip_index"]),
                "speaker_id": sn,
                "picture_n": 1,
                "audio_path": clip["audio_guide"],
                "intended_text": dialogue["text"],
            }],
        }
        clip["profile"]=3
        clip["recipe_name"]="production"
        queue.update_clips(job.job_id, clips)
        records.append({
            "job_id": job.job_id,
            "clip_index": clip["clip_index"],
            "status_before_reconcile": clip.get("status"),
            "audio_policy": clip["audio_policy"],
            "audio_carrier": clip["audio_carrier"],
            "speaker_manifest": clip["speaker_manifest"],
        })
    failed=queue.list_state("failed") + queue.list_state("dead_letter")
    assert failed == ["job-1789937516351-1da5e2de"], failed
    queue.set_state(failed[0], "dead_letter")
    attempt=queue.reopen_dead_letter(
        failed[0],
        reason="reconcile top-level Ref2VA audio policy/carrier/speaker metadata from generated settings without changing rendered bytes",
    )
finally:
    queue.close()

payload={
    "schema_version": 1,
    "reason": "content-brief queue envelope omitted top-level audio policy/carrier/speaker manifest required by QC; fields reconciled from generated Ref2VA settings and approved plan",
    "canonical_plan_sha256": "70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86",
    "reopened_attempt_id": attempt,
    "jobs": records,
}
out=root/"datasets/runs/provenance/lf004-operator-dogfood-20260920/audio-policy-reconciliation.json"
out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
print(json.dumps(payload,indent=2,sort_keys=True))
PY

scp -q "3090:$REMOTE_SETTINGS" "$BACKUP"
ssh -o BatchMode=yes 3090 "python3 - <<'PY'
import json
from pathlib import Path
p=Path('/home/straughter/Wan2GP/wgp_config.json')
d=json.loads(p.read_text()); d['multi_prompts_gen_type']='FG'
t=p.with_name('wgp_config.lf004-continue-tmp.json')
t.write_text(json.dumps(d,indent=4)+'\\n'); t.replace(p)
PY"

export WANGP_VISION_BACKEND=local
export WANGP_WHISPER_LOCAL_FIRST=0
export WANGP_QC_URL=http://localhost:8000/health

set -o pipefail
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python scripts/run_jobs.py \
  --db "$DB" \
  2>&1 | tee -a "$PROVENANCE/execution.log"

restore_settings
ssh -o BatchMode=yes 3090 "sha256sum $REMOTE_SETTINGS" > "$PROVENANCE/wgp-config-after-audio-policy-continue.sha256"
cat "$PROVENANCE/wgp-config-after-audio-policy-continue.sha256"
