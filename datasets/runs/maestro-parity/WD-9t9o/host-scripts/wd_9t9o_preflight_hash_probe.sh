#!/bin/bash
set -euo pipefail

ROOT=/home/straughter/Wan2GP
WORK=$ROOT/wd-9t9o
mkdir -p "$WORK"

cat > "$WORK/wd-9t9o-model-hashes.sha256" <<'EOF'
30ff400f974b11a1ef13d216c5d9f6439a9c10322a3988b0374a39672ce286f0  /home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA-pruned_rank8_int8_convrot.safetensors
455010492bb59a9cc7b8f1ee23905b22a10079f89490adbf820a1728efcaea6b  /home/straughter/Wan2GP/ckpts/MiniMax-H3-video_vae_fp16.safetensors
37dddc2f3e6d5d5139d823d5ea283bbf304dadcb885b1ccda818aa13dade5ea2  /home/straughter/Wan2GP/ckpts/MiniMax-H3-audio_vae_fp32.safetensors
4df8fc5237746b3b058745d6ec8fe1e54a9721bdc663d35d2d1806952672f301  /home/straughter/Wan2GP/ckpts/Qwen3-VL-32B-Instruct/Qwen3-VL-32B-Instruct-layer50_quanto_bf16_int8.safetensors
EOF

{
  date -u +%Y-%m-%dT%H:%M:%SZ
  hostname
  printf '%s\n' '--- model sha256sum -c ---'
  sha256sum -c "$WORK/wd-9t9o-model-hashes.sha256"
  printf '%s\n' '--- source hash ---'
  sha256sum "$WORK/inputs/source.mp4"
  printf '%s\n' '--- raw model sha256sum ---'
  sha256sum /home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA-pruned_rank8_int8_convrot.safetensors /home/straughter/Wan2GP/ckpts/MiniMax-H3-video_vae_fp16.safetensors /home/straughter/Wan2GP/ckpts/MiniMax-H3-audio_vae_fp32.safetensors /home/straughter/Wan2GP/ckpts/Qwen3-VL-32B-Instruct/Qwen3-VL-32B-Instruct-layer50_quanto_bf16_int8.safetensors
  printf '%s\n' '--- stat size/mtime ---'
  stat -c '%n|%s|%y' /home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA-pruned_rank8_int8_convrot.safetensors /home/straughter/Wan2GP/ckpts/MiniMax-H3-video_vae_fp16.safetensors /home/straughter/Wan2GP/ckpts/MiniMax-H3-audio_vae_fp32.safetensors /home/straughter/Wan2GP/ckpts/Qwen3-VL-32B-Instruct/Qwen3-VL-32B-Instruct-layer50_quanto_bf16_int8.safetensors "$WORK/inputs/source.mp4"
  printf '%s\n' '--- disk ---'
  df -B1 "$ROOT"
  printf '%s\n' '--- gpu ---'
  nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader
  nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
  printf '%s\n' '--- unrelated process state ---'
  pgrep -af 'wgp.py|uvicorn|llama-server|ffmpeg' || true
  printf '%s\n' '--- QC health ---'
  curl -fsS --max-time 5 http://127.0.0.1:8377/health
  printf '\n'
} | tee "$WORK/preflight-model-hash.txt"
