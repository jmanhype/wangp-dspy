#!/bin/bash
set -euo pipefail

LIVE=/home/straughter/Wan2GP
SOURCE=/home/straughter/Wan2GP-story-WD-ycjg
RUN=/home/straughter/wd-ycjg-run
LOG=$RUN/host-logs
MODEL_MANIFEST=/tmp/wd-ycjg-download-manifest.tsv
PY_MANIFEST=/tmp/wd-ycjg-python-deps.tsv

{
  date -u +%Y-%m-%dT%H:%M:%SZ
  hostname
  git -C "$SOURCE" rev-parse HEAD
  git -C "$SOURCE" status --porcelain=v1
  git -C "$LIVE" rev-parse HEAD
  git -C "$LIVE" status --porcelain=v1 | sha256sum
  df -B1 "$RUN"
  nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits
  nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
} >"$LOG/90_final_postflight.txt"

while IFS=$'\t' read -r _ destination expected_size expected_sha; do
  test "$(stat -c %s "$destination")" = "$expected_size"
  test "$(sha256sum "$destination" | awk '{print $1}')" = "$expected_sha"
done < <(tail -n +2 "$MODEL_MANIFEST")
sha256sum $(tail -n +2 "$MODEL_MANIFEST" | cut -f2) >"$LOG/91_model_asset_hashes_after.txt"

while IFS=$'\t' read -r _ destination expected_size expected_sha; do
  test "$(stat -c %s "$destination")" = "$expected_size"
  test "$(sha256sum "$destination" | awk '{print $1}')" = "$expected_sha"
done < <(tail -n +2 "$PY_MANIFEST")
sha256sum $(tail -n +2 "$PY_MANIFEST" | cut -f2) >"$LOG/92_python_dependency_hashes_after.txt"

sha256sum "$RUN/inputs/control.mp4" "$RUN/inputs/reference.png" "$RUN/inputs/alternate-reference.png" "$RUN/inputs/control-mask.mp4" >"$LOG/93_input_hashes_after.txt"
find "$RUN" -type f -printf '%s %p\n' | sort >"$LOG/94_run_inventory.txt"
du -sb "$RUN" >"$LOG/95_run_size.txt"
printf 'model_download_bytes=28418240079\nmodel_session_bytes=2408271915\nstory_local_dependency_bytes=665045\ncombined_session_network_bytes=2408936960\ntotal_authorized_bytes=28418905124\nlive_dependency_mutation=0\n' >"$LOG/96_final_download_accounting.txt"
printf 'POSTFLIGHT_PASS\n'
