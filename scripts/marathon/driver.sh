#!/usr/bin/env bash
# MARATHON DRIVER v1 — runs until stopped. Each stage logs to /home/straughter/marathon/.
set -u
M=/home/straughter/marathon
mkdir -p "$M"
log(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$M/driver.log"; }

log "MARATHON START"

# --- Stage 0: wait for Devil's Grandma render to finish ---
while pgrep -f "wgp.py --process" >/dev/null 2>&1; do sleep 60; done
log "Devil's Grandma render process ended"
NEW="/home/straughter/Wan2GP/outputs/$(ls -t /home/straughter/Wan2GP/outputs/ | head -1)"
cp "$NEW" "$M/devilgrandma_15s.mp4" && log "Grandma saved: $(basename "$NEW")"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$M/devilgrandma_15s.mp4" >> "$M/driver.log" 2>&1

# --- Stage 1: disk triage (keep root under 85%) ---
USED=$(df / | awk 'NR==2{gsub("%",""); print $5}')
if [ "$USED" -gt 85 ]; then
  log "disk at ${USED}% — triaging old outputs"
  # move chain6/scratch mp4s older runs to bulk if writable, else delete dupes in outputs
  ls /home/straughter/Wan2GP/outputs/*.mp4 2>/dev/null | head -n -5 | while read f; do
    gzip -9 "$f" && log "compressed $(basename "$f")"
  done
fi
log "disk now: $(df / | awk 'NR==2{print $5}')"

# --- Stage 2: production queue (placeholder loop; premise configs appended by agent) ---
log "entering production queue"
while true; do
  if [ -f "$M/NEXT_JOB.json" ]; then
    python3 - << 'PYEOF'
import json, subprocess
M="/home/straughter/marathon"
job=json.load(open(f"{M}/NEXT_JOB.json"))
RUN="/home/straughter/wangp-dspy-fresh/runs/directpin/settings.json"
d=json.load(open(RUN)); d.update(job); json.dump(d,open(RUN,"w"),indent=2)
PYEOF
    log "rendering premise: $(python3 -c "import json;print(json.load(open('$M/NEXT_JOB.json')).get('premise','?'))")"
    cd /home/straughter/Wan2GP
    ./venv/bin/python wgp.py --process /home/straughter/wangp-dspy-fresh/runs/directpin/settings.json --profile 2 --attention sdpa > "$M/render.log" 2>&1
    RC=$?
    NEW="/home/straughter/Wan2GP/outputs/$(ls -t /home/straughter/Wan2GP/outputs/ | head -1)"
    OUT="$M/$(python3 -c "import json;print(json.load(open('$M/NEXT_JOB.json')).get('premise','out'))").mp4"
    [ $RC -eq 0 ] && cp "$NEW" "$OUT" && log "DONE -> $OUT"
    [ $RC -ne 0 ] && log "RENDER FAILED rc=$RC — see $M/render.log"
    mv "$M/NEXT_JOB.json" "$M/done_$(date +%s).json" 2>/dev/null
  else
    sleep 120
  fi
done
