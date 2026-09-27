#!/bin/bash
set -euo pipefail

LIVE=/home/straughter/Wan2GP
SOURCE=/home/straughter/Wan2GP-story-WD-ycjg
RUN=/home/straughter/wd-ycjg-run
MANIFEST=/tmp/wd-ycjg-download-manifest.tsv

test "$(hostname)" = straughter-Z690-Steel-Legend
test "$(git -C "$LIVE" rev-parse HEAD)" = 4c93b64a47b5b0a915f2abec2ce754be98227150
test -s /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4
test "$(sha256sum /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4 | awk '{print $1}')" = c71398ba3c4fe6394c83450d7cd5267187e4c65b8d9b568f9457f1a9aac03ca8

mkdir -p "$RUN/host-logs" "$RUN/inputs" "$RUN/settings" "$RUN/outputs" "$RUN/boundaries" "$RUN/rejected-downloads"
df -B1 "$LIVE" >"$RUN/host-logs/00_disk_before.txt"
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits >"$RUN/host-logs/00_gpu_before.txt"
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader >"$RUN/host-logs/00_gpu_apps_before.txt" || true

free=$(df -B1 "$LIVE" | awk 'NR==2 {print $4}')
if test -f /home/straughter/Wan2GP/ckpts/scail2_14B_quanto_mbf16_int8.safetensors; then
  test "$free" -ge 30000000000
else
  test "$free" -ge 40000000000
fi
gpu_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
test "$gpu_used" -le 1000

: >"$RUN/host-logs/download-report.tsv"
declared_bytes=0
session_bytes=0
while IFS=$'\t' read -r url destination expected_size expected_sha; do
  test -n "$url"
  test -n "$destination"
  test -n "$expected_size"
  test -n "$expected_sha"
  mkdir -p "$(dirname "$destination")"
  declared_bytes=$((declared_bytes + expected_size))
  status=already-present
  if ! test -f "$destination"; then
    status=downloaded
    part="${destination}.wd-ycjg.part"
    curl --fail --location --retry 5 --retry-delay 5 --connect-timeout 30 \
      --continue-at - --output "$part" "$url"
    actual_size=$(stat -c %s "$part")
    actual_sha=$(sha256sum "$part" | awk '{print $1}')
    if test "$actual_size" != "$expected_size" || test "$actual_sha" != "$expected_sha"; then
      mv "$part" "$RUN/rejected-downloads/$(basename "$destination").$(date -u +%Y%m%dT%H%MSZ).rejected"
      printf 'HASH_MISMATCH\t%s\t%s\t%s\n' "$url" "$actual_size" "$actual_sha" >>"$RUN/host-logs/download-failures.tsv"
      exit 90
    fi
    mv "$part" "$destination"
    session_bytes=$((session_bytes + expected_size))
  else
    actual_size=$(stat -c %s "$destination")
    actual_sha=$(sha256sum "$destination" | awk '{print $1}')
    test "$actual_size" = "$expected_size"
    test "$actual_sha" = "$expected_sha"
  fi
  printf '%s\t%s\t%s\t%s\t%s\n' "$status" "$url" "$destination" "$actual_size" "$actual_sha" >>"$RUN/host-logs/download-report.tsv"
done < <(tail -n +2 "$MANIFEST")

printf 'planned_bytes=28418240079\nactual_bytes=%s\nsession_bytes=%s\nasset_count=16\n' "$declared_bytes" "$session_bytes" >"$RUN/host-logs/download-accounting.txt"

while IFS=$'\t' read -r _ destination expected_size expected_sha; do
  test "$(stat -c %s "$destination")" = "$expected_size"
  test "$(sha256sum "$destination" | awk '{print $1}')" = "$expected_sha"
done < <(tail -n +2 "$MANIFEST")
sha256sum $(tail -n +2 "$MANIFEST" | cut -f2) >"$RUN/host-logs/11_asset_hashes_after_download.txt"

cp /home/straughter/Downloads/HOL120_ssscdn_scail_r9_00001.mp4 "$RUN/inputs/control.mp4"
ffmpeg -nostdin -v error -y -i "$RUN/inputs/control.mp4" -update 1 -frames:v 1 "$RUN/inputs/reference.png"
ffmpeg -nostdin -v error -y -i "$RUN/inputs/control.mp4" -vf "select=eq(n\,4)" -frames:v 1 "$RUN/inputs/alternate-reference.png"
sha256sum "$RUN/inputs/control.mp4" "$RUN/inputs/reference.png" "$RUN/inputs/alternate-reference.png" >"$RUN/host-logs/12_source_hashes.txt"

if ! test -e "$SOURCE"; then
  git -C "$LIVE" worktree add --detach "$SOURCE" 4c93b64a47b5b0a915f2abec2ce754be98227150 >"$RUN/host-logs/13_worktree_deploy.txt" 2>&1
fi
git -C "$SOURCE" restore -- shared/gradio/hierarchy_selector/hierarchy_selector.pyi 2>/dev/null || true
if ! test -e "$SOURCE/ckpts"; then
  ln -s "$LIVE/ckpts" "$SOURCE/ckpts"
fi
test "$(git -C "$SOURCE" rev-parse HEAD)" = 4c93b64a47b5b0a915f2abec2ce754be98227150
test "$(git -C "$SOURCE" status --porcelain=v1)" = "?? ckpts"
df -B1 "$LIVE" >"$RUN/host-logs/14_disk_after_download.txt"
printf 'DOWNLOAD_PREFLIGHT_PASS\n'
