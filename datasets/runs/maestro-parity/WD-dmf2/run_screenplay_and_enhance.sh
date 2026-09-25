#!/usr/bin/env bash
set -Eeuo pipefail

bundle=$(cd "$(dirname "$0")" && pwd)
results="$bundle/planning/results"
plans="$bundle/planning/plans"
mkdir -p "$results" "$plans"

timeout 180 uv run --frozen wgp director plan \
  --request "$bundle/planning/requests/screenplay.json" \
  --db "$plans/screenplay.db" \
  --json > "$results/screenplay.plan.json" \
  2> "$results/screenplay.plan.stderr"
printf '%s' "$?" > "$results/screenplay.plan.exit"

timeout 120 uv run --frozen wgp director queue \
  --db "$plans/screenplay.db" \
  --json > "$results/screenplay.queue.json" \
  2> "$results/screenplay.queue.stderr"
printf '%s' "$?" > "$results/screenplay.queue.exit"

timeout 180 uv run --frozen wgp director review \
  --db "$plans/screenplay.db" \
  --json > "$results/screenplay.review.json" \
  2> "$results/screenplay.review.stderr"
printf '%s' "$?" > "$results/screenplay.review.exit"

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
