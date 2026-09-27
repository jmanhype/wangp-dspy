#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OPERATIONS = {
    "extend": ("extend-probe", "seed3301"),
    "retake": ("retake-probe", "seed3303"),
    "edit": ("edit-probe", "seed3304"),
    "repaint": ("repaint-probe", "seed3305"),
    "recast": ("recast-probe", "seed3306"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


for operation, (probe, seed) in OPERATIONS.items():
    matches = list((ROOT / "boundaries" / probe).glob(f"*{seed}*.mp4"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {probe} seed match, found {matches}")
    source = matches[0]
    out = ROOT / f"outputs/{operation}"
    out.mkdir(parents=True, exist_ok=True)
    final = out / f"wd_8h6p_{operation}.mp4"
    shutil.copyfile(source, final)
    (out / f"wd_8h6p_{operation}.sha256").write_text(f"{sha(final)}  {final.name}\n")
    subprocess.run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(final),
    ], check=True, stdout=(out / f"wd_8h6p_{operation}.ffprobe.json").open("w"))
    subprocess.run([
        "ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(final),
        "-vf", "fps=6,scale=240:-1,tile=4x2", "-frames:v", "1", str(out / "contact-sheet.jpg"),
    ], check=True)
    subprocess.run([
        "ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(final),
        "-update", "1", "-frames:v", "1", str(out / "first-frame.png"),
    ], check=True)
    (out / "output-path.txt").write_text(f"source={source}\nfinal={final}\n")
