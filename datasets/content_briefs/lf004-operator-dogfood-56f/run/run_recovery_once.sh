#!/bin/bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)
BASE="$ROOT/datasets/content_briefs/lf004-operator-dogfood-56f"
SOURCE="$ROOT/datasets/content_briefs/lf004-operator-dogfood"
RUN_ID=lf004-operator-dogfood-56f-recovery-20260921
DB="$ROOT/datasets/$RUN_ID.jobs.db"
PROVENANCE="$ROOT/datasets/runs/provenance/$RUN_ID"
REMOTE_WGP=/home/straughter/Wan2GP/wgp_config.json
REMOTE_MODELS=/home/straughter/Wan2GP/models/_settings.json
PYTHON="$ROOT/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then PYTHON=/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python; fi
if [[ -e "$DB" || -e "$PROVENANCE/execution-command.json" ]]; then
  echo "refusing a second LF004 recovery execution" >&2
  exit 3
fi
mkdir -p "$PROVENANCE"

export WANGP_VISION_BACKEND=local
export WANGP_WHISPER_LOCAL_FIRST=0
export WANGP_QC_URL=http://localhost:8000/health
export WANGP_ASSET_MAP="$SOURCE/plates=/home/straughter/Wan2GP/$RUN_ID/plates;$ROOT/datasets/runs/provenance=/home/straughter/Wan2GP/$RUN_ID/datasets/runs/provenance"
export WANGP_SYNCNET_MODEL=/home/straughter/models/syncnet_v2/syncnet_v2.model
export WANGP_SYNCNET_PYTHON=/home/straughter/Wan2GP/venv/bin/python
export WANGP_SYNCNET_REPO=/home/straughter/wangp-dspy-vibevoice-20260916

"$PYTHON" - <<'PY'
import json, os
from pathlib import Path
root = Path.cwd()
base = root / "datasets/content_briefs/lf004-operator-dogfood-56f"
source = root / "datasets/content_briefs/lf004-operator-dogfood"
guides = [root / "datasets/runs/provenance/lf003-vibevoice-audition-20260917/audio/tess.prepared.wav", root / "datasets/runs/provenance/lf003-vibevoice-rho-strong-20260918/audio/rho.prepared.wav", root / "datasets/runs/provenance/lf003-four-cut-fullgate-20260919/audio/tess-cut3.prepared.wav", root / "datasets/runs/provenance/lf003-four-cut-fullgate-20260919/audio/rho-cut4.prepared.wav"]
command = ["scripts/run_film.py", "--script", str(base / "run/script.txt"), "--plates", str(source / "plates"), "--characters", "Tess:S1:a sleepless young observatory astronomer with short dark hair, navy jacket, silver star pin, standing on the LEFT inside a glass-dome control room", "Rho:S2:a pragmatic bearded station caretaker with red knit cap and olive work jacket, standing on the RIGHT inside the same glass-dome observatory control room", "--db", "datasets/lf004-operator-dogfood-56f-recovery-20260921.jobs.db", *[item for value in [2.3333333333333335] * 4 for item in ("--duration-s", str(value))], *[item for guide in guides for item in ("--audio", str(guide))]]
payload = {"schema_version": 1, "execution_count": 1, "command": command, "environment": {key: value for key, value in os.environ.items() if key.startswith("WANGP_")}, "canonical_plan_sha256": "620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8"}
out = root / "datasets/runs/provenance/lf004-operator-dogfood-56f-recovery-20260921/execution-command.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(json.dumps(payload, sort_keys=True))
PY

{
  echo "LF004 56-frame recovery preflight $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  ssh -o BatchMode=yes -o ConnectTimeout=15 3090 nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader
  ssh -o BatchMode=yes -o ConnectTimeout=15 3090 df -h /home/straughter/Wan2GP
  ssh -o BatchMode=yes -o ConnectTimeout=15 3090 test -d /home/straughter/Wan2GP/acceptance
  ssh -o BatchMode=yes -o ConnectTimeout=15 3090 test -x /home/straughter/Wan2GP/venv/bin/python
  ssh -o BatchMode=yes -o ConnectTimeout=15 3090 test -f /home/straughter/models/syncnet_v2/syncnet_v2.model
  ssh -o BatchMode=yes -o ConnectTimeout=15 3090 test -d /home/straughter/wangp-dspy-vibevoice-20260916
  ssh -o BatchMode=yes -o ConnectTimeout=15 3090 curl -fsS -m 5 http://localhost:8000/health
} 2>&1 | tee "$PROVENANCE/preflight.txt"
available_kb=$(ssh -o BatchMode=yes 3090 df -k /home/straughter/Wan2GP | awk 'NR==2 {print $4}')
(( available_kb >= 10 * 1024 * 1024 ))

