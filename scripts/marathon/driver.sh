#!/usr/bin/env bash
# MARATHON DRIVER v1 — runs until stopped. Each stage logs to the render host.
set -u
REPO=$("${0%/*}/repository-root.sh")
export PYTHONPATH="$REPO${PYTHONPATH:+:$PYTHONPATH}"
CONFIGURATION=$("$REPO/scripts/marathon/resolve-config.sh") || {
  printf '%s\n' "$CONFIGURATION" >&2
  exit 2
}
IFS=$'\t' read -r RENDER_TARGET WGP_ROOT WGP_PYTHON <<< "$CONFIGURATION"
if [ "$RENDER_TARGET" != "localhost" ]; then
  printf '%s\n' "configuration error: marathon driver is localhost-only; target ${RENDER_TARGET} would use ${WGP_ROOT} as a local path" >&2
  exit 2
fi
M=/home/straughter/marathon
mkdir -p "$M"
log(){
  printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" | tee -a "$M/driver.log"
}

log "MARATHON START"

# --- Stage 0: wait for Devil's Grandma render to finish ---
while pgrep -f "wgp.py --process" >/dev/null 2>&1; do sleep 60; done
log "Devil's Grandma render process ended"
NEW=$("$REPO/scripts/marathon/latest-output.py" "$WGP_ROOT/outputs") || exit 1
if cp "$NEW" "$M/devilgrandma_15s.mp4"; then
  log "Grandma saved: ${NEW##*/}"
fi
ffprobe -v error -show_entries format=duration -of csv=p=0 "$M/devilgrandma_15s.mp4" >> "$M/driver.log" 2>&1

# --- Stage 1: disk triage (keep root under 85%) ---
USED=$("$REPO/scripts/marathon/disk-usage-percent.sh")
if [ "$USED" -gt 85 ]; then
  log "disk at ${USED}% — triaging old outputs"
  "$REPO/scripts/marathon/triage-outputs.py" "$WGP_ROOT/outputs" 5
fi
CURRENT_USED=$("$REPO/scripts/marathon/disk-usage-percent.sh")
log "disk now: $CURRENT_USED%"

# --- Stage 2: production queue (placeholder loop; premise configs appended by agent) ---
log "entering production queue"
while true; do
  if [ -f "$M/NEXT_JOB.json" ]; then
    "$REPO/scripts/marathon/prepare-job.py" "$M/NEXT_JOB.json" /home/straughter/wangp-dspy-fresh/runs/directpin/settings.json
    PREMISE=$("$REPO/scripts/marathon/job-premise.py" "$M/NEXT_JOB.json")
    log "rendering premise: $PREMISE"
    "$REPO/scripts/marathon/render-job.sh" "$WGP_ROOT" "$WGP_PYTHON" /home/straughter/wangp-dspy-fresh/runs/directpin/settings.json "$M/render.log"
    RC=$?
    NEW=$("$REPO/scripts/marathon/latest-output.py" "$WGP_ROOT/outputs") || exit 1
    OUT="$M/$("$REPO/scripts/marathon/job-premise.py" "$M/NEXT_JOB.json").mp4"
    if [ "$RC" -eq 0 ]; then
      if cp "$NEW" "$OUT"; then
        log "DONE -> $OUT"
      fi
    else
      log "RENDER FAILED rc=$RC — see $M/render.log"
    fi
    mv "$M/NEXT_JOB.json" "$M/done_$(date +%s).json" 2>/dev/null
  else
    sleep 120
  fi
done
