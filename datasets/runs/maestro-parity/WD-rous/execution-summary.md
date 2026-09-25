# WD-rous native execution summary

All operations ran synchronously with local SSH timeouts of 1800 seconds and remote `timeout 1740` boundaries. The primary generation started at clean commit `3fd053f`, after the durable queue reached `rendering`.

1. ACE generate: `/mnt/bulk/straughter/ACE-Step-1.5/.venv/bin/python /home/straughter/Wan2GP/wd_rous_ace.py generate /home/straughter/Wan2GP/outputs/wd-rous/ace/wd_rous_ace_generate.wav`
2. Stable Audio generate: `cd /home/straughter/Wan2GP && ./venv/bin/python wgp.py --process /home/straughter/Wan2GP/stable-generate.json --output-dir /home/straughter/Wan2GP/outputs/wd-rous/stable`
3. ACE style adapt: `/mnt/bulk/straughter/ACE-Step-1.5/.venv/bin/python /home/straughter/Wan2GP/wd_rous_ace.py adapt /home/straughter/Wan2GP/outputs/wd-rous/ace/wd_rous_ace_style_adapt.wav /home/straughter/Wan2GP/outputs/wd-rous/ace/wd_rous_ace_generate.wav /home/straughter/Wan2GP/outputs/wd-rous/stable/wd_rous_stable_generate.wav`

No training, GUI, registry publication, or protected engine change ran. The final host check shows 11,151,310,848 bytes free, GPU at 83 MiB / 0%, both temporary services down, and no active lane process.
