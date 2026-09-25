#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=/home/straughter/Wan2GP
WORK="$ROOT/wd-r81u"
SRC="$WORK/source.mp4"
ASSETS="$WORK/assets"
OUT="$WORK/outputs"
TMP="$WORK/intermediates"
EXPECTED_SOURCE=e8b690774b0df7a73c85505ea507277d2745641b34f68c60c24855882da88859
EXPECTED_RIFE=45c7f74156704769dc9f85cfcaf8552e1e926f9399dcfa3a553dee88fac6f53f
EXPECTED_ESRGAN=d5888fcefd5e1a71eb6b324546f977efe0b5176c67a046cdd144189312d3f894

mkdir -p "$ASSETS" "$OUT" "$TMP/rife" "$TMP/film" "$TMP/esrgan-input" "$TMP/esrgan-output"
printf 'host=%s\n' "$(hostname)"
date -u +%Y-%m-%dT%H:%M:%SZ
df -B1 /
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader

actual_source=$(timeout 120 sha256sum "$SRC" | awk '{print $1}')
test "$actual_source" = "$EXPECTED_SOURCE"

if [ ! -f "$ASSETS/rife4.26.pkl" ]; then
  timeout 900 curl --fail --location --continue-at - --output "$ASSETS/rife4.26.pkl.tmp" 'https://huggingface.co/DeepBeepMeep/Wan2.1/resolve/main/rife4.26.pkl'
  mv "$ASSETS/rife4.26.pkl.tmp" "$ASSETS/rife4.26.pkl"
fi
actual_rife=$(timeout 120 sha256sum "$ASSETS/rife4.26.pkl" | awk '{print $1}')
test "$actual_rife" = "$EXPECTED_RIFE"

if [ ! -f "$ASSETS/realesrgan-ncnn-vulkan-20220424-ubuntu.zip" ]; then
  timeout 900 curl --fail --location --continue-at - --output "$ASSETS/realesrgan-ncnn-vulkan-20220424-ubuntu.zip.tmp" 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip'
  mv "$ASSETS/realesrgan-ncnn-vulkan-20220424-ubuntu.zip.tmp" "$ASSETS/realesrgan-ncnn-vulkan-20220424-ubuntu.zip"
fi
actual_esrgan=$(timeout 120 sha256sum "$ASSETS/realesrgan-ncnn-vulkan-20220424-ubuntu.zip" | awk '{print $1}')
test "$actual_esrgan" = "$EXPECTED_ESRGAN"
if [ ! -x "$ASSETS/realesrgan-ncnn-vulkan-20220424-ubuntu/realesrgan-ncnn-vulkan" ]; then
  timeout 180 unzip -q "$ASSETS/realesrgan-ncnn-vulkan-20220424-ubuntu.zip" -d "$ASSETS"
fi
timeout 120 sha256sum "$ASSETS/realesrgan-ncnn-vulkan-20220424-ubuntu/models/realesrgan-x4plus.bin" "$ASSETS/realesrgan-ncnn-vulkan-20220424-ubuntu/models/realesrgan-x4plus.param" > "$WORK/realesrgan-model-hashes.txt"
df -B1 /

timeout 120 ffprobe -v error -print_format json -show_format -show_streams "$SRC" > "$WORK/ffprobe-source.json"

timeout 1200 ffmpeg -nostdin -y -i "$SRC" -an -vf 'minterpolate=fps=48:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1' -c:v ffv1 "$TMP/ffmpeg-interpolation.mp4"
timeout 600 ffmpeg -nostdin -y -i "$SRC" -i "$TMP/ffmpeg-interpolation.mp4" -map 1:v:0 -map 0:a:0 -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart "$OUT/wd_r81u_ffmpeg_interpolation_x2.mp4"

timeout 1200 ffmpeg -nostdin -y -i "$SRC" -an -vf 'scale=iw*2:ih*2:flags=lanczos' -c:v ffv1 "$TMP/ffmpeg-spatial-x2.mp4"
timeout 600 ffmpeg -nostdin -y -i "$SRC" -i "$TMP/ffmpeg-spatial-x2.mp4" -map 1:v:0 -map 0:a:0 -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart "$OUT/wd_r81u_ffmpeg_spatial_x2.mp4"

timeout 1200 ffmpeg -nostdin -y -i "$SRC" -an -vf 'noise=alls=12:allf=t+u:all_seed=2935' -c:v ffv1 "$TMP/ffmpeg-grain.mp4"
timeout 600 ffmpeg -nostdin -y -i "$SRC" -i "$TMP/ffmpeg-grain.mp4" -map 1:v:0 -map 0:a:0 -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart "$OUT/wd_r81u_ffmpeg_film_grain.mp4"

timeout 600 ffmpeg -nostdin -y -i "$SRC" -map 0:v:0 -map 0:a:0 -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart "$OUT/wd_r81u_ffmpeg_codec_h264.mp4"

cd "$ROOT"
timeout 1200 "$ROOT/venv/bin/python" "$WORK/wd_r81u_rife.py" "$SRC" "$TMP/rife/%08d.png" "$ASSETS/rife4.26.pkl"
timeout 600 ffmpeg -nostdin -y -i "$SRC" -i "$TMP/rife/%08d.png" -map 1:v:0 -map 0:a:0 -r 48 -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart "$OUT/wd_r81u_rife_interpolation_x2.mp4"

timeout 1200 "$ROOT/venv/bin/python" "$WORK/wd_r81u_film.py" "$SRC" "$TMP/film/%08d.png" --seed 2936 --intensity 0.05
timeout 600 ffmpeg -nostdin -y -i "$SRC" -i "$TMP/film/%08d.png" -map 1:v:0 -map 0:a:0 -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart "$OUT/wd_r81u_film_film_grain.mp4"

timeout 600 ffmpeg -nostdin -y -i "$SRC" -an -vsync 0 "$TMP/esrgan-input/%08d.png"
cd "$ASSETS/realesrgan-ncnn-vulkan-20220424-ubuntu"
timeout 1800 ./realesrgan-ncnn-vulkan -i "$TMP/esrgan-input" -o "$TMP/esrgan-output" -n realesrgan-x4plus -s 2 -t 128 -m models -g 0 -j 1:1:1
cd "$WORK"
timeout 600 ffmpeg -nostdin -y -i "$SRC" -i "$TMP/esrgan-output/%08d.png" -map 1:v:0 -map 0:a:0 -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart "$OUT/wd_r81u_real_esrgan_spatial_x2.mp4"

for media in "$OUT"/*.mp4; do
  timeout 120 ffprobe -v error -print_format json -show_format -show_streams "$media" > "$WORK/ffprobe-$(basename "$media" .mp4).json"
done
timeout 300 sha256sum "$SRC" "$OUT"/*.mp4 > "$WORK/output-hashes.txt"
du -sb "$OUT" > "$WORK/output-size.txt"
df -B1 /
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
date -u +%Y-%m-%dT%H:%M:%SZ
