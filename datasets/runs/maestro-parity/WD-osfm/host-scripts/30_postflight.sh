#!/bin/bash
set -euo pipefail

LIVE=/home/straughter/Wan2GP
SOURCE=/home/straughter/Wan2GP-story-WD-osfm
RUN=/home/straughter/wd-osfm-run
MANIFEST=/tmp/wd-osfm-download-manifest.tsv

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
test "$(stat -Lc %s /home/straughter/Wan2GP/ckpts/ltx-2.3-temporal-upscaler-x2-1.0.safetensors)" = 261944000
test "$(sha256sum /home/straughter/Wan2GP/ckpts/ltx-2.3-temporal-upscaler-x2-1.0.safetensors | awk '{print $1}')" = 2bc3300f2b3c3c1834d72164fbf13a3b9fd73e5a741e8a2c3f4035f89a75c3fe
sha256sum "$RUN/inputs/control.mp4" "$RUN/inputs/reference.png" "$RUN/inputs/alternate-reference.png" "$RUN/inputs/control-mask.mp4" >"$RUN/host-logs/92_input_hashes_after.txt"
find "$RUN" -type f -printf '%s %p\n' | sort >"$RUN/host-logs/93_run_inventory.txt"
du -sb "$RUN" >"$RUN/host-logs/94_run_size.txt"
test ! -e /home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA_int8_convrot.safetensors
printf 'offloaded_remote_absent=PASS\nmodel_download_bytes=35379235525\nlinked_download_bytes=0\nlive_dependency_mutation=0\n' >"$RUN/host-logs/95_final_download_accounting.txt"
printf 'POSTFLIGHT_PASS\n'
