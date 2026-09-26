#!/usr/bin/env bash
set -Eeuo pipefail

lane=/home/straughter/Wan2GP/wd-7fvx
pidfile=$lane/judge-server.pid
if [ ! -f "$pidfile" ]; then
  echo "judge pid file absent; no broad process mutation"
  exit 0
fi
pid=$(cat "$pidfile")
if kill -0 "$pid" 2>/dev/null; then
  kill "$pid"
  for _ in $(seq 1 30); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 1
  done
fi
if kill -0 "$pid" 2>/dev/null; then
  echo "judge pid $pid did not exit" >&2
  exit 2
fi
echo "judge stopped pid=$pid"
