#!/usr/bin/env python3
"""S4 STEP 4b — remux REAL TTS over each rendered cut (G4: never trust H3 audio).

Reads jobs.json; for each cut with a local render in renders/, strips the
render's audio and muxes the authored edge-tts guide wav. Idempotent: skips
cuts whose remux already exists. Prints per-cut durations.
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILM = ROOT / "films" / "satans-mom"
RENDERS = FILM / "renders"
REMUXED = FILM / "remux"
REMUXED.mkdir(exist_ok=True)

def sh(argv, timeout=600):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)

jobs = json.loads((FILM / "jobs/jobs.json").read_text())
missing = []
for j in jobs:
    c = j["cut"]
    vid = RENDERS / f"cut{c}.mp4"
    out = REMUXED / f"cut{c}.mp4"
    if not vid.exists():
        missing.append(c)
        print(f"cut{c}: NO LOCAL RENDER — skipped")
        continue
    if out.exists():
        print(f"cut{c}: remux already exists — skip")
        continue
    wav = FILM / "dialogue" / j["guide_wav"]
    r = sh(["ffmpeg", "-y", "-i", str(vid), "-i", str(wav),
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
            "-c:a", "aac", "-shortest", str(out)])
    if r.returncode != 0:
        print(f"cut{c}: REMUX FAILED\n{r.stderr[-500:]}"); sys.exit(1)
    d = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "csv=p=0", str(out)]).stdout.strip()
    print(f"cut{c}: remuxed with real TTS, {d}s")

if missing:
    print(f"INCOMPLETE — missing renders for cuts: {missing}")
else:
    print("ALL CUTS REMUXED")
