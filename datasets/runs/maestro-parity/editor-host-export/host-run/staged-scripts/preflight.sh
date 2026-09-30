set -eu
ROOT=/home/straughter/Wan2GP
WORK=/home/straughter/Wan2GP/wd-qthq-editor-export/20260929T195201Z/cc0280f0
test "$(hostname)" != localhost
command -v ffmpeg
command -v ffprobe
if ps -eo args= | grep -E 'wd[-]bw0h|WD[-]bw0h' >/dev/null; then exit 71; fi
mkdir -p "$ROOT"
test ! -e "$WORK"
mkdir -p "$WORK/sources" "$WORK/project" "$WORK/outputs"
FREE=$(df -B1 "$ROOT" | awk 'NR==2 {print $4}')
printf 'host=%s\n' "$(hostname)"
printf 'user=%s\n' "$(id -un)"
printf 'workspace=%s\n' "$WORK"
printf 'ffmpeg=%s\n' "$(command -v ffmpeg)"
printf 'ffprobe=%s\n' "$(command -v ffprobe)"
printf 'free_bytes=%s\n' "$FREE"
ffmpeg -version | sed -n '1p'
