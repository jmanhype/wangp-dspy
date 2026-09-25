#!/usr/bin/env python3
"""Bound each WD-dmf2 assembly to its exact director target duration."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Sequence


MODES = {
    "prompt": 4.666667,
    "audio": 10.0,
    "music_video": 10.0,
    "screenplay": 5.833333,
}


def run(argv: Sequence[str], log) -> None:
    print(json.dumps(list(argv)), file=log, flush=True)
    subprocess.run(list(argv), stdout=log, stderr=subprocess.STDOUT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lane_root", type=Path)
    arguments = parser.parse_args()
    root = arguments.lane_root.resolve()
    outputs = root / "outputs"
    log_path = root / "wd-dmf2-finalize.native.log"
    with log_path.open("w", encoding="utf-8") as log:
        for mode, duration in MODES.items():
            first = outputs / f"clips/{mode}/clip0001.mp4"
            second = outputs / f"clips/{mode}/clip0002.mp4"
            target = outputs / f"wd_dmf2_{mode}_composition.mp4"
            temporary = target.with_suffix(".bounded.mp4")
            if mode == "prompt":
                filter_complex = "[0:v][1:v]concat=n=2:v=1:a=0[v]"
                maps = ["-map", "[v]", "-an"]
                audio = []
            else:
                filter_complex = (
                    "[0:v][1:v]concat=n=2:v=1:a=0[v];"
                    "[0:a][1:a]concat=n=2:v=0:a=1[a]"
                )
                maps = ["-map", "[v]", "-map", "[a]"]
                audio = [
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                ]
            run([
                "ffmpeg", "-y", "-v", "error", "-i", str(first),
                "-i", str(second), "-filter_complex", filter_complex, *maps,
                "-t", f"{duration:.6f}", "-r", "24",
                "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                "-pix_fmt", "yuv420p", *audio,
                "-movflags", "+faststart", str(temporary),
            ], log)
            temporary.replace(target)
    print(json.dumps({"finalized_modes": sorted(MODES)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
