#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path


RUN = Path("/home/straughter/wd-28i5-run")
OPERATIONS = {
    "retake": ("retake-probe", "seed3604"),
    "edit": ("edit-probe", "seed3605"),
    "repaint": ("repaint-probe", "seed3607"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


for operation, (probe, seed) in OPERATIONS.items():
    matches = list((RUN / "boundaries/probe-batch").glob(f"*{seed}*.mp4"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {probe} seed match, found {matches}")
    source = matches[0]
    out = RUN / f"outputs/{operation}"
    out.mkdir(parents=True, exist_ok=True)
    final = out / f"wd_28i5_{operation}.mp4"
    shutil.copyfile(source, final)
    (out / f"wd_28i5_{operation}.sha256").write_text(f"{sha(final)}  {final.name}\n")
    with (out / f"wd_28i5_{operation}.ffprobe.json").open("w") as stream:
        subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(final)], check=True, stdout=stream)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(final), "-vf", "fps=3,scale=240:-1,tile=3x3", "-frames:v", "1", str(out / "contact-sheet.jpg")], check=True)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(final), "-update", "1", "-frames:v", "1", str(out / "first-frame.png")], check=True)
    (out / "output-path.txt").write_text(f"source={source}\nfinal={final}\n")
