#!/usr/bin/env bash
# audio_critic supervisor — up/down lifecycle (slice 2, proposal
# "Contention strategy"): stays down by default; refuses to start
# while wgp render or vLLM holds GPU memory; idles out (unloads)
# after N minutes without requests.
#
# Env:
#   AC_IDLE_MINUTES   idle unload threshold      (default 20)
#   AC_MIN_FREE_MB    minimum free GPU memory    (default 1000)
#   AC_PORT           service port               (default 8377)
#   AC_BIND           bind address (localhost + LAN only; never a
#                     auth-free public bind)     (default 127.0.0.1)
set -euo pipefail

PORT="${AC_PORT:-8377}"
BIND="${AC_BIND:-127.0.0.1}"
IDLE_MINUTES="${AC_IDLE_MINUTES:-20}"
MIN_FREE_MB="${AC_MIN_FREE_MB:-1000}"
PIDFILE="/tmp/audio_critic_svc_${PORT}.pid"
LOG="/tmp/audio_critic_svc_${PORT}.log"

die() { echo "audio-critic supervisor: $*" >&2; exit 1; }

gpu_holders() {
    # processes holding GPU memory, with names (wgp / vllm blocks us)
    nvidia-smi --query-compute-apps=pid,process_name,used_memory \
        --format=csv,noheader 2>/dev/null || true
}

cmd_up() {
    command -v nvidia-smi >/dev/null 2>&1 || die \
        "nvidia-smi not found — this supervisor runs on the 3090 host"
    [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null \
        && { echo "already up (pid $(cat "$PIDFILE"))"; exit 0; }

    # refuse to start while wgp render or vLLM holds the GPU
    holders="$(gpu_holders)"
    if echo "$holders" | grep -qiE 'wgp|vllm'; then
        die "GPU is held by wgp/vLLM — refusing to start. Holders:
$holders"
    fi
    free_mb="$(nvidia-smi --query-gpu=memory.free \
        --format=csv,noheader,nounits | head -1)"
    [ "$free_mb" -ge "$MIN_FREE_MB" ] || die \
        "insufficient free GPU memory: ${free_mb}MB < ${MIN_FREE_MB}MB"

    nohup uvicorn qc.audio_critic.service:app \
        --host "$BIND" --port "$PORT" --workers 1 \
        >"$LOG" 2>&1 &
    echo $! > "$PIDFILE"
    echo "up: pid $(cat "$PIDFILE") on ${BIND}:${PORT} (log: $LOG)"
}

cmd_down() {
    [ -f "$PIDFILE" ] || { echo "down: not running"; exit 0; }
    pid="$(cat "$PIDFILE")"
    kill "$pid" 2>/dev/null || true
    rm -f "$PIDFILE"
    echo "down: stopped $pid"
}

cmd_status() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "up: pid $(cat "$PIDFILE")"
    else
        echo "down"
    fi
}

case "${1:-}" in
    up)      cmd_up ;;
    down)    cmd_down ;;
    status)  cmd_status ;;
    *) die "usage: $0 up|down|status" ;;
esac
