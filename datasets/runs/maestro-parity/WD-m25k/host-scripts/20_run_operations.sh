#!/bin/bash
set -uo pipefail

SOURCE=/home/straughter/Wan2GP-story-WD-m25k
RUN=/home/straughter/wd-m25k-run
PY=/home/straughter/Wan2GP/venv/bin/python
LOG=$RUN/host-logs
SETTINGS=$RUN/settings

snapshot() {
  file=$1
  {
    date -u +%Y-%m-%dT%H:%M:%SZ
    git -C "$SOURCE" rev-parse HEAD
    git -C "$SOURCE" status --porcelain=v1
    df -B1 "$RUN"
    nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
  } >"$file"
}

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

run_probe() {
  name=$1
  timeout_s=${2:-180}
  out=$RUN/boundaries/$name
  mkdir -p "$out"
  snapshot "$LOG/$name.host-before.txt"
  printf '%s\n' "$PY" wgp.py --process "$SETTINGS/$name.json" --profile 3 --attention sdpa --output-dir "$out" >"$LOG/$name.argv.txt"
  (
    cd "$SOURCE"
    PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
      timeout "$timeout_s" "$PY" wgp.py --process "$SETTINGS/$name.json" --profile 3 --attention sdpa --output-dir "$out" >"$LOG/$name.render.log" 2>&1
  )
  code=$?
  printf '%s\n' "$code" >"$LOG/$name.exit"
  snapshot "$LOG/$name.host-after.txt"
  find "$out" -maxdepth 1 -type f -printf '%s %p\n' | sort >"$LOG/$name.output-inventory.txt"
  printf 'probe=%s exit=%s\n' "$name" "$code"
}

mkdir -p "$RUN/outputs" "$RUN/boundaries" "$LOG"
snapshot "$LOG/batch-host-before.txt"

for probe in kfi-create-probe kfi-blend-probe kfi-outpaint-probe kfi-recast-probe audio-create-probe audio-blend-probe audio-outpaint-probe audio-recast-probe; do
  run_probe "$probe" 240
done

find "$RUN/boundaries" -type f -name '*.mp4' -printf '%s %p\n' | sort >"$LOG/boundary-output-inventory.txt"

out=$RUN/outputs/render-batch
mkdir -p "$out"
find "$out" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort >"$LOG/render-batch-before.txt"
printf '%s\n' "$PY" wgp.py --process "$SETTINGS/render-batch.json" --profile 3 --attention sdpa --output-dir "$out" >"$LOG/render-batch.argv.txt"
(
  cd "$SOURCE"
  PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    timeout 5400 "$PY" wgp.py --process "$SETTINGS/render-batch.json" --profile 3 --attention sdpa --output-dir "$out" >"$LOG/render-batch.render.log" 2>&1
)
batch_code=$?
printf '%s\n' "$batch_code" >"$LOG/render-batch.exit"
find "$out" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort >"$LOG/render-batch-after.txt"
mapfile -t generated < <(find "$out" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort -nr | head -6 | cut -d' ' -f2-)
if test "${#generated[@]}" -ge 1; then
  i=0
  for name in kfi_extend kfi_edit kfi_repaint audio_extend audio_retake audio_repaint; do
    i=$((i+1))
    if test "$i" -le "${#generated[@]}"; then record_output "$name" "${generated[$((i-1))]}"; fi
  done
fi
printf 'render_batch_exit=%s outputs=%s\n' "$batch_code" "${#generated[@]}" | tee "$LOG/render-status.txt"

for name in kfi_upscale audio_upscale; do
  out=$RUN/outputs/$name
  mkdir -p "$out"
  snapshot "$LOG/$name.host-before.txt"
  printf '%s\n' "$PY" wgp.py --process "$SETTINGS/${name/_/-}.json" --output-dir "$out" >"$LOG/$name.argv.txt" 2>/dev/null || printf '%s\n' "$PY" wgp.py --process "$SETTINGS/$name.json" --output-dir "$out" >"$LOG/$name.argv.txt"
  (
    cd "$SOURCE"
    PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
      timeout 240 "$PY" wgp.py --process "$SETTINGS/$name.json" --output-dir "$out" >"$LOG/$name.render.log" 2>&1
  )
  code=$?
  printf '%s\n' "$code" >"$LOG/$name.exit"
  newest=$(find "$out" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
  if test -n "$newest"; then record_output "$name" "$newest"; fi
  snapshot "$LOG/$name.host-after.txt"
  printf 'postprocess=%s exit=%s output=%s\n' "$name" "$code" "$newest" | tee -a "$LOG/render-status.txt"
done

snapshot "$LOG/batch-host-after.txt"
find "$RUN/outputs" -type f | sort >"$LOG/final-output-inventory.txt"
