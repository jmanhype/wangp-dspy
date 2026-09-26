#!/bin/bash
set -euo pipefail
bundle=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$bundle/review"

for name in edit repaint upscale; do
  ffmpeg -y -v error -i "$bundle/outputs/$name/wd_9t9o_${name}.mp4" -vf 'fps=2,scale=240:-2,tile=5x2' -frames:v 1 "$bundle/review/$name-contact-sheet.jpg"
done

ffmpeg -y -v error \
  -ss 00:00:01.000 -i "$bundle/inputs/source.mp4" \
  -ss 00:00:01.000 -i "$bundle/outputs/edit/wd_9t9o_edit.mp4" \
  -ss 00:00:01.000 -i "$bundle/outputs/repaint/wd_9t9o_repaint.mp4" \
  -filter_complex '[0:v]scale=320:-2[a];[1:v]scale=320:-2[b];[2:v]scale=320:-2[c];[a][b][c]hstack=inputs=3' \
  -frames:v 1 "$bundle/review/source-edit-repaint-midframe.jpg"

shasum -a 256 "$bundle"/review/*.jpg > "$bundle/review/review-visual-hashes.txt"
