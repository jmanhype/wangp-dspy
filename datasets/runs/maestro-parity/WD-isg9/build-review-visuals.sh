#!/bin/bash
set -euo pipefail
bundle=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$bundle/review"

for name in extend retake edit repaint upscale; do
  input=$bundle/outputs/$name/wd_isg9_${name}.mp4
  fps=2
  if test "$name" = extend; then fps=1; fi
  ffmpeg -y -v error -i "$input" -vf "fps=$fps,scale=240:-2,tile=5x2" -frames:v 1 "$bundle/review/$name-contact-sheet.jpg"
done

ffmpeg -y -v error \
  -ss 00:00:01.000 -i "$bundle/inputs/source.mp4" \
  -ss 00:00:01.000 -i "$bundle/outputs/edit/wd_isg9_edit.mp4" \
  -ss 00:00:01.000 -i "$bundle/outputs/repaint/wd_isg9_repaint.mp4" \
  -filter_complex '[0:v]scale=320:-2[a];[1:v]scale=320:-2[b];[2:v]scale=320:-2[c];[a][b][c]hstack=inputs=3' \
  -frames:v 1 "$bundle/review/source-edit-repaint-midframe.jpg"

ffmpeg -y -v error \
  -i "$bundle/inputs/repaint-mask.mp4" \
  -i "$bundle/inputs/source.mp4" \
  -filter_complex '[0:v]select=eq(n\,28)[a];[1:v]select=eq(n\,28)[b];[a][b]hstack' \
  -frames:v 1 "$bundle/review/mask-source-midframe.jpg"

shasum -a 256 "$bundle"/review/*.jpg > "$bundle/review/review-visual-hashes.txt"
