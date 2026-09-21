"""QC leg for the pipeline cycle (WD-mhr2 stage 5).

Runs on the MAC (local): pushes the rendered video to the 3090,
faststart-remuxes it (wgp mp4s have moov-at-end, which breaks
llama-server's cache:pipe ffmpeg decode), critiques it through the
qwen38-27b VLM (llama-server, port 8000), and writes the verdict back
into the run record.

Empirical contract (2026-08-24 live debugging):
- llama-server needs --media-path, and file:// URLs are RELATIVE to it
  (absolute paths get prefixed onto media-path, doubling them)
- input_video payload shape: {"url": "file://<rel-path>"} object
- the critique must run against the FASTSTART copy

Usage: run_qc.py <local_video> <run_record.json> <genre>
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

from wangp.config import HostConfigError, load_host_config, require_host_config

QC_DIR = "/home/straughter/qwen3vl-video"
THRESHOLDS = {"surreal": 4.5, "music": 5.0, "edu": 8.0, "comedy": 7.0}

PROMPT = (
    "You are a video QC grader. Analyze this video shot: subject, "
    "motion quality, temporal consistency (flicker/morphing), "
    "artifacts. Give a 1-10 score and a one-line verdict. "
    "End your reply with exactly: Score: N/10")

# remote-side critique script (written once per call; idempotent)
_REMOTE_QC = f'''
import json, sys, time, urllib.request
V, OUT = sys.argv[1], sys.argv[2]
payload = {{"model": "q",
           "chat_template_kwargs": {{"enable_thinking": False}},
           "messages": [{{"role": "user", "content": [
               {{"type": "text", "text": {PROMPT!r}}},
               {{"type": "input_video",
                "input_video": {{"url": "file://" + V}}}}]}}],
           "max_tokens": 600}}
req = urllib.request.Request(
    "http://localhost:8000/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={{"Content-Type": "application/json"}})
t0 = time.time()
r = json.load(urllib.request.urlopen(req, timeout=590))
open(OUT, "w").write(json.dumps({{
    "content": r["choices"][0]["message"]["content"],
    "latency": round(time.time() - t0, 1)}}))
'''


def _ssh(cmd: str, timeout: int = 620) -> str:
    target = require_host_config(
        load_host_config(environ=os.environ)
    ).target
    assert target is not None
    r = subprocess.run(["ssh", "-o", "ConnectTimeout=15", target.value, cmd],
                       capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"ssh failed: {r.stderr[-300:]}")
    return r.stdout


def critique(local_video: str, genre: str) -> dict:
    """Full QC leg. Returns {critic, score, verdict, summary, latency}."""
    config = require_host_config(load_host_config(environ=os.environ))
    target = config.target
    assert target is not None
    remote_name = Path(local_video).name.replace(".mp4", "_qc.mp4")
    remote_fast = remote_name.replace(".mp4", "_fast.mp4")

    subprocess.run(["rsync", "-q", local_video,
                    f"{target.value}:{QC_DIR}/{remote_name}"], check=True,
                   timeout=300)

    # write the critique helper, remux, critique, fetch result
    import base64
    helper_b64 = base64.b64encode(_REMOTE_QC.encode()).decode()
    out = _ssh(
        f"cd {QC_DIR} && "
        f"echo {helper_b64} | base64 -d > /tmp/qc_one.py && "
        f"ffmpeg -y -v error -i {remote_name} "
        f"-c copy -movflags +faststart {remote_fast} && "
        f"python3 /tmp/qc_one.py {remote_fast} /tmp/qc_result.json && "
        f"cat /tmp/qc_result.json")

    parsed = json.loads(out)
    content = parsed["content"]
    m = re.search(r"Score:\s*(\d+)\s*/\s*10", content)
    if not m:
        raise RuntimeError(f"no score parsed from critique: {content[-200:]}")
    score = int(m.group(1))
    threshold = THRESHOLDS[genre]
    verdict = "PASS" if score >= threshold else "REJECT"
    return {
        "critic": "qwen38-27b-Q4_K_M.gguf (llama-server, 3090 :8000)",
        "score": score,
        "verdict": f"{verdict} ({genre} threshold {threshold})",
        "summary": content[:600],
        "latency_secs": parsed.get("latency"),
    }


if __name__ == "__main__":
    video, run_json, genre = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        qc = critique(video, genre)
    except HostConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2)
    rec = json.loads(Path(run_json).read_text())
    rec["qc"] = qc
    Path(run_json).write_text(json.dumps(rec, indent=2, default=str))
    print(f"QC {qc['score']}/10 — {qc['verdict']}")
