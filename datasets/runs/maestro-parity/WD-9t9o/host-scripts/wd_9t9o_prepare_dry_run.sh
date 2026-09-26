#!/bin/bash
set -uo pipefail

ROOT=/home/straughter/Wan2GP
WORK=$ROOT/wd-9t9o
SETTINGS=$WORK/settings
LOGS=$WORK/logs
PYTHON=$ROOT/venv/bin/python
expected_source=6becf70d98be579159b0e3ed6b212517ee78c7a1cc01906588c3ad6f0dfb8beb

mkdir -p "$SETTINGS" "$LOGS" "$WORK/inputs" "$WORK/outputs"
actual_source=$(sha256sum "$WORK/inputs/source.mp4" | awk '{print $1}')
printf 'source_sha256=%s\n' "$actual_source" > "$WORK/source-hash.txt"
test "$actual_source" = "$expected_source"

ffmpeg -y -v error -i "$WORK/inputs/source.mp4" -update 1 -frames:v 1 "$WORK/inputs/first-frame.png"
ffmpeg -y -v error -f lavfi -i color=c=0x504f40:s=480x832:r=1:d=1 -frames:v 1 "$WORK/inputs/recast-reference.png"
ffmpeg -y -v error -f lavfi -i color=c=black:s=480x832:r=24:d=3 -vf drawbox=x=120:y=250:w=240:h=330:color=white:t=fill -frames:v 56 -c:v libx264 -pix_fmt yuv420p "$WORK/inputs/repaint-mask.mp4"
sha256sum "$WORK/inputs/source.mp4" "$WORK/inputs/first-frame.png" "$WORK/inputs/recast-reference.png" "$WORK/inputs/repaint-mask.mp4" > "$WORK/input-hashes.txt"
ffprobe -v error -count_frames -show_streams -show_format -of json "$WORK/inputs/repaint-mask.mp4" > "$WORK/inputs/repaint-mask.ffprobe.json"

rm -f "$LOGS"/dry-run-*.exit "$LOGS"/dry-run-*.log
for name in extend retake edit repaint upscale blend-probe recast-probe outpaint-probe; do
  cd "$ROOT"
  "$PYTHON" wgp.py --process "$SETTINGS/$name.json" --dry-run > "$LOGS/dry-run-$name.log" 2>&1
  code=$?
  printf '%s\n' "$code" > "$LOGS/dry-run-$name.exit"
  printf 'name=%s exit=%s\n' "$name" "$code"
done
for name in extend retake edit repaint upscale; do
  test "$(cat "$LOGS/dry-run-$name.exit")" = 0 || exit 1
done
