#!/usr/bin/env bash
set -euo pipefail

LIVE=/home/straughter/Wan2GP
ISOLATED=/home/straughter/Wan2GP-story-WD-i7qs
TOKENIZER="$LIVE/models/ltx2/ltx_core/text_encoders/gemma/tokenizer.py"
ENCODER="$LIVE/models/ltx2/ltx_core/text_encoders/gemma/encoders/base_encoder.py"

live_count=$(git -C "$LIVE" status --short | wc -l | tr -d ' ')
live_head=$(git -C "$LIVE" rev-parse HEAD)
tokenizer_hash=$(sha256sum "$TOKENIZER" | cut -d' ' -f1)
encoder_hash=$(sha256sum "$ENCODER" | cut -d' ' -f1)

printf 'live_dirty_count=%s\n' "$live_count"
printf 'live_head=%s\n' "$live_head"
printf 'live_origin_main=%s\n' "$(git -C "$LIVE" rev-parse origin/main)"
printf 'live_tokenizer_sha256=%s\n' "$tokenizer_hash"
printf 'live_encoder_sha256=%s\n' "$encoder_hash"
printf 'isolated_branch=%s\n' "$(git -C "$ISOLATED" branch --show-current)"
printf 'isolated_head=%s\n' "$(git -C "$ISOLATED" rev-parse HEAD)"
printf 'isolated_upstream=%s\n' "$(git -C "$ISOLATED" rev-parse --abbrev-ref --symbolic-full-name '@{u}')"
printf 'isolated_dirty_count=%s\n' "$(git -C "$ISOLATED" status --short | wc -l | tr -d ' ')"
printf 'fork_branch_sha=%s\n' "$(git -C "$ISOLATED" ls-remote fork refs/heads/story/WD-i7qs | cut -f1)"

[[ "$live_count" == "106" ]]
[[ "$live_head" == "4c93b64a47b5b0a915f2abec2ce754be98227150" ]]
[[ "$tokenizer_hash" == "0accdf91f65ff63eee107ff28fbe64424052c39e809c0415164feb83acee5299" ]]
[[ "$encoder_hash" == "2ac7aaed0e0ad852461aed1b8d2be4023b00e0f7b84308e9a8902c896e5ec824" ]]
printf 'live_untouched_checks=PASS\n'
