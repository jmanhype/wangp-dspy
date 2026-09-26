#!/usr/bin/env bash
set -Eeuo pipefail

printf 'user=%s host=%s\n' "$(id -un)" "$(hostname)"
printf 'wgp_root=%s\n' "$(readlink -f /home/straughter/Wan2GP)"
df -B1 / | tail -1
printf '%s\n' 'llama_server_processes:'
pgrep -af llama-server || true
printf '%s\n' 'gpu:'
nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader
printf 'whisper=%s\n' "$(command -v whisper || true)"
printf 'ffmpeg=%s\n' "$(command -v ffmpeg || true)"
printf '%s\n' 'python_candidates:'
for python in /home/straughter/Wan2GP/.venv/bin/python /home/straughter/wangp-dspy/.venv/bin/python python3; do
  if command -v "$python" >/dev/null 2>&1; then
    "$python" -c 'import sys; print(sys.executable, sys.version.split()[0])' || true
  fi
done
printf '%s\n' 'required_assets:'
find /home/straughter -type f \( -name small.pt -o -name syncnet_v2.model \) -printf '%p %s\n' 2>/dev/null | sort
