#!/usr/bin/env bash
set -Eeuo pipefail
date -u +%Y-%m-%dT%H:%M:%SZ
df -B1 /
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
ps -eo pid,stat,cmd | grep -E 'wd_r81u|rife|realesrgan|ffmpeg' | grep -v grep || true
