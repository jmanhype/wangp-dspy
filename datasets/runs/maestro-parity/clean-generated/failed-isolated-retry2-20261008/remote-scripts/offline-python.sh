#!/bin/bash
set -euo pipefail
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONPATH=/home/straughter/wd-28ac-final-gate7-20261003/runtime/rembg-2.0.65:/home/straughter/wd-28ac-final-gate7-20261003/runtime/mmgp-3.7.14:/home/straughter/ComfyUI/venv/lib/python3.12/site-packages
export PYTHONUNBUFFERED=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
exec /usr/bin/python3 "$@"
