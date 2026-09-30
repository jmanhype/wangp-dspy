set -eu
cd /home/straughter/Wan2GP/wd-qthq-editor-export/20260929T195201Z/cc0280f0
printf '%s=' 'sources/video-cut.mp4'; sha256sum 'sources/video-cut.mp4' | awk '{print $1}'
printf '%s=' 'sources/voice.wav'; sha256sum 'sources/voice.wav' | awk '{print $1}'
printf '%s=' 'project/lf002-editor-media.wgp-editor.json'; sha256sum 'project/lf002-editor-media.wgp-editor.json' | awk '{print $1}'
printf '%s=' 'export.json'; sha256sum 'export.json' | awk '{print $1}'
