#!/usr/bin/env python3
"""Verify the 2-shot chained render: per-shot motion thirds + boundary frames.

Runs on the 3090 (python3 + numpy + ffmpeg). Shot 1 = frames [0:56);
shot 2 = frames [56:56+55] (multishot drops shot 2's duplicated first
frame). Evidence:
  - motion thirds per shot (64x36 luma diff, threshold 2.0)
  - boundary frames around the shot1->shot2 junction (55,56,57)
  - luma MAE between junction-adjacent frames: continuation implies
    small frame-to-frame change at the seam relative to in-shot motion;
    a scene reset implies a large seam jump.

Usage: verify_chained.py VIDEO.mp4 OUTDIR [shot1_frames shot2_frames]
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

W, H = 64, 36
SPLITS = (0, 21, 43, 64)
THRESHOLD = 2.0
NAMES = ("left", "center", "right")


def decode(video, w, h):
    p = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-i", video,
         "-vf", f"scale={w}:{h}", "-pix_fmt", "gray",
         "-f", "rawvideo", "-"], capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w)


def thirds(frames):
    d = np.abs(frames[1:].astype(np.int16) - frames[:-1].astype(np.int16))
    return {n: float(d[:, :, SPLITS[i]:SPLITS[i+1]].mean())
            for i, n in enumerate(NAMES)}


def main():
    video, outdir = sys.argv[1], Path(sys.argv[2])
    n1 = int(sys.argv[3]) if len(sys.argv) > 3 else 56
    n2 = int(sys.argv[4]) if len(sys.argv) > 4 else 55
    outdir.mkdir(parents=True, exist_ok=True)
    big = decode(video, 192, 108)
    small = decode(video, W, H)
    total = len(big)
    print(f"total frames: {total}")

    s1, s2 = small[:n1], small[n1:n1 + n2]
    m1, m2 = thirds(s1), thirds(s2)
    alive1 = min(m1.values()) >= THRESHOLD
    alive2 = min(m2.values()) >= THRESHOLD

    # seam analysis on full-res gray frames
    seam = {}
    for a, b in [(n1 - 2, n1 - 1), (n1 - 1, n1), (n1, n1 + 1)]:
        seam[f"{a}->{b}"] = float(np.abs(
            big[a].astype(np.int16) - big[b].astype(np.int16)).mean())
    # reference: mean in-shot consecutive diff for each shot
    big1, big2 = big[:n1], big[n1:n1 + n2]
    inshot1 = float(np.abs(big1[1:].astype(np.int16) - big1[:-1].astype(np.int16)).mean())
    inshot2 = float(np.abs(big2[1:].astype(np.int16) - big2[:-1].astype(np.int16)).mean())

    for i in (n1 - 2, n1 - 1, n1, n1 + 1, n1 + 2):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video,
                        "-vf", f"select=eq(n\\,{i})", "-frames:v", "1",
                        str(outdir / f"frame_{i:04d}.png")], check=True)

    seam_jump = seam[f"{n1-1}->{n1}"]
    ref = max(inshot1, inshot2, 1e-6)
    ratio = seam_jump / ref
    verdict = ("CONTINUES" if seam_jump <= 3 * ref and alive2
               else "RESETS" if seam_jump > 3 * ref
               else "INCONCLUSIVE")
    report = {
        "shot1_thirds": m1, "shot1_alive": alive1,
        "shot2_thirds": m2, "shot2_alive": alive2,
        "seam_diffs": seam, "inshot_mean_diff": {"shot1": inshot1, "shot2": inshot2},
        "seam_jump": seam_jump, "seam_to_inshot_ratio": ratio,
        "verdict": verdict,
    }
    import json
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
