#!/bin/bash
# S4 STEP 3 — render driver: stage assets to 3090, run wgp headless
# per cut (PROVEN S2.5 job shape), collect mp4s into /tmp/s4/render-out.
# Runs ON THE MAC. Sequential — 24GB card, one job at a time.
set -u
SSH="ssh -o ConnectTimeout=15 -o BatchMode=yes 3090"
VENV_PY=/home/straughter/Wan2GP/venv/bin/python
WGP=/home/straughter/Wan2GP/wgp.py
LOCAL_FILM=/Users/Shared/HermesWorkspace/wangp-dspy/s4/films/satans-mom

$SSH 'mkdir -p /tmp/s4/render-out /tmp/s4/jobs /tmp/s4/audio /tmp/s4/masters'
# stage masters + cut1 master from /tmp/s25 (already on the 3090)
scp -q "$LOCAL_FILM/masters/cut2_master.png" 3090:/tmp/s4/masters/
scp -q "$LOCAL_FILM/masters/cut3_master.png" 3090:/tmp/s4/masters/
$SSH 'cp /tmp/s25/master.png /tmp/s4/masters/cut1_master.png'

# stage guide audio (includes lines_padded/cut1_1.wav)
for f in "$LOCAL_FILM"/dialogue/lines/*.wav; do
  scp -q "$f" 3090:/tmp/s4/audio/ || exit 9
done
for f in "$LOCAL_FILM"/dialogue/lines_padded/*.wav; do
  scp -q "$f" 3090:/tmp/s4/audio/ || exit 9
done
echo "STAGED $(date -u +%H:%M:%S)"

render_cut() {
  CUT=$1; WAV=$2; MASTER=$3; FRAMES=$4; SEED=$5; PROMPTFILE=$6
  $SSH "python3 - <<PYEOF
import json
doc = json.load(open('/tmp/s4/jobs/cut${CUT}_prompt.json'))
settings = {
  'model_type': 'minimax_h3_ref2va_pruned',
  'prompt': doc['prompt'],
  'width': 480, 'height': 832,
  'num_inference_steps': 20,
  'guidance_scale': 1.0,
  'embedded_guidance_scale': 6.0,
  'force_fps': '24',
  'seed': ${SEED},
  'image_refs': ['/tmp/s4/masters/${MASTER}'],
  'audio_prompt_type': 'A',
  'audio_guide': '/tmp/s4/audio/${WAV}',
  'audio_refs': ['/tmp/s4/audio/${WAV}'],
  'video_prompt_type': 'I',
  'video_length': ${FRAMES},
}
json.dump(settings, open('/tmp/s4/jobs/cut${CUT}_settings.json','w'), indent=2)
print('cut${CUT} settings written')
PYEOF"
  $SSH "cd /home/straughter/Wan2GP && timeout 2100 $VENV_PY $WGP --process /tmp/s4/jobs/cut${CUT}_settings.json --profile 3 --attention sdpa > /tmp/s4/jobs/cut${CUT}_render.log 2>&1; echo wgp_exit=\$?"
  # collect newest mp4 from wgp outputs into render-out
  $SSH "latest=\$(ls -t /home/straughter/Wan2GP/outputs/*.mp4 2>/dev/null | head -1); if [ -n \"\$latest\" ]; then cp \"\$latest\" /tmp/s4/render-out/cut${CUT}.mp4 && rm -f \"\$latest\"; ffprobe -v error -show_entries format=duration -of csv=p=0 /tmp/s4/render-out/cut${CUT}.mp4; else echo NO_OUTPUT_cut${CUT}; fi"
}

render_cut 1 cut1_1.wav cut1_master.png 107 43 cut1
echo "CUT1 DONE $(date -u +%H:%M:%S)"
render_cut 2 cut1_2.wav cut1_master.png 124 44 cut2
echo "CUT2 DONE $(date -u +%H:%M:%S)"
render_cut 3 cut2_1.wav cut2_master.png 141 45 cut3
echo "CUT3 DONE $(date -u +%H:%M:%S)"
render_cut 4 cut2_2.wav cut2_master.png 209 46 cut4
echo "CUT4 DONE $(date -u +%H:%M:%S)"
render_cut 5 cut3_1.wav cut3_master.png 107 47 cut5
echo "CUT5 DONE $(date -u +%H:%M:%S)"
render_cut 6 cut3_2.wav cut3_master.png 124 48 cut6
echo "CUT6 DONE $(date -u +%H:%M:%S)"
echo "ALL RENDERS COMPLETE"
