#!/usr/bin/env bash
# Two-shot chained proof driver — run ON THE 3090 inside /home/straughter/Wan2GP.
# Usage: bash experiments_chained_test/run-chained-test.sh
# Fires wgp.py in CLI --process mode on shot-config.json (multishot path:
# per-shot generation with last-frame image_start chaining in
# models/minimax_h3/multishot.py), then verifies with verify_chained.py.
set -euo pipefail
cd /home/straughter/Wan2GP

CFG="$1"
OUT=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))[0]['params']['output'])" "$CFG")
mkdir -p "$(dirname "$OUT")"

SESSION=chained2shot
tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" \
  "python3 wgp.py --process '$CFG' --profile 3 --attention sdpa \
   2>&1 | tee '$OUT.log'; echo EXIT=\$? >> '$OUT.log'"
echo "render fired in tmux session '$SESSION'; log: $OUT.log"
