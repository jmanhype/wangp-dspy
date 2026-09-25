#!/usr/bin/env bash
set -euo pipefail

printf 'chatterbox_tree\n'
find /home/straughter/Wan2GP/models/TTS/chatterbox -maxdepth 4 -type f -printf '%s\t%p\n' | sort -k2
printf 't3_tree\n'
find /home/straughter/Wan2GP/models/TTS/chatterbox/models/t3 -maxdepth 3 -printf '%y\t%s\t%p\n' 2>/dev/null | sort -k3 || true
printf 'defaults\n'
cat /home/straughter/Wan2GP/defaults/chatterbox.json
printf 'handler_symbols\n'
grep -nE 'def (load|generate|__call__)|Chatterbox|chatterbox|model_path|weights|voice|t3' /home/straughter/Wan2GP/models/TTS/chatterbox_handler.py | head -240
printf 'wgp_tts_help\n'
cd /home/straughter/Wan2GP
./venv/bin/python wgp.py --help | grep -A3 -B2 -E 'tts|chatterbox|voice' || true
