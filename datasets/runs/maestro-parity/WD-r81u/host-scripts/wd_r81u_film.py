#!/usr/bin/env python3
"""Run WanGP's real film-grain implementation with a recorded seed."""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import torch

from postprocessing.film_grain import add_film_grain


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("frame_template", type=Path)
    parser.add_argument("--seed", type=int, default=2936)
    parser.add_argument("--intensity", type=float, default=0.05)
    args = parser.parse_args()

    capture = cv2.VideoCapture(str(args.source))
    if not capture.isOpened():
        raise RuntimeError(f"cannot open source: {args.source}")
    frames = []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frames.append(frame)
    capture.release()
    if not frames:
        raise RuntimeError("source contains no decodable frames")

    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    sample = torch.from_numpy(frames).permute(3, 0, 1, 2).contiguous()
    output = add_film_grain(sample, grain_intensity=args.intensity, saturation=0.5)
    args.frame_template.parent.mkdir(parents=True, exist_ok=True)
    for index in range(output.shape[1]):
        rgb = output[:, index].permute(1, 2, 0).numpy()
        cv2.imwrite(str(args.frame_template % (index + 1)), rgb)
    print(f"source_frames={len(frames)} output_frames={output.shape[1]} seed={args.seed} intensity={args.intensity}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
