#!/bin/bash
set -uo pipefail

ROOT=/home/straughter/Wan2GP
WORK=$ROOT/wd-isg9
SETTINGS=$WORK/settings
LOGS=$WORK/logs
PYTHON=$ROOT/venv/bin/python

mkdir -p "$SETTINGS" "$LOGS" "$WORK/inputs" "$WORK/outputs"

source=$ROOT/outputs/wd-2gyw/h3-standard/wd_2gyw_h3_standard.mp4
first=$ROOT/outputs/wd-2gyw/h3-standard/wd_2gyw_h3_standard_first_frame.png
expected_source=e8b690774b0df7a73c85505ea507277d2745641b34f68c60c24855882da88859
expected_first=888e32c332c922616d39f802383d66a3de8733d7bb54d5aacdb6a03560bd638b

actual_source=$(sha256sum "$source" | awk '{print $1}')
actual_first=$(sha256sum "$first" | awk '{print $1}')
printf 'source_sha256=%s\nfirst_frame_sha256=%s\n' "$actual_source" "$actual_first" > "$WORK/source-hashes.txt"
test "$actual_source" = "$expected_source"
test "$actual_first" = "$expected_first"

ffmpeg -y -v error -f lavfi -i color=c=0x404f64:s=480x832:r=1:d=1 -frames:v 1 "$WORK/inputs/recast-reference.png"
ffmpeg -y -v error -f lavfi -i color=c=black:s=480x832:r=24:d=3 -vf drawbox=x=120:y=250:w=240:h=330:color=white:t=fill -frames:v 56 -c:v libx264 -pix_fmt yuv420p "$WORK/inputs/repaint-mask.mp4"
sha256sum "$WORK/inputs/recast-reference.png" "$WORK/inputs/repaint-mask.mp4" > "$WORK/input-hashes.txt"
ffprobe -v error -count_frames -show_streams -show_format -of json "$WORK/inputs/repaint-mask.mp4" > "$WORK/inputs/repaint-mask.ffprobe.json"

rm -f "$LOGS"/dry-run-*.exit "$LOGS"/dry-run-*.log
for name in extend retake edit repaint upscale blend-probe recast-probe outpaint-probe; do
  cd "$ROOT"
  "$PYTHON" wgp.py --process "$SETTINGS/$name.json" --dry-run > "$LOGS/dry-run-$name.log" 2>&1
  code=$?
  printf '%s\n' "$code" > "$LOGS/dry-run-$name.exit"
  printf 'name=%s exit=%s\n' "$name" "$code"
done

python3 - <<'PY'
from pathlib import Path
logs = Path('/home/straughter/Wan2GP/wd-isg9/logs')
for path in sorted(logs.glob('dry-run-*.exit')):
    print(f'{path.stem.removeprefix("dry-run-")}: {path.read_text().strip()}')
PY

for name in extend retake edit repaint upscale; do
  test "$(cat "$LOGS/dry-run-$name.exit")" = 0 || exit 1
done
