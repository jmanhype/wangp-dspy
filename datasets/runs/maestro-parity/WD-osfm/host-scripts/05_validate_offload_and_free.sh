#!/bin/bash
set -euo pipefail

repo=/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-osfm
out="$repo/datasets/runs/maestro-parity/WD-osfm/host-logs/00-offload-proof.txt"
remote_path=/home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA_int8_convrot.safetensors
target=/Users/Shared/HermesWorkspace/model-offload/wangp-3090/MiniMax-H3-FL2VA_int8_convrot.safetensors
chunk_dir=/Users/Shared/HermesWorkspace/model-offload/wangp-3090/.wd-osfm-chunks
expected_size=34038903007
expected_sha=83a36b67776962f44087f2f7c12d95791393f3cce1ef898efc90405216e7b0c0

mkdir -p "$(dirname "$out")"
{
  date -u +%Y-%m-%dT%H:%M:%SZ
  printf 'destination_free_before='; df -g /Users/Shared/HermesWorkspace/model-offload | tail -1 | awk '{print $4}'
  local_size=$(stat -f %z "$target")
  local_sha=$(shasum -a 256 "$target" | awk '{print $1}')
  printf 'local_size=%s\nlocal_sha256=%s\n' "$local_size" "$local_sha"
  remote_size=$(ssh 3090 "stat -c %s '$remote_path'")
  remote_sha=$(ssh 3090 "sha256sum '$remote_path'" | awk '{print $1}')
  printf 'remote_size=%s\nremote_sha256=%s\n' "$remote_size" "$remote_sha"
  test "$local_size" = "$expected_size"
  test "$local_sha" = "$expected_sha"
  test "$remote_size" = "$expected_size"
  test "$remote_sha" = "$expected_sha"
  test "$local_size" = "$remote_size"
  test "$local_sha" = "$remote_sha"
  ssh 3090 "test ! -L '$remote_path' && unlink '$remote_path'"
  if ssh 3090 "test -e '$remote_path'"; then
    printf 'remote_unlink=FAIL\n'
    exit 90
  fi
  for chunk in "$chunk_dir"/chunk-1 "$chunk_dir"/chunk-2 "$chunk_dir"/chunk-3 "$chunk_dir"/chunk-4; do
    test ! -e "$chunk" || unlink "$chunk"
  done
  test ! -e "$chunk_dir/chunk-1"
  test ! -e "$chunk_dir/chunk-2"
  test ! -e "$chunk_dir/chunk-3"
  test ! -e "$chunk_dir/chunk-4"
  rmdir "$chunk_dir" 2>/dev/null || true
  printf 'remote_unlink=PASS\nchunk_unlink=PASS\n'
  printf 'remote_free_after='; ssh 3090 "df -B1 /home/straughter/Wan2GP | tail -1" | awk '{print $4}'
  printf 'destination_free_after='; df -g /Users/Shared/HermesWorkspace/model-offload | tail -1 | awk '{print $4}'
  printf 'OFFLOAD_VERIFIED_AND_REMOTE_FREED=PASS\n'
} | tee "$out"
