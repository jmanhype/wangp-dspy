#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/straughter/wangp-dspy-vibevoice-20260916/datasets/runs/maestro-parity/WD-bxhc
PRESERVED="$ROOT/attempt-10-preserved"
mkdir -p "$PRESERVED"
if [[ -f "$ROOT/vibevoice-custom-report.json" ]]; then
  mv "$ROOT/vibevoice-custom-report.json" "$PRESERVED/vibevoice-custom-report.json"
fi
find "$ROOT/outputs" -maxdepth 1 -type f -name 'wd_bxhc_vibevoice_speech.attempt-*' -exec mv '{}' "$PRESERVED/" \;
printf 'destination=%s quarantined_files=%s\n' "$PRESERVED" "$(find "$PRESERVED" -maxdepth 1 -type f | wc -l)"
