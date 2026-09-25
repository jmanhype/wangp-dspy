#!/usr/bin/env bash
set -euo pipefail
ROOT=/home/straughter/wangp-dspy-vibevoice-20260916/datasets/runs/maestro-parity/WD-cpow
mkdir -p "$ROOT/outputs"
set -- "$ROOT"/.vibevoice-*/turn-1.prepared.wav
test "$#" -eq 1
PREPARED=$1
ffmpeg -y -v error -i "$ROOT/inputs/source.mp4" -i "$PREPARED" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 128k -ar 48000 -ac 2 -shortest -movflags +faststart "$ROOT/outputs/wd_cpow_vibevoice_revoice.mp4"
ffprobe -v error -show_streams -show_format -of json "$ROOT/outputs/wd_cpow_vibevoice_revoice.mp4" > "$ROOT/ffprobe-wd_cpow_vibevoice_revoice.remote.json"
ffmpeg -loglevel error -i "$ROOT/inputs/source.mp4" -map 0:v:0 -c copy -f streamhash -hash sha256 "$ROOT/video-stream-hash.source.txt"
ffmpeg -loglevel error -i "$ROOT/outputs/wd_cpow_vibevoice_revoice.mp4" -map 0:v:0 -c copy -f streamhash -hash sha256 "$ROOT/video-stream-hash.revoice.txt"