"$PYTHON" - <<'PY'
from pathlib import Path, PurePosixPath
from host.render_host import SshHost
root = Path.cwd()
source = root / "datasets/content_briefs/lf004-operator-dogfood"
run_id = "lf004-operator-dogfood-56f-recovery-20260921"
remote = f"/home/straughter/Wan2GP/{run_id}"
asset_map = {str(source / "plates"): f"{remote}/plates", str(root / "datasets/runs/provenance"): f"{remote}/datasets/runs/provenance"}
host = SshHost(target="3090", wgp_root="/home/straughter/Wan2GP", pull_root="datasets/runs/pull", asset_map=asset_map)
paths = [*sorted((source / "plates").glob("*.png")), root / "datasets/runs/provenance/lf003-vibevoice-audition-20260917/audio/tess.prepared.wav", root / "datasets/runs/provenance/lf003-vibevoice-rho-strong-20260918/audio/rho.prepared.wav", root / "datasets/runs/provenance/lf003-four-cut-fullgate-20260919/audio/tess-cut3.prepared.wav", root / "datasets/runs/provenance/lf003-four-cut-fullgate-20260919/audio/rho-cut4.prepared.wav"]
for path in paths:
    destination = host.map_asset(str(path))
    host.makedirs(str(PurePosixPath(destination).parent))
    assert host.push_asset(str(path)) == destination
    print(f"staged {path.relative_to(root)} -> {destination}")
PY

scp -q 3090:$REMOTE_WGP "$PROVENANCE/wgp-config.before.json"
scp -q 3090:$REMOTE_MODELS "$PROVENANCE/wan2gp-models-settings.before.json"
restore_settings() {
  scp -q "$PROVENANCE/wgp-config.before.json" 3090:$REMOTE_WGP
  scp -q "$PROVENANCE/wan2gp-models-settings.before.json" 3090:$REMOTE_MODELS
  ssh -o BatchMode=yes 3090 sha256sum "$REMOTE_WGP" "$REMOTE_MODELS" > "$PROVENANCE/remote-settings-restored.sha256"
}
trap restore_settings EXIT INT TERM
"$PYTHON" - "$PROVENANCE" <<'PY'
import json, sys
from pathlib import Path
for source, target in (("wgp-config.before.json", "wgp-config.render.json"), ("wan2gp-models-settings.before.json", "wan2gp-models-settings.render.json")):
    path = Path(sys.argv[1]) / source
    data = json.loads(path.read_text())
    before = data.get("multi_prompts_gen_type")
    data["multi_prompts_gen_type"] = "FG"
    (path.parent / target).write_text(json.dumps(data, indent=4) + "\n")
    print(f"prompt_mode {source} {before}->FG")
PY
scp -q "$PROVENANCE/wgp-config.render.json" 3090:$REMOTE_WGP
scp -q "$PROVENANCE/wan2gp-models-settings.render.json" 3090:$REMOTE_MODELS

cd "$ROOT"
set -o pipefail
"$PYTHON" scripts/run_film.py \
  --script "$BASE/run/script.txt" \
  --plates "$SOURCE/plates" \
  --characters 'Tess:S1:a sleepless young observatory astronomer with short dark hair, navy jacket, silver star pin, standing on the LEFT inside a glass-dome control room' 'Rho:S2:a pragmatic bearded station caretaker with red knit cap and olive work jacket, standing on the RIGHT inside the same glass-dome observatory control room' \
  --db "$DB" \
  --duration-s 2.3333333333333335 --duration-s 2.3333333333333335 --duration-s 2.3333333333333335 --duration-s 2.3333333333333335 \
  --audio "$ROOT/datasets/runs/provenance/lf003-vibevoice-audition-20260917/audio/tess.prepared.wav" \
  --audio "$ROOT/datasets/runs/provenance/lf003-vibevoice-rho-strong-20260918/audio/rho.prepared.wav" \
  --audio "$ROOT/datasets/runs/provenance/lf003-four-cut-fullgate-20260919/audio/tess-cut3.prepared.wav" \
  --audio "$ROOT/datasets/runs/provenance/lf003-four-cut-fullgate-20260919/audio/rho-cut4.prepared.wav" \
  2>&1 | tee "$PROVENANCE/execution.log"

"$PYTHON" "$BASE/run/recover_once.py" reconcile
"$PYTHON" scripts/run_jobs.py --db "$DB" 2>&1 | tee -a "$PROVENANCE/execution.log"
"$PYTHON" "$BASE/run/recover_once.py" finalize 2>&1 | tee "$PROVENANCE/finalize.log"
trap - EXIT INT TERM
restore_settings
