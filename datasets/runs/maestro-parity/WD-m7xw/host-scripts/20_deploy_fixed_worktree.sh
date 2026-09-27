#!/bin/bash
set -euo pipefail
LIVE=/home/straughter/Wan2GP
FIXED=/home/straughter/Wan2GP-story-WD-i7qs
SOURCE=/home/straughter/Wan2GP-story-WD-m7xw
RUN=/home/straughter/wd-m7xw-run
PY=$LIVE/venv/bin/python
COMMIT=faea82d15bf10b3479c42c0ea430892aae975870
test -d "$LIVE"
test -d "$FIXED"
test ! -e "$SOURCE"
test ! -e "$RUN"
test "$(git -C "$FIXED" rev-parse HEAD)" = "$COMMIT"
test -z "$(git -C "$FIXED" status --porcelain=v1)"
live_before=$(git -C "$LIVE" status --porcelain=v1 | sha256sum | awk '{print $1}')
git -C "$LIVE" worktree add --detach "$SOURCE" "$COMMIT"
mkdir -p "$RUN/preflight" "$RUN/settings" "$RUN/logs" "$RUN/inputs" "$RUN/outputs"
ln -s "$LIVE/ckpts" "$SOURCE/ckpts"
cat > "$RUN/preflight/tokenizer_check.py" <<'PY'
import sys
from pathlib import Path
source = Path('/home/straughter/Wan2GP-story-WD-i7qs')
run_source = Path('/home/straughter/Wan2GP-story-WD-m7xw')
sys.path.insert(0, str(run_source))
from models.ltx2.ltx_core.text_encoders.gemma.tokenizer import LTXVGemmaTokenizer
path = '/home/straughter/Wan2GP/ckpts/gemma4-12b-ltx-v1'
tokenizer = LTXVGemmaTokenizer(path, 1024, extra_special_tokens={'video_token': '<|video|>'})
vocab_size = len(tokenizer.tokenizer)
video_id = tokenizer.tokenizer.convert_tokens_to_ids('<|video|>')
encoded = tokenizer('<|video|>')
print(f'vocab_size={vocab_size}')
print(f'video_token_id={video_id}')
print(f'encoded={encoded}')
assert vocab_size == 262144
assert video_id == 258884
assert 258884 in encoded
print('tokenizer_check=PASS')
PY
PYTHONPATH="$SOURCE" "$PY" "$RUN/preflight/tokenizer_check.py" > "$RUN/preflight/tokenizer_check.raw.txt" 2>&1
{
  date -u +%Y-%m-%dT%H:%M:%SZ
  hostname
  git -C "$SOURCE" rev-parse HEAD
  git -C "$SOURCE" status --porcelain=v1
  git -C "$SOURCE" status --porcelain=v1 | sha256sum
  readlink "$SOURCE/ckpts"
  df -B1 "$RUN"
  nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits
} > "$RUN/preflight/deploy_state.txt"
cat "$RUN/preflight/tokenizer_check.raw.txt"
cat "$RUN/preflight/deploy_state.txt"
live_after=$(git -C "$LIVE" status --porcelain=v1 | sha256sum | awk '{print $1}')
test "$live_before" = "$live_after"
printf 'live_dirty_identity_unchanged=PASS\n'
