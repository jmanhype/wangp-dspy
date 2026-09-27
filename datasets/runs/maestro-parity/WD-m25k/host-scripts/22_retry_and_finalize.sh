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

mkdir -p "$RUN/mapping-error"
if test -d "$RUN/outputs/kfi_extend"; then mv "$RUN/outputs/kfi_extend" "$RUN/mapping-error/kfi_extend_mislabeled"; fi
if test -d "$RUN/outputs/kfi_edit"; then mv "$RUN/outputs/kfi_edit" "$RUN/mapping-error/kfi_edit_mislabeled"; fi

record_output kfi_repaint "$(find "$RUN/outputs/render-batch" -maxdepth 1 -type f -name '*seed3103*.mp4' -print -quit)"
record_output audio_repaint "$(find "$RUN/outputs/render-batch" -maxdepth 1 -type f -name '*seed3106*.mp4' -print -quit)"
audio_outpaint=$(find "$RUN/boundaries/audio-outpaint-probe" -maxdepth 1 -type f -name '*.mp4' -print -quit)
if test -n "$audio_outpaint"; then record_output audio_outpaint "$audio_outpaint"; fi

out=$RUN/outputs/render-batch-retry
mkdir -p "$out"
snapshot "$LOG/render-batch-retry.host-before.txt"
printf '%s\n' "$PY" wgp.py --process "$SETTINGS/render-batch-retry.json" --profile 3 --attention sdpa --output-dir "$out" >"$LOG/render-batch-retry.argv.txt"
(
  cd "$SOURCE"
  PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    timeout 4800 "$PY" wgp.py --process "$SETTINGS/render-batch-retry.json" --profile 3 --attention sdpa --output-dir "$out" >"$LOG/render-batch-retry.render.log" 2>&1
)
retry_code=$?
printf '%s\n' "$retry_code" >"$LOG/render-batch-retry.exit"
for pair in kfi_extend:3111 kfi_edit:3112 audio_extend:3113 audio_retake:3114; do
  name=${pair%%:*}
  seed=${pair##*:}
  src=$(find "$out" -maxdepth 1 -type f -name "*seed${seed}*.mp4" -print -quit)
  if test -n "$src"; then record_output "$name" "$src"; fi
done
snapshot "$LOG/render-batch-retry.host-after.txt"
printf 'render_batch_retry_exit=%s\n' "$retry_code" | tee -a "$LOG/render-status.txt"

for name in kfi_upscale audio_upscale; do
  file=${name/_/-}
  out=$RUN/outputs/$name
  mkdir -p "$out"
  snapshot "$LOG/$name.host-before.txt"
  printf '%s\n' "$PY" wgp.py --process "$SETTINGS/$file.json" --output-dir "$out" >"$LOG/$name.argv.txt"
  (
    cd "$SOURCE"
    PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
      timeout 240 "$PY" wgp.py --process "$SETTINGS/$file.json" --output-dir "$out" >"$LOG/$name.render.log" 2>&1
  )
  code=$?
  printf '%s\n' "$code" >"$LOG/$name.exit"
  newest=$(find "$out" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
  if test -n "$newest"; then record_output "$name" "$newest"; fi
  snapshot "$LOG/$name.host-after.txt"
  printf 'postprocess=%s exit=%s output=%s\n' "$name" "$code" "$newest" | tee -a "$LOG/render-status.txt"
done

snapshot "$LOG/retry-final-host.txt"
find "$RUN/outputs" -type f | sort >"$LOG/final-output-inventory.txt"
