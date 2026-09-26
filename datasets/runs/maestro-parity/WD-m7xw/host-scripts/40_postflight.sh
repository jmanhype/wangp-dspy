#!/bin/bash
set -euo pipefail
LIVE=/home/straughter/Wan2GP
SOURCE=/home/straughter/Wan2GP-story-WD-m7xw
RUN=/home/straughter/wd-m7xw-run
printf '%s\n' '=== time ==='
date -u +%Y-%m-%dT%H:%M:%SZ
printf '%s\n' '=== live ==='
printf 'head='; git -C "$LIVE" rev-parse HEAD
printf 'dirty_count='; git -C "$LIVE" status --porcelain=v1 | wc -l
printf 'dirty_identity='; git -C "$LIVE" status --porcelain=v1 | sha256sum | awk '{print $1}'
printf '%s\n' '=== isolated source ==='
printf 'head='; git -C "$SOURCE" rev-parse HEAD
printf 'dirty_count='; git -C "$SOURCE" status --porcelain=v1 | wc -l
printf 'dirty_identity='; git -C "$SOURCE" status --porcelain=v1 | sha256sum | awk '{print $1}'
printf 'status:'; git -C "$SOURCE" status --short
printf '%s\n' '=== run outputs ==='
find "$RUN/outputs" -type f -printf '%s %p\n' | sort
printf 'output_count='; find "$RUN/outputs" -type f | wc -l
printf '%s\n' '=== gpu ==='
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
