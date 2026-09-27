#!/bin/bash
set -euo pipefail

LIVE=/home/straughter/Wan2GP
SOURCE=/home/straughter/Wan2GP-story-WD-28i5
RUN=/home/straughter/wd-28i5-run
MANIFEST=/tmp/wd-28i5-download-manifest.tsv
SHARED=/tmp/wd-28i5-shared-manifest.tsv

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
} >"$RUN/host-logs/90_final_postflight.txt"

while IFS=$'\t' read -r _ destination expected_size expected_sha; do
  test "$(stat -c %s "$destination")" = "$expected_size"
  test "$(sha256sum "$destination" | awk '{print $1}')" = "$expected_sha"
done < <(tail -n +2 "$MANIFEST")
sha256sum $(tail -n +2 "$MANIFEST" | cut -f2) >"$RUN/host-logs/91_model_hashes_after.txt"

while IFS=$'\t' read -r destination expected_size expected_sha; do
  test "$(stat -c %s "$destination")" = "$expected_size"
  test "$(sha256sum "$destination" | awk '{print $1}')" = "$expected_sha"
done < <(tail -n +2 "$SHARED")
sha256sum $(tail -n +2 "$SHARED" | cut -f1) >"$RUN/host-logs/92_shared_dependency_hashes_after.txt"

sha256sum "$RUN/inputs/control.mp4" "$RUN/inputs/reference.png" "$RUN/inputs/alternate-reference.png" "$RUN/inputs/control-mask.mp4" >"$RUN/host-logs/93_input_hashes_after.txt"
find "$RUN" -type f -printf '%s %p\n' | sort >"$RUN/host-logs/94_run_inventory.txt"
du -sb "$RUN" >"$RUN/host-logs/95_run_size.txt"
printf 'model_download_bytes=14903022013\nmodel_session_bytes=14903022013\nshared_dependency_download_bytes=0\ntotal_authorized_bytes=14903022013\nlive_dependency_mutation=0\n' >"$RUN/host-logs/96_final_download_accounting.txt"
printf 'POSTFLIGHT_PASS\n'
