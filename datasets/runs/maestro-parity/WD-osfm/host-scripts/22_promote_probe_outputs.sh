#!/bin/bash
set -euo pipefail

RUN=/home/straughter/wd-osfm-run
BOUNDARIES=$RUN/boundaries/probe-batch
LOG=$RUN/host-logs

record_output() {
  local name=$1
  local src=$2
  local out=$RUN/outputs/$name
  mkdir -p "$out"
  test -s "$src"
  cp "$src" "$out/wd_osfm_${name}.mp4"
  sha256sum "$out/wd_osfm_${name}.mp4" >"$out/wd_osfm_${name}.sha256"
  ffprobe -v error -show_streams -show_format -of json "$out/wd_osfm_${name}.mp4" >"$out/wd_osfm_${name}.ffprobe.json"
  ffmpeg -nostdin -v error -y -i "$out/wd_osfm_${name}.mp4" -vf fps=3,scale=240:-1,tile=3x3 -frames:v 1 "$out/contact-sheet.jpg"
  ffmpeg -nostdin -v error -y -i "$out/wd_osfm_${name}.mp4" -update 1 -frames:v 1 "$out/first-frame.png"
  printf 'source=%s\nfinal=%s\n' "$src" "$out/wd_osfm_${name}.mp4" >"$out/output-path.txt"
}

: >"$LOG/probe-promotion-report.tsv"
for pair in extend:3702 retake:3704 edit:3705 repaint:3707; do
  name=${pair%%:*}
  seed=${pair##*:}
  src=$(find "$BOUNDARIES" -maxdepth 1 -type f -name "*seed${seed}*.mp4" -print -quit)
  test -n "$src"
  record_output "$name" "$src"
  digest=$(sha256sum "$RUN/outputs/$name/wd_osfm_${name}.mp4" | awk '{print $1}')
  printf '%s\t%s\t%s\t%s\n' "$name" "$seed" "$digest" "$src" >>"$LOG/probe-promotion-report.tsv"
done

for seed in 3703 3706 3708; do
  test -z "$(find "$BOUNDARIES" -maxdepth 1 -type f -name "*seed${seed}*.mp4" -print -quit)"
done
printf 'promoted=4\nunpromoted_native_failures=blend,outpaint,recast\ngpu_invoked=0\n' >"$LOG/probe-promotion-accounting.txt"
find "$RUN/outputs" -type f | sort >"$LOG/probe-promotion-output-inventory.txt"
printf 'PROBE_OUTPUT_PROMOTION_PASS\n'
