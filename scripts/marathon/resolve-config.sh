#!/usr/bin/env bash
# Resolve the configured render target, Wan2GP root, and interpreter.
set -u
script_directory=${0%/*}
exec python3 "${script_directory}/resolve-config.py"
