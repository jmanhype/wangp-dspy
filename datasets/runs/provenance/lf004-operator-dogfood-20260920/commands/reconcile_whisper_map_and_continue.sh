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
queue = JobQueue("datasets/lf004-operator-dogfood-20260920.jobs.db")
records = []
try:
    states = ["dead_letter", "failed", "pending"]
    job_ids = [jid for state in states for jid in queue.list_state(state)]
    jobs = sorted((queue.get(jid) for jid in job_ids), key=lambda job: job.clips[0]["clip_index"])
    assert [job.clips[0]["clip_index"] for job in jobs] == [1, 2, 3, 4]
    for job in jobs:
        clips = list(job.clips)
        clip = clips[0]
        provenance = dict(clip["audio_provenance"])
        provenance["whisper_map"] = clip["audio_guide"]
        clip["audio_provenance"] = provenance
        queue.update_clips(job.job_id, clips)
        records.append({
            "job_id": job.job_id,
            "clip_index": clip["clip_index"],
            "audio_guide": clip["audio_guide"],
            "whisper_map": provenance["whisper_map"],
            "state_before_reopen": job.state,
        })
    dead_letter = queue.list_state("dead_letter")
    assert dead_letter == ["job-1789937516351-1da5e2de"], dead_letter
    attempt_id = queue.reopen_dead_letter(
        dead_letter[0],
        reason="runtime audio whisper_map reconciled to approved audio guide after empty-path rejection",
    )
finally:
    queue.close()

payload = {
    "schema_version": 1,
    "reason": "content-brief run_film path omitted non-empty whisper_map required by accepted Ref2VA runtime; reconcile from each approved audio guide without changing bytes or render identity",
    "canonical_plan_sha256": "70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86",
    "reopened_attempt_id": attempt_id,
    "jobs": records,
}
out = root / "datasets/runs/provenance/lf004-operator-dogfood-20260920/runtime-whisper-map-reconciliation.json"
out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2, sort_keys=True))
PY

export WANGP_VISION_BACKEND=local
export WANGP_WHISPER_LOCAL_FIRST=0
export WANGP_QC_URL=http://localhost:8000/health

set -o pipefail
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python scripts/run_jobs.py \
  --db "$DB" \
  2>&1 | tee -a "$PROVENANCE/execution.log"
