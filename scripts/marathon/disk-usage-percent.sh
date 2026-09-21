#!/usr/bin/env bash
# Print root filesystem use as an integer percentage.
set -u
df / | awk 'NR==2{gsub("%",""); print $5}'
