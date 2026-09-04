#!/usr/bin/env bash
# QUEUE FEEDER — copies QUEUE/*.json into NEXT_JOB.json when idle, every 2 min.
set -u
M=/home/straughter/marathon
while true; do
  if [ ! -f "$M/NEXT_JOB.json" ]; then
    N=$(ls "$M/QUEUE" 2>/dev/null | head -1)
    if [ -n "$N" ]; then
      mv "$M/QUEUE/$N" "$M/NEXT_JOB.json"
      echo "[$(date +%H:%M:%S)] fed $N from QUEUE" >> "$M/driver.log"
    fi
  fi
  sleep 120
done
