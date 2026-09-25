#!/usr/bin/env python3
"""Create the durable WD-r81u finishing batch."""
from __future__ import annotations

import json
from pathlib import Path

from services.jobs.queue import JobQueue


CLIPS = [
    {
        "clip_index": index,
        "status": "pending",
        "log": None,
        "mp4": name,
        "qc_verdict": None,
        "kind": "finishing_generation",
        "family": family,
        "operation": operation,
        "prompt": parameters,
        "seed": seed,
        "video_length": frames,
    }
    for index, (name, family, operation, parameters, seed, frames) in enumerate(
        [
            ("wd_r81u_ffmpeg_interpolation_x2.mp4", "ffmpeg", "interpolation", "minterpolate mci/aobmc/bidir vsbmc x2 24->48 fps", 2931, 56),
            ("wd_r81u_ffmpeg_spatial_x2.mp4", "ffmpeg", "spatial_upscale", "lanczos x2 480x832 -> 960x1664", 2932, 56),
            ("wd_r81u_ffmpeg_film_grain.mp4", "ffmpeg", "film_grain", "noise strength 12 temporal+uniform seed 2935", 2935, 56),
            ("wd_r81u_ffmpeg_codec_h264.mp4", "ffmpeg", "codec", "MP4 H264 CRF18 yuv420p faststart", 2933, 56),
            ("wd_r81u_rife_interpolation_x2.mp4", "rife", "interpolation", "WanGP RIFE v4.26 x2 24->48 fps CUDA", 2934, 56),
            ("wd_r81u_film_film_grain.mp4", "film", "film_grain", "WanGP add_film_grain intensity 0.05 saturation 0.5 seed 2936", 2936, 56),
            ("wd_r81u_real_esrgan_spatial_x2.mp4", "real_esrgan", "spatial_upscale", "Real-ESRGAN x4plus NCNN Vulkan scale 2 tile 128", 2937, 56),
        ],
        start=1,
    )
]


def main() -> int:
    bundle = Path(__file__).resolve().parent
    database = bundle / "queue.db"
    if database.exists():
        raise SystemExit(f"refusing to replace existing queue: {database}")
    queue = JobQueue(database)
    try:
        job_id = queue.submit(plan_ref="WD-r81u-finishing-batch-1", clips=CLIPS)
    finally:
        queue.close()
    record = {
        "queue_id": "wangp-JobQueue-WD-r81u",
        "database": "queue.db",
        "job_id": job_id,
        "retry_id": "attempt-1",
        "admission_state": "admitted",
        "preflight": "doctor-preflight-after-download.json",
    }
    (bundle / "queue-record.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
