#!/bin/bash
set -euo pipefail

LIVE=/home/straughter/Wan2GP
SOURCE=/home/straughter/Wan2GP-story-WD-28i5
RUN=/home/straughter/wd-28i5-run
MANIFEST=/tmp/wd-28i5-download-manifest.tsv
SHARED=/tmp/wd-28i5-shared-manifest.tsv

test "$(hostname)" = straughter-Z690-Steel-Legend
test "$(git -C "$LIVE" rev-parse HEAD)" = 4c93b64a47b5b0a915f2abec2ce754be98227150
test ! -e "$SOURCE"
mkdir -p "$RUN/host-logs" "$RUN/inputs" "$RUN/settings" "$RUN/outputs" "$RUN/boundaries" "$RUN/rejected-downloads"

df -B1 "$LIVE" >"$RUN/host-logs/00_disk_before.txt"
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits >"$RUN/host-logs/00_gpu_before.txt"
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader >"$RUN/host-logs/00_gpu_apps_before.txt" || true
free=$(df -B1 "$LIVE" | awk 'NR==2 {print $4}')
if test -f /home/straughter/Wan2GP/ckpts/wan2.1_text2video_14B_quanto_mbf16_int8.safetensors; then
  test "$free" -ge 18000000000
else
  test "$free" -ge 25000000000
fi
gpu_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
test "$gpu_used" -le 1000

previous_session_bytes=0
if test -s "$RUN/host-logs/download-accounting.txt"; then
  previous_session_bytes=$(awk -F= '$1=="session_bytes" {print $2}' "$RUN/host-logs/download-accounting.txt")
fi
: >"$RUN/host-logs/download-report.tsv"
session_bytes=${previous_session_bytes:-0}
while IFS=$'\t' read -r url destination expected_size expected_sha; do
  test -n "$url"
  mkdir -p "$(dirname "$destination")"
  status=already-present
  if ! test -f "$destination"; then
    status=downloaded
    part="${destination}.wd-28i5.part"
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
  fi
  actual_size=$(stat -c %s "$destination")
  actual_sha=$(sha256sum "$destination" | awk '{print $1}')
  test "$actual_size" = "$expected_size"
  test "$actual_sha" = "$expected_sha"
  printf '%s\t%s\t%s\t%s\t%s\n' "$status" "$url" "$destination" "$actual_size" "$actual_sha" >>"$RUN/host-logs/download-report.tsv"
done < <(tail -n +2 "$MANIFEST")
printf 'planned_bytes=14903022013\nactual_bytes=14903022013\nsession_bytes=%s\nasset_count=1\n' "$session_bytes" >"$RUN/host-logs/download-accounting.txt"

while IFS=$'\t' read -r destination expected_size expected_sha; do
  test "$(stat -c %s "$destination")" = "$expected_size"
  test "$(sha256sum "$destination" | awk '{print $1}')" = "$expected_sha"
done < <(tail -n +2 "$SHARED")
sha256sum $(tail -n +2 "$SHARED" | cut -f1) >"$RUN/host-logs/11_shared_dependency_hashes.txt"

cp /home/straughter/wd-ycjg-run/outputs/create/wd_ycjg_create.mp4 "$RUN/inputs/control.mp4"
test "$(sha256sum "$RUN/inputs/control.mp4" | awk '{print $1}')" = 1fb5689ac1647dda8ddd0806981eb0ee93a2ca641956ea3848fce65aad817a2a
ffmpeg -nostdin -v error -y -i "$RUN/inputs/control.mp4" -update 1 -frames:v 1 "$RUN/inputs/reference.png"
ffmpeg -nostdin -v error -y -i "$RUN/inputs/control.mp4" -vf "select=eq(n\,4)" -frames:v 1 "$RUN/inputs/alternate-reference.png"
ffmpeg -nostdin -v error -y -i "$RUN/inputs/control.mp4" -vf "eq=brightness=0.25" -c:v libx264 -pix_fmt yuv420p -an "$RUN/inputs/control-mask.mp4"
sha256sum "$RUN/inputs/control.mp4" "$RUN/inputs/reference.png" "$RUN/inputs/alternate-reference.png" "$RUN/inputs/control-mask.mp4" >"$RUN/host-logs/12_input_hashes.txt"

git -C "$LIVE" worktree add --detach "$SOURCE" 4c93b64a47b5b0a915f2abec2ce754be98227150 >"$RUN/host-logs/13_worktree_deploy.txt" 2>&1
ln -s "$LIVE/ckpts" "$SOURCE/ckpts"
test "$(git -C "$SOURCE" rev-parse HEAD)" = 4c93b64a47b5b0a915f2abec2ce754be98227150
test "$(git -C "$SOURCE" status --porcelain=v1)" = "?? ckpts"
df -B1 "$LIVE" >"$RUN/host-logs/14_disk_after_download.txt"
printf 'DOWNLOAD_PREFLIGHT_PASS\n'
