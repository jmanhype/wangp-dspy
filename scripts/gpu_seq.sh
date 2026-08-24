#!/bin/bash
# GPU sequencing for pipeline cycles (runbook discipline, scripted).
# The 27B critic and H3 renders cannot share 24GB — sequence them.
# Usage: gpu_seq.sh stop-critic|start-critic|status
set -e
QC_DIR=/home/straughter/qwen3vl-video
SERVER=/home/straughter/llama.cpp/build/bin/llama-server

case "$1" in
  stop-critic)
    ssh -o ConnectTimeout=15 3090 'pkill -f llama-server || true; sleep 3; nvidia-smi --query-gpu=memory.used --format=csv,noheader'
    ;;
  start-critic)
    ssh -o ConnectTimeout=15 3090 "cd $QC_DIR && nohup $SERVER \\
      -m qwen38-27b-Q4_K_M.gguf --mmproj mmproj.gguf \\
      -np 1 -c 20480 --port 8000 --host 127.0.0.1 \\
      --media-path $QC_DIR -v > server.log 2>&1 & echo starting"
    echo "waiting for model load (~60s)..."
    sleep 65
    ssh -o ConnectTimeout=15 3090 'curl -s -m 5 http://127.0.0.1:8000/health'
    ;;
  status)
    ssh -o ConnectTimeout=15 3090 'nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader; pgrep -x llama-server >/dev/null && echo "critic: up" || echo "critic: down"; pgrep -fx ".*python.*wgp.py.*--process.*" >/dev/null && echo "render: running" || echo "render: idle"'
    ;;
  *) echo "usage: $0 stop-critic|start-critic|status"; exit 1 ;;
esac
