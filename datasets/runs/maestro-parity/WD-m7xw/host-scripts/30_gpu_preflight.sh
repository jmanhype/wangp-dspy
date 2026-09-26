#!/bin/bash
set -euo pipefail
printf '%s\n' '=== time ==='
date -u +%Y-%m-%dT%H:%M:%SZ
printf '%s\n' '=== gpu ==='
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits
printf '%s\n' '=== compute_apps ==='
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
printf '%s\n' '=== blocking_processes ==='
ps -o pid,ppid,user,stat,lstart,cmd -p 3213164,3225057
printf '%s\n' '=== decision ==='
used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits)
printf 'memory.used_mib=%s\nmemory.free_mib=%s\n' "$used" "$free"
if test "$free" -lt 20000; then
  printf '%s\n' 'gpu_preflight=BLOCKED unauthorized unrelated llama-server occupies 18154 MiB; killing or restarting it is out of scope'
  exit 2
fi
printf '%s\n' 'gpu_preflight=PASS'
