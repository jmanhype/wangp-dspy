#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


SOURCE = Path("/home/straughter/Wan2GP-story-WD-ycjg")
RUN = Path("/home/straughter/wd-ycjg-run")
PYTHON_DEPS = RUN / "python-deps/packages"
CONTROL = RUN / "inputs/control.mp4"
MASK = RUN / "inputs/control-mask.mp4"

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.chdir(SOURCE)
sys.path.insert(0, str(PYTHON_DEPS))
sys.path.insert(0, str(SOURCE))

from shared.magic_mask import generate_video_mask  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


generated, keywords = generate_video_mask(
    str(CONTROL),
    "person",
    colorize_objects=True,
    max_colored_objects=1,
)
shutil.copyfile(generated, MASK)
probe = subprocess.run(
    ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(MASK)],
    check=True,
    text=True,
    capture_output=True,
).stdout
(RUN / "inputs/control-mask.ffprobe.json").write_text(probe)
record = {
    "schema_version": "wangp-dspy.wd-ycjg.mask-preparation/v1",
    "source": str(CONTROL),
    "source_sha256": sha256(CONTROL),
    "generated_mask_source": generated,
    "mask": str(MASK),
    "mask_sha256": sha256(MASK),
    "keywords": keywords,
    "colorized": True,
    "max_colored_objects": 1,
    "download_bytes": 0,
}
(RUN / "host-logs/20-mask-preparation.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
