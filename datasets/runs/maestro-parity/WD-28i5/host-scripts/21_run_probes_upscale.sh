#!/bin/bash
set -uo pipefail

SOURCE=/home/straughter/Wan2GP-story-WD-28i5
RUN=/home/straughter/wd-28i5-run
PY=/home/straughter/Wan2GP/venv/bin/python
LOG=$RUN/host-logs

snapshot() {
  {
    date -u +%Y-%m-%dT%H:%M:%SZ
    git -C "$SOURCE" rev-parse HEAD
    git -C "$SOURCE" status --porcelain=v1
    df -B1 "$RUN"
    nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
  } >"$1"
}

record_output() {
  name=$1
  src=$2
  out=$RUN/outputs/$name
  mkdir -p "$out"
  test -s "$src"
  cp "$src" "$out/wd_28i5_${name}.mp4"
  sha256sum "$out/wd_28i5_${name}.mp4" >"$out/wd_28i5_${name}.sha256"
  ffprobe -v error -show_streams -show_format -of json "$out/wd_28i5_${name}.mp4" >"$out/wd_28i5_${name}.ffprobe.json"
  ffmpeg -nostdin -v error -y -i "$out/wd_28i5_${name}.mp4" -vf fps=3,scale=240:-1,tile=3x3 -frames:v 1 "$out/contact-sheet.jpg"
  ffmpeg -nostdin -v error -y -i "$out/wd_28i5_${name}.mp4" -update 1 -frames:v 1 "$out/first-frame.png"
  printf 'source=%s\nfinal=%s\n' "$src" "$out/wd_28i5_${name}.mp4" >"$out/output-path.txt"
}

snapshot "$LOG/probes.host-before.txt"
out=$RUN/boundaries/probe-batch
mkdir -p "$out"
printf '%s\n' "$PY" wgp.py --process "$RUN/settings/probe-batch.json" --profile 3 --attention sdpa --output-dir "$out" >"$LOG/probe-batch.argv.txt"
(
  cd "$SOURCE"
  PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    timeout 3600 "$PY" wgp.py --process "$RUN/settings/probe-batch.json" --profile 3 --attention sdpa --output-dir "$out" >"$LOG/probe-batch.render.log" 2>&1
)
code=$?
printf '%s\n' "$code" >"$LOG/probe-batch.exit"
find "$out" -maxdepth 1 -type f -printf '%s %p\n' | sort >"$LOG/probe-batch.output-inventory.txt"
for pair in extend:3602 blend:3603 retake:3604 edit:3605 outpaint:3606 repaint:3607 recast:3608; do
  name=${pair%%:*}; seed=${pair##*:}
  src=$(find "$out" -maxdepth 1 -type f -name "*seed${seed}*.mp4" -print -quit)
  if test -n "$src"; then record_output "$name" "$src"; fi
done
snapshot "$LOG/probes.host-after.txt"
printf 'probe_batch_exit=%s\n' "$code" | tee "$LOG/remaining-status.txt"

out=$RUN/outputs/upscale
mkdir -p "$out"
snapshot "$LOG/upscale.host-before.txt"
printf '%s\n' "$PY" wgp.py --process "$RUN/settings/upscale.json" --output-dir "$out" >"$LOG/upscale.argv.txt"
(
  cd "$SOURCE"
  PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    timeout 300 "$PY" wgp.py --process "$RUN/settings/upscale.json" --output-dir "$out" >"$LOG/upscale.render.log" 2>&1
)
upscale_code=$?
printf '%s\n' "$upscale_code" >"$LOG/upscale.exit"
newest=$(find "$out" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
if test -n "$newest"; then record_output upscale "$newest"; fi
snapshot "$LOG/upscale.host-after.txt"
printf 'upscale_exit=%s output=%s\n' "$upscale_code" "$newest" | tee -a "$LOG/remaining-status.txt"

snapshot "$LOG/remaining.host-after.txt"
git -C "$SOURCE" restore -- shared/gradio/hierarchy_selector/hierarchy_selector.pyi 2>/dev/null || true
git -C "$SOURCE" status --porcelain=v1 >"$LOG/remaining.source-final-status.txt"
find "$RUN/outputs" -type f | sort >"$LOG/remaining.output-inventory.txt"
cat "$LOG/remaining-status.txt"
