#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST=3090
RUN=/home/straughter/wd-osfm-run
SOURCE=/home/straughter/Wan2GP-story-WD-osfm

test -f "$ROOT/native-settings/create.json"
test -f "$ROOT/native-settings/probe-batch.json"
test -f "$ROOT/native-settings/upscale.json"
test -f "$ROOT/host-scripts/20_run_create.sh"
test -f "$ROOT/host-scripts/21_run_probes_upscale.sh"
test -f "$ROOT/host-scripts/30_postflight.sh"

ssh "$HOST" "mkdir -p '$RUN/host-scripts' '$RUN/settings'"
scp "$ROOT"/host-scripts/*.sh "$HOST:$RUN/host-scripts/"
scp "$ROOT"/native-settings/*.json "$HOST:$RUN/settings/"
ssh "$HOST" "chmod +x '$RUN/host-scripts/20_run_create.sh' '$RUN/host-scripts/21_run_probes_upscale.sh' '$RUN/host-scripts/30_postflight.sh'"

expected=$(
  find "$ROOT/native-settings" "$ROOT/host-scripts" -maxdepth 1 -type f -print0 |
    sort -z |
    while IFS= read -r -d '' file; do
      digest=$(shasum -a 256 "$file" | awk '{print $1}')
      relative=${file#"$ROOT"/}
      relative=${relative/#native-settings\//settings\/}
      printf '%s  %s\n' "$digest" "$relative"
    done
)
observed=$(ssh "$HOST" "cd '$RUN' && find settings host-scripts -maxdepth 1 -type f -print0 | sort -z | xargs -0 sha256sum")
test "$expected" = "$observed"

test "$(ssh "$HOST" "git -C '$SOURCE' rev-parse HEAD")" = 4c93b64a47b5b0a915f2abec2ce754be98227150
test "$(ssh "$HOST" "git -C '$SOURCE' status --porcelain=v1")" = '?? ckpts'
test "$(ssh "$HOST" "find '$RUN/outputs' -type f -print -quit")" = ""
ssh "$HOST" "df -B1 '$RUN' > '$RUN/host-logs/04_disk_before_create.txt'; nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits > '$RUN/host-logs/04_gpu_before_create.txt'; nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader > '$RUN/host-logs/04_gpu_apps_before_create.txt' || true"

printf 'RUN_ASSETS_DEPLOY_VERIFIED\n'
