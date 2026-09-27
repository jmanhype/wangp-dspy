#!/bin/bash
set -euo pipefail

LIVE=/home/straughter/Wan2GP
SOURCE=/home/straughter/Wan2GP-story-WD-m25k
RUN=/home/straughter/wd-m25k-run
PY=$LIVE/venv/bin/python

test "$(hostname)" = straughter-Z690-Steel-Legend
test "$(git -C "$SOURCE" rev-parse HEAD)" = 4c93b64a47b5b0a915f2abec2ce754be98227150
test "$(git -C "$SOURCE" status --porcelain=v1)" = "?? ckpts"
test "$(readlink "$SOURCE/ckpts")" = "$LIVE/ckpts"
test "$(sha256sum "$RUN/inputs/kfi-first-frame.png" | awk '{print $1}')" = cef70dbe1d40dc26acd19109f01d62e19197fc580e88d69b52a4624cc7dc98c7
test "$(sha256sum "$RUN/inputs/audio-first-frame.png" | awk '{print $1}')" = 82e5cb5509832944e00615123f999297106b21ad1e8191cbdf63a42b81ca2876

free=$(df -B1 "$RUN" | awk 'NR==2 {print $4}')
test "$free" -ge 20000000000
gpu_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
test "$gpu_used" -le 1000

"$PY" -m pip check >"$RUN/host-logs/13_python_pip_check_advisory.txt" 2>&1 || true
{
  date -u +%Y-%m-%dT%H:%M:%SZ
  git -C "$SOURCE" rev-parse HEAD
  git -C "$SOURCE" status --porcelain=v1
  df -B1 "$RUN"
  nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits
  printf '%s\n' 'pip_check=advisory_only_existing_environment_conflicts_no_dependency_mutation'
  printf '%s\n' 'offline=forced'
  printf '%s\n' 'planned_download_bytes=0'
} >"$RUN/host-logs/16_resume_preflight.txt"
printf 'RESUME_PREFLIGHT_PASS\n'
