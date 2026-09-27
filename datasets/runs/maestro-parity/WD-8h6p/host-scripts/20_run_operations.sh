#!/bin/bash
set -uo pipefail

SOURCE=/home/straughter/Wan2GP-story-WD-8h6p
RUN=/home/straughter/wd-8h6p-run
PY=/home/straughter/Wan2GP/venv/bin/python
LOG=$RUN/host-logs

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

record_output() {
  name=$1
  src=$2
  out=$RUN/outputs/$name
  mkdir -p "$out"
  test -s "$src"
  cp "$src" "$out/wd_8h6p_${name}.mp4"
  sha256sum "$out/wd_8h6p_${name}.mp4" >"$out/wd_8h6p_${name}.sha256"
  ffprobe -v error -show_streams -show_format -of json "$out/wd_8h6p_${name}.mp4" >"$out/wd_8h6p_${name}.ffprobe.json"
  ffmpeg -nostdin -v error -y -i "$out/wd_8h6p_${name}.mp4" -vf fps=6,scale=240:-1,tile=4x2 -frames:v 1 "$out/contact-sheet.jpg"
  ffmpeg -nostdin -v error -y -i "$out/wd_8h6p_${name}.mp4" -update 1 -frames:v 1 "$out/first-frame.png"
  printf 'source=%s\nfinal=%s\n' "$src" "$out/wd_8h6p_${name}.mp4" >"$out/output-path.txt"
}

run_native() {
  name=$1
  timeout_s=$2
  out=$RUN/boundaries/$name
  mkdir -p "$out"
  snapshot "$LOG/$name.host-before.txt"
  printf '%s\n' "$PY" wgp.py --process "$RUN/settings/$name.json" --profile 3 --attention sdpa --output-dir "$out" >"$LOG/$name.argv.txt"
  (
    cd "$SOURCE"
    PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
      timeout "$timeout_s" "$PY" wgp.py --process "$RUN/settings/$name.json" --profile 3 --attention sdpa --output-dir "$out" >"$LOG/$name.render.log" 2>&1
  )
  code=$?
  printf '%s\n' "$code" >"$LOG/$name.exit"
  find "$out" -maxdepth 1 -type f -printf '%s %p\n' | sort >"$LOG/$name.output-inventory.txt"
  snapshot "$LOG/$name.host-after.txt"
  printf 'native=%s exit=%s\n' "$name" "$code" | tee -a "$LOG/render-status.txt"
}

mkdir -p "$RUN/outputs" "$RUN/boundaries"
snapshot "$LOG/batch-host-before.txt"
for name in extend-probe blend-probe retake-probe edit-probe repaint-probe recast-probe; do
  run_native "$name" 420
done

out=$RUN/outputs/upscale
mkdir -p "$out"
snapshot "$LOG/upscale.host-before.txt"
printf '%s\n' "$PY" wgp.py --process "$RUN/settings/upscale.json" --output-dir "$out" >"$LOG/upscale.argv.txt"
(
  cd "$SOURCE"
  PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    timeout 300 "$PY" wgp.py --process "$RUN/settings/upscale.json" --output-dir "$out" >"$LOG/upscale.render.log" 2>&1
)
code=$?
printf '%s\n' "$code" >"$LOG/upscale.exit"
newest=$(find "$out" -maxdepth 1 -type f -name '*.mp4' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
if test -n "$newest"; then record_output upscale "$newest"; fi
snapshot "$LOG/upscale.host-after.txt"
printf 'postprocess=upscale exit=%s output=%s\n' "$code" "$newest" | tee -a "$LOG/render-status.txt"
snapshot "$LOG/batch-host-after.txt"
find "$RUN" -type f | sort >"$LOG/final-inventory.txt"
