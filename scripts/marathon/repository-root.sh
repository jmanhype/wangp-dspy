#!/usr/bin/env bash
# Print this checkout's repository root without compound shell discovery.
set -u
script_directory=${0%/*}
scripts_directory=${script_directory%/*}
printf '%s\n' "${scripts_directory%/*}"
