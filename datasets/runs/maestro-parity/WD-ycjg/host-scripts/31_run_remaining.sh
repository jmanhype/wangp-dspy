#!/bin/bash
set -uo pipefail

SOURCE=/home/straughter/Wan2GP-story-WD-ycjg
RUN=/home/straughter/wd-ycjg-run
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
  cp "$src" "$out/wd_ycjg_${name}.mp4"
  sha256sum "$out/wd_ycjg_${name}.mp4" >"$out/wd_ycjg_${name}.sha256"
  ffprobe -v error -show_streams -show_format -of json "$out/wd_ycjg_${name}.mp4" >"$out/wd_ycjg_${name}.ffprobe.json"
  ffmpeg -nostdin -v error -y -i "$out/wd_ycjg_${name}.mp4" -vf fps=3,scale=240:-1,tile=3x3 -frames:v 1 "$out/contact-sheet.jpg"
  ffmpeg -nostdin -v error -y -i "$out/wd_ycjg_${name}.mp4" -update 1 -frames:v 1 "$out/first-frame.png"
  printf 'source=%s\nfinal=%s\n' "$src" "$out/wd_ycjg_${name}.mp4" >"$out/output-path.txt"
}

run_task() {
  name=$1
  timeout_s=$2
  out=$RUN/boundaries/$name
  mkdir -p "$out"
  snapshot "$LOG/$name.host-before.txt"
  printf '%s\n' "$PY" wgp.py --process "$RUN/settings/$name.json" --profile 3 --attention sdpa --output-dir "$out" >"$LOG/$name.argv.txt"
  (
    cd "$SOURCE"
    PYTHONPATH="$RUN/python-deps/packages:$SOURCE" PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True \
      HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
      timeout "$timeout_s" "$PY" wgp.py --process "$RUN/settings/$name.json" --profile 3 --attention sdpa --output-dir "$out" >"$LOG/$name.render.log" 2>&1
  )
  code=$?
  printf '%s\n' "$code" >"$LOG/$name.exit"
  find "$out" -maxdepth 1 -type f -printf '%s %p\n' | sort >"$LOG/$name.output-inventory.txt"
  snapshot "$LOG/$name.host-after.txt"
  git -C "$SOURCE" restore -- shared/gradio/hierarchy_selector/hierarchy_selector.pyi 2>/dev/null || true
  printf 'task=%s exit=%s\n' "$name" "$code" | tee -a "$LOG/remaining-status.txt"
}

snapshot "$LOG/remaining.host-before.txt"
run_task replacement-batch 3600
for pair in retake:3502 repaint:3503 recast:3504; do
  name=${pair%%:*}; seed=${pair##*:}
  src=$(find "$RUN/boundaries/replacement-batch" -maxdepth 1 -type f -name "*seed${seed}*.mp4" -print -quit)
  if test -n "$src"; then record_output "$name" "$src"; fi
done

for name in edit extend blend-probe; do
  run_task "$name" 3600
  case "$name" in
    edit) seed=3505 ;;
    extend) seed=3506 ;;
    blend-probe) seed=3507 ;;
  esac
  src=$(find "$RUN/boundaries/$name" -maxdepth 1 -type f -name "*seed${seed}*.mp4" -print -quit)
  target=${name%-probe}
  if test -n "$src"; then record_output "$target" "$src"; fi
done

snapshot "$LOG/remaining.host-after.txt"
git -C "$SOURCE" restore -- shared/gradio/hierarchy_selector/hierarchy_selector.pyi 2>/dev/null || true
git -C "$SOURCE" status --porcelain=v1 >"$LOG/remaining.source-final-status.txt"
find "$RUN/outputs" -type f | sort >"$LOG/remaining.output-inventory.txt"
cat "$LOG/remaining-status.txt"
