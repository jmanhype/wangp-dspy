#!/usr/bin/env python3
"""Measure every WD-dmf2 output without regenerating any media."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format",
         "-of", "json", str(path)],
        check=True, text=True, capture_output=True,
    )
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lane_root", type=Path)
    arguments = parser.parse_args()
    root = arguments.lane_root.resolve()
    outputs = root / "outputs"
    records = []
    for path in sorted(outputs.rglob("*.mp4")):
        relative = path.relative_to(root).as_posix()
        payload = probe(path)
        destination = root / "ffprobe" / Path(relative).with_suffix(".json")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        video = next(
            item for item in payload["streams"]
            if item.get("codec_type") == "video"
        )
        audio = next(
            (item for item in payload["streams"]
             if item.get("codec_type") == "audio"), None,
        )
        records.append({
            "path": relative,
            "sha256": sha256(path),
            "duration_s": float(payload["format"]["duration"]),
            "width": int(video["width"]),
            "height": int(video["height"]),
            "fps": video["r_frame_rate"],
            "audio_present": audio is not None,
            "audio_codec": audio.get("codec_name") if audio else None,
            "sample_rate_hz": (
                int(audio["sample_rate"]) if audio else None
            ),
            "channels": int(audio["channels"]) if audio else None,
        })
    document = {
        "schema_version": "wangp-dspy.director-media-measurements/v1",
        "records": records,
    }
    destination = root / "media-qc.json"
    destination.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(document, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
