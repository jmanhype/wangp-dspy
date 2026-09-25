#!/usr/bin/env bash
set -Eeuo pipefail
bundle=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$bundle/planning/results"
for request in "$bundle"/planning/requests/*.json; do
  name=$(basename "$request" .json)
  timeout 120 uv run --frozen wgp finish plan --request "$request" --dry-run --json > "$bundle/planning/results/$name.json" 2> "$bundle/planning/results/$name.stderr"
  printf '%s\n' "$?" > "$bundle/planning/results/$name.exit"
done
