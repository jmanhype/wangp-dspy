#!/usr/bin/env bash
set -Eeuo pipefail
printf '%s\n' '--- WanGP neural_frame_gen implementation search ---'
grep -R -n 'neural_frame_gen' /home/straughter/Wan2GP/postprocessing /home/straughter/Wan2GP/wgp.py /home/straughter/Wan2GP/setup_config.json 2>/dev/null || true
printf '%s\n' '--- WanGP neural file search ---'
find /home/straughter/Wan2GP -iname '*neural*frame*' -print 2>/dev/null | head -100
printf '%s\n' '--- H3 face refiner implementation (separate named backend, not neural_frame_gen) ---'
find /home/straughter/Wan2GP/postprocessing/h3_face_refiner -maxdepth 2 -type f -print | sort
