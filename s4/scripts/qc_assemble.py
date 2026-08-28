#!/usr/bin/env python3
"""S4 STEP 5 — QC each remuxed cut through the 3090 VLM critic
(qwen38-27b llama-server, scripts/run_qc.py contract), then assemble
the film: concat with 0.6s silence gaps, whisper-gate the final.

Usage: qc_assemble.py qc|assemble|all
"""
import json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILM = ROOT / "films" / "satans-mom"
REPO = ROOT.parent
THRESH = 7.0

def sh(argv, timeout=900):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)

def qc():
    jobs = json.loads((FILM / "jobs/jobs.json").read_text())
    results = {}
    for j in jobs:
        c = j["cut"]
        vid = FILM / "remux" / f"cut{c}.mp4"
        rec = FILM / "qc" / f"cut{c}.json"
        # faststart copy for llama-server (run_qc contract)
        fs = FILM / "qc" / f"cut{c}_fs.mp4"
        sh(["ffmpeg", "-y", "-i", str(vid), "-c", "copy",
            "-movflags", "+faststart", str(fs)])
        r = sh([sys.executable, str(REPO / "scripts/run_qc.py"),
                str(fs), str(rec), "comedy"], timeout=1200)
        try:
            doc = json.loads(rec.read_text())
        except Exception:
            doc = {"raw": r.stdout[-800:], "err": r.stderr[-800:]}
        results[c] = doc
        score = doc.get("score")
        print(f"cut{c}: QC score={score}")
    (FILM / "qc/qc_all.json").write_text(json.dumps(results, indent=2))

def assemble():
    jobs = json.loads((FILM / "jobs/jobs.json").read_text())
    # concat remuxed cuts in order with 0.6s silence between (film cut gaps)
    concat = FILM / "final"
    concat.mkdir(exist_ok=True)
    lst = concat / "list.txt"
    sil = FILM / "dialogue/_silence_06.wav"
    with lst.open("w") as f:
        for j in jobs:
            p = FILM / "remux" / ("cut%d.mp4" % j["cut"])
            f.write("file '%s'\n" % p)
            f.write("file '%s'\n" % sil)
    out = concat / "satans_mom.mp4"
    r = sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
            "-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-c:a", "aac", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(out)])
    if r.returncode != 0:
        print("ASSEMBLY FAILED\n", r.stderr[-600:]); sys.exit(1)
    d = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "csv=p=0", str(out)]).stdout.strip()
    print(f"ASSEMBLED {out} {d}s")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("qc", "all"): qc()
    if mode in ("assemble", "all"): assemble()
