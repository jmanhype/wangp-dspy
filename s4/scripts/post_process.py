#!/usr/bin/env python3
"""S4 STEP 4 — post-render: pull mp4s, remux REAL TTS over each cut
(G4: never trust H3 audio — strip it entirely), QC per shot via
3090 VLM (qwen38-27b), write per-cut run records + state updates.

Usage: post_process.py (after render_driver.sh completes)
"""
import json, hashlib, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILM = ROOT / "films" / "satans-mom"
SSH = ["ssh", "-o", "ConnectTimeout=15", "3090"]
THRESH = 7.0  # comedy gate (Larson gag film); surreal floor 4.5 fallback

def sh(argv, **kw):
    return subprocess.run(argv, capture_output=True, text=True, timeout=kw.pop("timeout", 900), **kw)

jobs = json.loads((FILM / "jobs/jobs.json").read_text())
renders = FILM / "renders"; renders.mkdir(exist_ok=True)
remuxed = FILM / "remux"; remuxed.mkdir(exist_ok=True)
qc_dir = FILM / "qc"; qc_dir.mkdir(exist_ok=True)

# 1. pull renders
for j in jobs:
    c = j["cut"]
    src = f"3090:/tmp/s4/render-out/cut{c}.mp4"
    dst = renders / f"cut{c}.mp4"
    r = subprocess.run(["scp", "-q", src, str(dst)], capture_output=True)
    if r.returncode != 0 or not dst.exists():
        print(f"cut{c}: PULL FAILED"); sys.exit(1)
    d = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "csv=p=0", str(dst)]).stdout.strip()
    print(f"cut{c}: pulled, {d}s")

# 2. remux real TTS over video (drop H3 audio entirely — G4)
for j in jobs:
    c = j["cut"]
    vid = renders / f"cut{c}.mp4"
    wav = FILM / "dialogue" / j["guide_wav"]
    out = remuxed / f"cut{c}.mp4"
    r = sh(["ffmpeg", "-y", "-i", str(vid), "-i", str(wav),
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
            "-c:a", "aac", "-shortest", str(out)])
    if r.returncode != 0:
        print(f"cut{c}: REMUX FAILED\n{r.stderr[-400:]}"); sys.exit(1)
    print(f"cut{c}: remuxed with real TTS")

print("PULL+REMUX COMPLETE")
