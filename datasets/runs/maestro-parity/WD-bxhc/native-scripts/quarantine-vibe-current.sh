#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/straughter/wangp-dspy-vibevoice-20260916/datasets/runs/maestro-parity/WD-bxhc
PRESERVED="$ROOT/${1:?destination-suffix}"
mkdir -p "$PRESERVED"
for name in \
  wd_bxhc_vibevoice_speech.wav \
  wd_bxhc_vibevoice_speech.prepared.wav \
  wd_bxhc_vibevoice_speech.wav.vibevoice.json \
  wd_bxhc_vibevoice_clone_one.wav \
  wd_bxhc_vibevoice_clone_one.prepared.wav \
  wd_bxhc_vibevoice_clone_one.wav.vibevoice.json \
  wd_bxhc_vibevoice_clone_two.wav \
  wd_bxhc_vibevoice_clone_two.prepared.wav \
  wd_bxhc_vibevoice_clone_two.wav.vibevoice.json; do
  if [[ -e "$ROOT/outputs/$name" ]]; then
    mv "$ROOT/outputs/$name" "$PRESERVED/$name"
  fi
done
printf 'destination=%s quarantined_files=%s\n' "$PRESERVED" "$(find "$PRESERVED" -maxdepth 1 -type f | wc -l)"
