#!/usr/bin/env bash
set -euo pipefail
cd /home/straughter/Wan2GP
./venv/bin/python wgp.py --process /home/straughter/Wan2GP/wd_cpow_stable_sfx.json --output-dir /home/straughter/Wan2GP/outputs/wd-cpow/stable
