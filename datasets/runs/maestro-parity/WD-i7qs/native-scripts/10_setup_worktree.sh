#!/usr/bin/env bash
set -euo pipefail

LIVE=/home/straughter/Wan2GP
BASE=071ce70aab1169c61cc14bbefd71bdda3a04a9e9
BRANCH=story/WD-i7qs
ISOLATED=/home/straughter/Wan2GP-story-WD-i7qs

if [[ -e "$ISOLATED" ]]; then
    printf 'ERROR: isolated path already exists: %s\n' "$ISOLATED" >&2
    exit 1
fi
if git -C "$LIVE" show-ref --verify --quiet "refs/heads/$BRANCH"; then
    printf 'ERROR: branch already exists: %s\n' "$BRANCH" >&2
    exit 1
fi

actual_base=$(git -C "$LIVE" rev-parse origin/main)
if [[ "$actual_base" != "$BASE" ]]; then
    printf 'ERROR: origin/main is %s, expected %s\n' "$actual_base" "$BASE" >&2
    exit 1
fi

git -C "$LIVE" worktree add -b "$BRANCH" "$ISOLATED" "$BASE"
printf 'isolated_branch='
git -C "$ISOLATED" branch --show-current
printf 'isolated_head='
git -C "$ISOLATED" rev-parse HEAD
printf 'isolated_dirty_count='
git -C "$ISOLATED" status --short | wc -l
printf '%s\n' 'target_hashes:'
git -C "$ISOLATED" hash-object \
  models/ltx2/ltx_core/text_encoders/gemma/tokenizer.py \
  models/ltx2/ltx_core/text_encoders/gemma/encoders/base_encoder.py
