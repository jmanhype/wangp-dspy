#!/usr/bin/env bash
set -euo pipefail

LIVE=/home/straughter/Wan2GP
TARGET_TOKENIZER="$LIVE/models/ltx2/ltx_core/text_encoders/gemma/tokenizer.py"
TARGET_ENCODER="$LIVE/models/ltx2/ltx_core/text_encoders/gemma/encoders/base_encoder.py"

printf 'live_dirty_count='
git -C "$LIVE" status --short | wc -l
printf 'live_head='
git -C "$LIVE" rev-parse HEAD
printf 'origin_main='
git -C "$LIVE" rev-parse origin/main
printf '%s\n' 'remotes:'
git -C "$LIVE" remote -v
printf '%s\n' 'target_hashes:'
sha256sum "$TARGET_TOKENIZER" "$TARGET_ENCODER"
printf '%s\n' 'tokenizer_config_extra_special_tokens:'
/home/straughter/Wan2GP/venv/bin/python - "$LIVE/ckpts/gemma4-12b-ltx-v1/tokenizer_config.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    config = json.load(handle)
print(repr(config.get("extra_special_tokens")))
PY
