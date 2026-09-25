#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/straughter/Wan2GP/models/TTS/chatterbox
MIN_BEFORE_BYTES=20324765368
MIN_AFTER_BYTES=16106127360

assets=(
  'chatterbox-t3-mtl23ls-v2|https://huggingface.co/DeepBeepMeep/TTS/resolve/main/t3_mtl23ls_v2.safetensors|t3_mtl23ls_v2.safetensors|2143989752|b1237586127ce98e7800a68e49938eb5092846862aabcb6e17b2fda7889a6c75'
  'chatterbox-s3gen|https://huggingface.co/DeepBeepMeep/TTS/resolve/main/chatterbox/s3gen.pt|s3gen.pt|1057165844|9b9ff07e60b20c136e2b1b3d7563a24604e8d2c4c267888d1ee929dd0151d2a3'
  'chatterbox-voice-encoder|https://huggingface.co/DeepBeepMeep/TTS/resolve/main/chatterbox/ve.safetensors|ve.safetensors|5695784|f0921cab452fa278bc25cd23ffd59d36f816d7dc5181dd1bef9751a7fb61f63c'
  'chatterbox-conditions|https://huggingface.co/DeepBeepMeep/TTS/resolve/main/chatterbox/conds.pt|conds.pt|107374|6552d70568833628ba019c6b03459e77fe71ca197d5c560cef9411bee9d87f4e'
  'chatterbox-grapheme-tokenizer|https://huggingface.co/DeepBeepMeep/TTS/resolve/main/chatterbox/grapheme_mtl_merged_expanded_v1.json|grapheme_mtl_merged_expanded_v1.json|70011|df81a7ca7c31796cbe97f7a7142d5a53b12e88e12417ebe98f66602cafaf0461'
  'chatterbox-cangjie-tokenizer|https://huggingface.co/DeepBeepMeep/TTS/resolve/main/chatterbox/Cangjie5_TC.json|Cangjie5_TC.json|1920163|7073fd9de919443ae88e0bd2449917a65fe54898a4413ed1edcc4b67f28bce8c'
)

mkdir -p "$ROOT"
before=$(df -B1 --output=avail / | tail -1)
printf 'disk_before_bytes=%s\n' "$before"
if (( before < MIN_BEFORE_BYTES )); then
  printf 'REFUSED disk_before_below_floor bytes=%s floor=%s\n' "$before" "$MIN_BEFORE_BYTES" >&2
  exit 2
fi

for item in "${assets[@]}"; do
  IFS='|' read -r id url name size sha <<< "$item"
  destination="$ROOT/$name"
  temporary="$ROOT/.$name.part"
  if [[ -e "$destination" ]]; then
    printf 'REFUSED destination_exists id=%s path=%s\n' "$id" "$destination" >&2
    exit 2
  fi
  if [[ -e "$temporary" ]]; then
    printf 'REFUSED partial_exists id=%s path=%s\n' "$id" "$temporary" >&2
    exit 2
  fi
  printf 'download_begin id=%s size_bytes=%s url=%s\n' "$id" "$size" "$url"
  curl --fail --location --continue-at - --output "$temporary" "$url"
  actual_size=$(stat -c %s "$temporary")
  actual_sha=$(sha256sum "$temporary" | awk '{print $1}')
  if [[ "$actual_size" != "$size" || "$actual_sha" != "$sha" ]]; then
    printf 'REFUSED verification id=%s expected_size=%s actual_size=%s expected_sha=%s actual_sha=%s\n' \
      "$id" "$size" "$actual_size" "$sha" "$actual_sha" >&2
    exit 3
  fi
  mv "$temporary" "$destination"
  printf 'download_complete id=%s size_bytes=%s sha256=%s\n' "$id" "$actual_size" "$actual_sha"
done

after=$(df -B1 --output=avail / | tail -1)
printf 'disk_after_bytes=%s\n' "$after"
if (( after < MIN_AFTER_BYTES )); then
  printf 'REFUSED disk_after_below_floor bytes=%s floor=%s\n' "$after" "$MIN_AFTER_BYTES" >&2
  exit 4
fi
printf 'download_batch_complete planned_bytes=3208948928\n'
