#!/bin/bash
set -euo pipefail
printf '%s\t' /home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA-pruned_rank8_int8_convrot.safetensors
stat -c '%s\t%y\t' /home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA-pruned_rank8_int8_convrot.safetensors | tr '\n' '\t'
sha256sum /home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA-pruned_rank8_int8_convrot.safetensors | awk '{print $1}'
printf '%s\t' /home/straughter/Wan2GP/ckpts/MiniMax-H3-video_vae_fp16.safetensors
stat -c '%s\t%y\t' /home/straughter/Wan2GP/ckpts/MiniMax-H3-video_vae_fp16.safetensors | tr '\n' '\t'
sha256sum /home/straughter/Wan2GP/ckpts/MiniMax-H3-video_vae_fp16.safetensors | awk '{print $1}'
printf '%s\t' /home/straughter/Wan2GP/ckpts/MiniMax-H3-audio_vae_fp32.safetensors
stat -c '%s\t%y\t' /home/straughter/Wan2GP/ckpts/MiniMax-H3-audio_vae_fp32.safetensors | tr '\n' '\t'
sha256sum /home/straughter/Wan2GP/ckpts/MiniMax-H3-audio_vae_fp32.safetensors | awk '{print $1}'
printf '%s\t' /home/straughter/Wan2GP/ckpts/Qwen3-VL-32B-Instruct/Qwen3-VL-32B-Instruct-layer50_quanto_bf16_int8.safetensors
stat -c '%s\t%y\t' /home/straughter/Wan2GP/ckpts/Qwen3-VL-32B-Instruct/Qwen3-VL-32B-Instruct-layer50_quanto_bf16_int8.safetensors | tr '\n' '\t'
sha256sum /home/straughter/Wan2GP/ckpts/Qwen3-VL-32B-Instruct/Qwen3-VL-32B-Instruct-layer50_quanto_bf16_int8.safetensors | awk '{print $1}'
