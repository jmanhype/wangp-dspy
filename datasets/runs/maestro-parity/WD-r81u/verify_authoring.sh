#!/usr/bin/env bash
set -Eeuo pipefail
repo=$(cd "$(dirname "$0")"/../../../../ && pwd)
cd "$repo"
mapfile -t paths < <(git diff --name-only c91a6d8..HEAD)
pvg verify "${paths[@]}" --format=text
