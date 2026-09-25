#!/usr/bin/env bash
set -Eeuo pipefail

bundle=$(cd "$(dirname "$0")" && pwd)
frames="$bundle/review/frames"
mkdir -p "$frames"

for mode in prompt audio music_video screenplay; do
  first="$bundle/outputs/clips/$mode/clip0001.mp4"
  second="$bundle/outputs/clips/$mode/clip0002.mp4"
  ffmpeg -y -v error -sseof -0.1 -i "$first" -frames:v 1 \
    "$frames/$mode-clip0001-last.png"
  ffmpeg -y -v error -i "$second" -frames:v 1 \
    "$frames/$mode-clip0002-first.png"
  ffmpeg -y -v error -i "$first" -i "$second" \
    -filter_complex "[0:v][1:v]concat=n=2:v=1:a=0,scale=240:416,tile=4x2" \
    -frames:v 1 "$frames/$mode-boundary-contact.png"
  ffmpeg -y -v error \
    -i "$frames/$mode-clip0001-last.png" \
    -i "$frames/$mode-clip0002-first.png" \
    -filter_complex "[0:v][1:v]hstack" \
    "$frames/$mode-boundary-pair.png"
done

shasum -a 256 "$frames"/*.png > "$bundle/review/frame-hashes.txt"
