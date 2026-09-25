#!/usr/bin/env bash
set -euo pipefail

printf 'user='; id -un
printf 'host='; hostname
printf 'kernel='; uname -sr
printf 'disk_root_bytes='; df -B1 --output=avail /
printf 'disk_wgp_bytes='; df -B1 --output=avail /home/straughter/Wan2GP
printf 'gpu\n'
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits
printf 'gpu_processes\n'
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader,nounits || true
printf 'vibevoice_7b\n'
du -sb /mnt/bulk/straughter/models/VibeVoice-7B-hf
find /mnt/bulk/straughter/models/VibeVoice-7B-hf -maxdepth 1 -type f -printf '%f\n' | sort
printf 'vibevoice_large\n'
du -sb /mnt/bulk/straughter/models/VibeVoice-Large
find /mnt/bulk/straughter/models/VibeVoice-Large -maxdepth 1 -type f -printf '%f\n' | sort
printf 'python_environments\n'
for python in /home/straughter/vb7-venv/bin/python /home/straughter/Wan2GP/venv/bin/python; do
  if [[ -x "$python" ]]; then
    printf '%s: ' "$python"
    "$python" -I -c 'import json,platform,sys; print(json.dumps({"resolved_python":sys.executable,"python_implementation":platform.python_implementation(),"python_version":platform.python_version()}))'
  else
    printf '%s: absent\n' "$python"
  fi
done
printf 'chatterbox_candidates\n'
find /home/straughter/Wan2GP /mnt/bulk/straughter/models -maxdepth 5 \( -iname '*chatterbox*' -o -iname '*t3*' \) -print 2>/dev/null | sort | head -200
printf 'chatterbox_imports\n'
for python in /home/straughter/vb7-venv/bin/python /home/straughter/Wan2GP/venv/bin/python; do
  if [[ -x "$python" ]]; then
    printf '%s: ' "$python"
    "$python" -I -c 'import importlib.util; print(importlib.util.find_spec("chatterbox_tts"))' || true
  fi
done
printf 'wgp_processes\n'
ps -eo pid,ppid,etimes,cmd --sort=pid | grep -E 'Wan2GP|wd_[a-z0-9_]+|chatterbox|vibevoice|llama-server' | grep -v grep || true
