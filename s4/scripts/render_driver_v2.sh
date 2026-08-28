#!/bin/bash
# S4 STEP 3b — render driver v2: sequential, GPU-free preflight before each cut.
# Cuts 1 and 3 are already collected; this renders the missing ones only.
set -u
SSH="ssh -o ConnectTimeout=15 -o BatchMode=yes 3090"
VENV_PY=/home/straughter/Wan2GP/venv/bin/python
WGP=/home/straughter/Wan2GP/wgp.py

gpu_free() {
  # returns 0 if < 3000 MiB used (server baseline ~500MiB)
  local m
  m=$($SSH 'nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits')
  [ "$m" -lt 3000 ]
}

wait_gpu() {
  for i in $(seq 1 60); do
    gpu_free && return 0
    sleep 15
  done
  echo "GPU_STILL_BUSY after 15min"; return 1
}

render_cut() {
  CUT=$1
  $SSH "ls /tmp/s4/render-out/cut${CUT}.mp4 >/dev/null 2>&1" && { echo "SKIP cut${CUT} (already collected)"; return 0; }
  echo "=== RENDER cut${CUT} start $(date -u +%H:%M:%S)"
  wait_gpu || exit 8
  $SSH "cd /home/straughter/Wan2GP && timeout 2100 $VENV_PY $WGP --process /tmp/s4/jobs/cut${CUT}_settings.json --profile 3 --attention sdpa > /tmp/s4/jobs/cut${CUT}_render.log 2>&1; echo wgp_exit=\$?"
  # collect newest mp4 from wgp outputs into render-out
  $SSH "latest=\$(ls -t /home/straughter/Wan2GP/outputs/*.mp4 2>/dev/null | head -1); if [ -n \"\$latest\" ]; then cp \"\$latest\" /tmp/s4/render-out/cut${CUT}.mp4 && rm -f \"\$latest\"; ffprobe -v error -show_entries format=duration -of csv=p=0 /tmp/s4/render-out/cut${CUT}.mp4; else echo NO_OUTPUT_cut${CUT}; fi"
  echo "=== RENDER cut${CUT} done $(date -u +%H:%M:%S)"
}

for c in 2 4 5 6; do
  render_cut $c
done
echo "ALL RENDERS COMPLETE $(date -u +%H:%M:%S)"
