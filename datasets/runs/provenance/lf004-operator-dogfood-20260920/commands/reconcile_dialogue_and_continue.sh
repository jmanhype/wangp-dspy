#!/bin/bash
set -euo pipefail

ROOT=/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-42no
PROVENANCE="$ROOT/datasets/runs/provenance/lf004-operator-dogfood-20260920"
DB="$ROOT/datasets/lf004-operator-dogfood-20260920.jobs.db"

export WANGP_ASSET_MAP="$ROOT/datasets/content_briefs/lf004-operator-dogfood/plates=/home/straughter/Wan2GP/lf004-operator-dogfood-20260920/plates;$ROOT/datasets/runs/provenance=/home/straughter/Wan2GP/lf004-operator-dogfood-20260920/datasets/runs/provenance"

cd "$ROOT"

/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python - <<'PY'
import json
from pathlib import Path
from services.jobs.queue import JobQueue

root = Path.cwd()
plan = json.loads((root / "datasets/content_briefs/lf004-operator-dogfood/plan.json").read_text())
dialogue = [row["text"] for row in plan["dialogue"]]
assert [row["speaker"] for row in plan["dialogue"]] == [clip["speaker"] for clip in plan["clips"]]
queue = JobQueue(str(root / "datasets/lf004-operator-dogfood-20260920.jobs.db"))
records = []
try:
    jobs = sorted(
        (queue.get(jid) for jid in queue.list_state("failed")
         + queue.list_state("pending")),
        key=lambda job: job.clips[0]["clip_index"],
    )
    assert [job.clips[0]["clip_index"] for job in jobs] == [1, 2, 3, 4]
    for job, text in zip(jobs, dialogue, strict=True):
        clips = list(job.clips)
        clips[0]["dialogue_text"] = text
        queue.update_clips(job.job_id, clips)
        records.append({
            "job_id": job.job_id,
            "clip_index": clips[0]["clip_index"],
            "dialogue_text": text,
            "failure_count_before_retry": job.failure_count,
        })
finally:
    queue.close()
payload = {
    "schema_version": 1,
    "reason": "run_film queue rows carried approved dialogue only inside prompt; reconcile scalar dialogue_text from approved canonical plan for Whisper gate without changing render inputs",
    "canonical_plan_sha256": "70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86",
    "jobs": records,
}
out = root / "datasets/runs/provenance/lf004-operator-dogfood-20260920/runtime-reconciliation.json"
out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2, sort_keys=True))
PY

export WANGP_VISION_BACKEND=local
export WANGP_WHISPER_LOCAL_FIRST=0
export WANGP_QC_URL=http://localhost:8000/health

set -o pipefail
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python scripts/run_jobs.py \
  --db "$DB" --retry-failed \
  2>&1 | tee -a "$PROVENANCE/execution.log"
