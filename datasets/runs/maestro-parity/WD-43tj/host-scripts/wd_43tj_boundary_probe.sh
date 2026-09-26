#!/bin/bash
set -uo pipefail

WAN2GP=/home/straughter/Wan2GP
MAESTRO=/mnt/bulk/straughter/Maestro/app

{
  date -u +%Y-%m-%dT%H:%M:%SZ
  hostname
  printf '%s\n' '--- all current-tree TaoMate matches (context) ---'
  grep -R -I -n -i 'taomate' "$WAN2GP" "$MAESTRO" \
    --exclude='*.safetensors' --exclude='*.pth' --exclude='*.bin' \
    --exclude='*.mp4' --exclude='*.wav' --exclude='*.png' --exclude='*.jpg' \
    --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=node_modules
  grep_code=$?
  printf 'all_matches_grep_exit=%s\n' "$grep_code"
  printf '%s\n' '--- TaoMate host-implementation search ---'
  grep -R -I -n -i 'taomate' \
    "$WAN2GP/models" "$WAN2GP/shared" "$WAN2GP/wgp.py" \
    "$WAN2GP/defaults" "$WAN2GP/profiles" "$MAESTRO" \
    --exclude='*.safetensors' --exclude='*.pth' --exclude='*.bin' \
    --exclude='*.mp4' --exclude='*.wav' --exclude='*.png' --exclude='*.jpg' \
    --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=node_modules
  host_grep_code=$?
  printf 'host_grep_exit=%s\n' "$host_grep_code"
  sha256sum "$WAN2GP/wd-dmf2/repo/predict/video_capabilities.py" || true
  printf '%s\n' '--- TaoMate filename search ---'
  find "$WAN2GP" "$MAESTRO" -iname '*taomate*' -print 2>/dev/null
  find_code=$?
  printf 'find_exit=%s match_count=' "$find_code"
  find "$WAN2GP" "$MAESTRO" -iname '*taomate*' -print 2>/dev/null | wc -l
  printf '%s\n' '--- checked-out tree identities ---'
  git -C "$WAN2GP" rev-parse HEAD 2>/dev/null || true
  git -C "$WAN2GP" status --short 2>/dev/null | head -20 || true
  git -C "$MAESTRO" rev-parse HEAD 2>/dev/null || true
  git -C "$MAESTRO" status --short 2>/dev/null | head -20 || true
  printf '%s\n' '--- host state ---'
  nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader
  nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
} | tee /tmp/wd_43tj_boundary_probe.txt
