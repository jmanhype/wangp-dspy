#!/usr/bin/env bash
set -Eeuo pipefail

lane=/home/straughter/Wan2GP/wd-7fvx
server=/home/straughter/llama.cpp/build/bin/llama-server
model=/mnt/bulk/home/straughter/models/qwen38-27b-uncensored/Q4_K_M.gguf
projector=/mnt/bulk/home/straughter/models/qwen38-27b-uncensored/mmproj-f16.gguf

if curl -fsS --max-time 2 http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "judge already running"
  exit 0
fi

nohup "$server" -m "$model" --mmproj "$projector" -ngl 99 -np 1 -c 20480 \
  --port 8000 --host 127.0.0.1 --media-path "$lane" \
  > "$lane/judge-server.log" 2>&1 < /dev/null &
echo $! > "$lane/judge-server.pid"
for _ in $(seq 1 180); do
  if curl -fsS --max-time 2 http://127.0.0.1:8000/health > "$lane/judge-health.json" 2>/dev/null; then
    echo "judge ready pid=$(cat "$lane/judge-server.pid")"
    exit 0
  fi
  pid=$(cat "$lane/judge-server.pid")
  if ! kill -0 "$pid" 2>/dev/null; then
    cat "$lane/judge-server.log" >&2
    exit 2
  fi
  sleep 2
done
cat "$lane/judge-server.log" >&2
exit 3
