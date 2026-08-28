#!/usr/bin/env python3
"""S4 STEP 1 — preflight: verify TTS durations match cut_map, run
diarization validator, check master shas."""
import json, subprocess, hashlib, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILM = ROOT / "films" / "satans-mom"
REPO = ROOT.parent

cut_map = json.loads((FILM / "dialogue/cut_map.json").read_text())
ok = True
print("== durations (ffprobe) vs cut_map ==")
for c in cut_map:
    w = FILM / "dialogue/lines" / c["lines"][0]
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "csv=p=0", str(w)],
        capture_output=True, text=True).stdout.strip())
    match = abs(d - c["duration_s"]) < 0.05
    ok &= match
    print(f"cut{c['cut']}: file={d:.3f}s map={c['duration_s']}s {'OK' if match else 'MISMATCH'}")
    ok &= c["duration_s"] <= 20.0

print("== master shas ==")
for line in (FILM / "masters/shas.txt").read_text().splitlines():
    sha, name = line.split()
    p = FILM / "masters" / name
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    m = actual == sha
    ok &= m
    print(f"{name}: {'OK' if m else 'MISMATCH'}")
m1 = hashlib.sha256(Path("/tmp/s25/master.png").read_bytes()).hexdigest()
print("cut1 /tmp/s25/master.png:", "OK" if m1 == "d7ca20745552a2eb7679a98d59dd8346f7feca418cc8c55bb82aca61e474c7dd" else "MISMATCH")

print("== diarization validator (repo) ==")
sys.path.insert(0, str(REPO))
r = subprocess.run([sys.executable, str(REPO / "scripts/check_diarization.py"),
                    str(FILM / "dialogue/timeline.json")], capture_output=True, text=True)
print(r.stdout[-500:] or r.stderr[-500:])
ok &= r.returncode == 0

print("PREFLIGHT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
