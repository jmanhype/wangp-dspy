#!/bin/bash
set -uo pipefail

WAN2GP=/home/straughter/Wan2GP
MAESTRO=/mnt/bulk/straughter/Maestro/app

{
  date -u +%Y-%m-%dT%H:%M:%SZ
  hostname
  printf '%s\n' '--- active h3_outpaint runtime identity search ---'
  grep -R -I -n -i 'h3_outpaint' \
    "$WAN2GP/models" "$WAN2GP/shared" "$WAN2GP/wgp.py" \
    "$WAN2GP/defaults" "$WAN2GP/profiles" "$MAESTRO" \
    --exclude='*.safetensors' --exclude='*.pth' --exclude='*.bin' \
    --exclude='*.mp4' --exclude='*.wav' --exclude='*.png' --exclude='*.jpg' \
    --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=node_modules
  identity_code=$?
  printf 'active_identity_grep_exit=%s\n' "$identity_code"
  printf '%s\n' '--- active disabled control search ---'
  grep -R -I -n -E 'video_guide_outpainting|outpainting_quantize_margins' \
    "$WAN2GP/models/minimax_h3" "$WAN2GP/shared" "$WAN2GP/wgp.py" \
    --exclude-dir=.git --exclude-dir=__pycache__
  control_code=$?
  printf 'disabled_control_grep_exit=%s\n' "$control_code"
  printf '%s\n' '--- filename search ---'
  find "$WAN2GP" "$MAESTRO" -iname '*h3*outpaint*' -print 2>/dev/null
  printf 'filename_match_count='
  find "$WAN2GP" "$MAESTRO" -iname '*h3*outpaint*' -print 2>/dev/null | wc -l
  printf '%s\n' '--- broad planner-only context ---'
  grep -R -I -n -i 'h3_outpaint' "$WAN2GP" "$MAESTRO" \
    --exclude='*.safetensors' --exclude='*.pth' --exclude='*.bin' \
    --exclude='*.mp4' --exclude='*.wav' --exclude='*.png' --exclude='*.jpg' \
    --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=node_modules | head -50
  printf '%s\n' '--- hashes and tree identity ---'
  sha256sum "$WAN2GP/models/minimax_h3/minimax_h3_handler.py" "$WAN2GP/wgp.py"
  git -C "$WAN2GP" rev-parse HEAD 2>/dev/null || true
  git -C "$WAN2GP" status --short 2>/dev/null | head -20 || true
  git -C "$MAESTRO" rev-parse HEAD 2>/dev/null || true
  printf '%s\n' '--- host state ---'
  nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader
  nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
} | tee /tmp/wd_5k28_boundary_probe.txt
