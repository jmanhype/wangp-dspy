#!/usr/bin/env bash
set -Eeuo pipefail

bundle=$(cd "$(dirname "$0")" && pwd)
results="$bundle/planning/results"
plans="$bundle/planning/plans"
mkdir -p "$results" "$plans"

for request in prompt audio music_video screenplay; do
  timeout 180 uv run --frozen wgp director plan \
    --request "$bundle/planning/requests/$request.json" \
    --db "$plans/$request.db" \
    --json > "$results/$request.plan.json" \
    2> "$results/$request.plan.stderr"
  printf '%s' "$?" > "$results/$request.plan.exit"

  timeout 120 uv run --frozen wgp director queue \
    --db "$plans/$request.db" \
    --json > "$results/$request.queue.json" \
    2> "$results/$request.queue.stderr"
  printf '%s' "$?" > "$results/$request.queue.exit"

  timeout 180 uv run --frozen wgp director review \
    --db "$plans/$request.db" \
    --json > "$results/$request.review.json" \
    2> "$results/$request.review.stderr"
  printf '%s' "$?" > "$results/$request.review.exit"
done

timeout 180 uv run --frozen wgp director enhance \
  --request "$bundle/planning/requests/enhancement.json" \
  --output-db "$plans/prompt.enhanced.db" \
  --json > "$results/prompt.enhance.json" \
  2> "$results/prompt.enhance.stderr"
printf '%s' "$?" > "$results/prompt.enhance.exit"

timeout 180 uv run --frozen wgp director review \
  --db "$plans/prompt.enhanced.db" \
  --json > "$results/prompt.enhanced.review.json" \
  2> "$results/prompt.enhanced.review.stderr"
printf '%s' "$?" > "$results/prompt.enhanced.review.exit"
