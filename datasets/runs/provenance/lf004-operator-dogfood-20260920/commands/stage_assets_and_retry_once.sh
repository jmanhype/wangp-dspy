#!/bin/bash
set -euo pipefail

ROOT=/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-42no
PROVENANCE="$ROOT/datasets/runs/provenance/lf004-operator-dogfood-20260920"
BRIEF="$ROOT/datasets/content_briefs/lf004-operator-dogfood"
DB="$ROOT/datasets/lf004-operator-dogfood-20260920.jobs.db"

export WANGP_ASSET_MAP="$BRIEF/plates=/home/straughter/Wan2GP/lf004-operator-dogfood-20260920/plates;$ROOT/datasets/runs/provenance=/home/straughter/Wan2GP/lf004-operator-dogfood-20260920/datasets/runs/provenance"

cd "$ROOT"

/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python - <<'PY'
from pathlib import Path, PurePosixPath
from host.render_host import SshHost

root = Path.cwd()
brief = root / "datasets/content_briefs/lf004-operator-dogfood"
paths = [
    brief / "plates/anchor.png",
    brief / "plates/Tess.png",
    brief / "plates/Rho.png",
    root / "datasets/runs/provenance/lf003-vibevoice-audition-20260917/audio/tess.prepared.wav",
    root / "datasets/runs/provenance/lf003-vibevoice-rho-strong-20260918/audio/rho.prepared.wav",
    root / "datasets/runs/provenance/lf003-four-cut-fullgate-20260919/audio/tess-cut3.prepared.wav",
    root / "datasets/runs/provenance/lf003-four-cut-fullgate-20260919/audio/rho-cut4.prepared.wav",
]
host = SshHost(
    target="3090",
    wgp_root="/home/straughter/Wan2GP",
    pull_root="datasets/runs/pull",
)
for path in paths:
    remote = host.map_asset(str(path))
    host.makedirs(str(PurePosixPath(remote).parent))
    actual = host.push_asset(str(path))
    assert actual == remote, (actual, remote)
    print(f"staged {path} -> {remote}")
PY

export WANGP_VISION_BACKEND=local
export WANGP_WHISPER_LOCAL_FIRST=0
export WANGP_QC_URL=http://localhost:8000/health

set -o pipefail
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python scripts/run_jobs.py \
  --db "$DB" --retry-failed \
  2>&1 | tee -a "$PROVENANCE/execution.log"
