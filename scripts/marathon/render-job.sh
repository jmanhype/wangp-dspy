#!/usr/bin/env bash
# Run one marathon render with the configured Wan2GP interpreter.
set -u
if [ "$#" -ne 4 ]; then
  printf '%s\n' 'usage: render-job.sh WGP_ROOT WGP_PYTHON SETTINGS LOG' >&2
  exit 2
fi
WGP_ROOT=$1
WGP_PYTHON=$2
SETTINGS=$3
LOG=$4
cd "$WGP_ROOT" || exit 1
exec "$WGP_PYTHON" wgp.py --process "$SETTINGS" --profile 2 --attention sdpa > "$LOG" 2>&1
