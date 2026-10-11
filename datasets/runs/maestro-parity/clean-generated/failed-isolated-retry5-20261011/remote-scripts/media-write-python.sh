#!/bin/bash
set -euo pipefail
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONUNBUFFERED=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
/usr/bin/python3 -S -c 'import hashlib,pathlib,sys; p=pathlib.Path(sys.argv[1]); sys.exit(0 if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==sys.argv[2] else '"'"'PYAV_COMPAT_FAILED: missing or changed shim'"'"')' /home/straughter/Wan2GP/wd-bw0h-clean-generated-retry5-20261009/pyav-compat/sitecustomize.py 9dfe8c270fc888acde082365a5d9d88208773679a4d5944940fdd8a97a4f0cb3
export PYTHONPATH=/home/straughter/Wan2GP/wd-bw0h-clean-generated-retry5-20261009/pyav-compat:/home/straughter/wd-28ac-final-gate7-20261003/runtime/rembg-2.0.65:/home/straughter/wd-28ac-final-gate7-20261003/runtime/mmgp-3.7.14:/home/straughter/ComfyUI/venv/lib/python3.12/site-packages
exec /usr/bin/python3 "$@"
