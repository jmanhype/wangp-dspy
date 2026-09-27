#!/bin/bash
set -uo pipefail

SOURCE=/home/straughter/Wan2GP-story-WD-m25k
RUN=/home/straughter/wd-m25k-run
PY=/home/straughter/Wan2GP/venv/bin/python
LOG=$RUN/host-logs
SETTINGS=$RUN/settings

record_output() {
  name=$1
  src=$2
  out=$RUN/outputs/$name
  mkdir -p "$out"
  test -s "$src"
  cp "$src" "$out/wd_m25k_${name}.mp4"
  sha256sum "$out/wd_m25k_${name}.mp4" >"$out/wd_m25k_${name}.sha256"
  ffprobe -v error -show_streams -show_format -of json "$out/wd_m25k_${name}.mp4" >"$out/wd_m25k_${name}.ffprobe.json"
  ffmpeg -nostdin -v error -y -i "$out/wd_m25k_${name}.mp4" -vf fps=6,scale=240:-1,tile=4x2 -frames:v 1 "$out/contact-sheet.jpg"
  ffmpeg -nostdin -v error -y -i "$out/wd_m25k_${name}.mp4" -update 1 -frames:v 1 "$out/first-frame.png"
  printf 'source=%s\nfinal=%s\n' "$src" "$out/wd_m25k_${name}.mp4" >"$out/output-path.txt"
}

snapshot() {
  snapshot_file=$1
  {
    date -u +%Y-%m-%dT%H:%M:%SZ
    git -C "$SOURCE" rev-parse HEAD
    git -C "$SOURCE" status --porcelain=v1
    df -B1 "$RUN"
    nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
  } >"$snapshot_file"
}

for name in kfi_upscale audio_upscale; do
  settings_name=${name/_/-}
  out=$RUN/outputs/$name
  mkdir -p "$out"
  snapshot "$LOG/$name.retry-host-before.txt"
  printf '%s\n' "$PY" wgp.py --process "$SETTINGS/$settings_name.json" --output-dir "$out" >"$LOG/$name.retry.argv.txt"
  (
    cd "$SOURCE"
    PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
      timeout 240 "$PY" wgp.py --process "$SETTINGS/$settings_name.json" --output-dir "$out" >"$LOG/$name.retry.render.log" 2>&1
  )
  code=$?
  printf '%s\n' "$code" >"$LOG/$name.retry.exit"
  newest=$(find "$out" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
  if test -n "$newest"; then record_output "$name" "$newest"; fi
  snapshot "$LOG/$name.retry-host-after.txt"
  printf 'postprocess_retry=%s exit=%s output=%s\n' "$name" "$code" "$newest" | tee -a "$LOG/render-status.txt"
done

find "$RUN/outputs" -type f | sort >"$LOG/final-output-inventory.txt"
