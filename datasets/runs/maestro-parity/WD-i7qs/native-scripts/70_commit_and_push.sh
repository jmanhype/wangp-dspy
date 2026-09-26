#!/usr/bin/env bash
set -euo pipefail

REPO=/home/straughter/Wan2GP-story-WD-i7qs
PYTHON=/home/straughter/Wan2GP/venv/bin/python
BRANCH=story/WD-i7qs

cd "$REPO"
"$PYTHON" -m py_compile \
  models/ltx2/ltx_core/text_encoders/gemma/tokenizer.py \
  models/ltx2/ltx_core/text_encoders/gemma/encoders/base_encoder.py \
  tests/test_ltx_gemma_tokenizer.py
git diff --check
printf '%s\n' 'pre_commit_status:'
git status --short
git add \
  models/ltx2/ltx_core/text_encoders/gemma/tokenizer.py \
  models/ltx2/ltx_core/text_encoders/gemma/encoders/base_encoder.py \
  tests/test_ltx_gemma_tokenizer.py
git commit -m 'fix(WD-i7qs): decouple gemma extra tokens from mistral patch'
git push -u fork "$BRANCH"
printf 'branch='
git branch --show-current
printf 'head='
git rev-parse HEAD
printf 'upstream='
git rev-parse --abbrev-ref --symbolic-full-name '@{u}'
printf '%s\n' 'post_push_status:'
git status --short --branch
