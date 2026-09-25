#!/usr/bin/env python3
"""Run WanGP's real RIFE v4.26 temporal upsampler on a short video."""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import torch

from postprocessing.rife.inference import temporal_interpolation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("frame_template", type=Path)
    parser.add_argument("model", type=Path)
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

    # WanGP expects uint8 C,T,H,W. RIFE emits 2N-1 frames for x2.
    sample = torch.from_numpy(frames).permute(3, 0, 1, 2).contiguous()
    output = temporal_interpolation(
        str(args.model),
        sample,
        1,
        device="cuda",
        rife_version="v4",
    )
    args.frame_template.parent.mkdir(parents=True, exist_ok=True)
    for index in range(output.shape[1]):
        rgb = output[:, index].permute(1, 2, 0).numpy()
        cv2.imwrite(str(args.frame_template % (index + 1)), rgb)
    print(f"source_frames={len(frames)} output_frames={output.shape[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
