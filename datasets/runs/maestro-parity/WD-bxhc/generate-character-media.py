#!/usr/bin/env python3
"""Emit model-free WD-bxhc image/video artifacts from one portable anchor."""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


BUNDLE = Path(__file__).resolve().parent
SOURCE = BUNDLE / "inputs" / "appearance-native.png"
IMAGE = BUNDLE / "outputs" / "wd_bxhc_character_image.png"
VIDEO = BUNDLE / "outputs" / "wd_bxhc_character_video.mp4"
AUDIO = BUNDLE / "outputs" / "wd_bxhc_vibevoice_clone_two.prepared.wav"
FIRST_FRAME = BUNDLE / "packages" / "character-video-first-frame.png"
IDENTITY = BUNDLE / "character-media-identity.json"
GATES = BUNDLE / "character-media-objective-gates.json"
FFPROBE_IMAGE = BUNDLE / "ffprobe-wd_bxhc_character_image.json"
FFPROBE_VIDEO = BUNDLE / "ffprobe-wd_bxhc_character_video.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ffprobe(path: Path, destination: Path) -> None:
    subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True, timeout=60, stdout=destination.open("w"), stderr=subprocess.PIPE, text=True,
    )


def average_hash(image: Image.Image, size: int = 8) -> list[int]:
    gray = ImageOps.grayscale(image).resize((size, size), Image.Resampling.LANCZOS)
    values = list(gray.getdata())
    threshold = sum(values) / len(values)
    return [1 if value >= threshold else 0 for value in values]


def hash_similarity(left: list[int], right: list[int]) -> float:
    if len(left) != len(right):
        raise ValueError("hash lengths differ")
    same = sum(a == b for a, b in zip(left, right, strict=True))
    return same / len(left)


def image_statistics(path: Path) -> dict[str, float]:
    gray = ImageOps.grayscale(Image.open(path)).resize((256, 256), Image.Resampling.LANCZOS)
    values = list(gray.getdata())
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return {"mean_luma": mean, "luma_stddev": math.sqrt(variance)}


def main() -> int:
    for path in (IMAGE, VIDEO, FIRST_FRAME, IDENTITY, GATES, FFPROBE_IMAGE, FFPROBE_VIDEO):
        if path.exists():
            raise RuntimeError(f"output namespace is not fresh: {path}")
    shown = json.loads((BUNDLE / "packages" / "character-show.json").read_text(encoding="utf-8"))
    manifest = shown["manifest"]
    appearance = manifest["appearance"][0]

    native = Image.open(SOURCE).convert("RGB")
    scaled = native.resize((native.width * 2, native.height * 2), Image.Resampling.LANCZOS)
    gray = ImageOps.grayscale(scaled)
    tinted = ImageOps.colorize(
        gray, black=(23, 29, 44), mid=(119, 130, 151), white=(236, 239, 246)
    )
    tinted = ImageEnhance.Contrast(tinted).enhance(1.08)
    tinted = ImageEnhance.Color(tinted).enhance(0.86)
    framed = ImageOps.expand(tinted, border=12, fill=(23, 32, 47))
    framed.save(IMAGE, format="PNG", optimize=True)

    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(IMAGE),
        "-i", str(AUDIO),
        "-vf",
        "zoompan=z='min(1+0.0008*on,1.04)':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=544x744,fps=24,format=yuv420p",
        "-t", "5", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "128k", "-ar", "24000", "-ac", "1",
        "-shortest", "-movflags", "+faststart", str(VIDEO),
    ], check=True, timeout=300)
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(VIDEO), "-frames:v", "1",
        str(FIRST_FRAME),
    ], check=True, timeout=60)
    ffprobe(IMAGE, FFPROBE_IMAGE)
    ffprobe(VIDEO, FFPROBE_VIDEO)

    native_hash = average_hash(native)
    image_hash = average_hash(Image.open(IMAGE))
    frame_hash = average_hash(Image.open(FIRST_FRAME))
    image_stats = image_statistics(IMAGE)
    anchor = {
        "package_path": "packages/portable-witness.wgpcharacter",
        "package_sha256": shown["package_sha256"],
        "character_json_identity_sha256": manifest["identity_sha256"],
        "character_id": manifest["character_id"],
        "speaker_label": manifest["speaker_label"],
        "appearance_member": appearance["member"],
        "appearance_sha256": appearance["sha256"],
        "voice_member": manifest["voice"]["member"],
        "voice_sha256": manifest["voice"]["sha256"],
        "voice_binding_id": manifest["voice"]["voice_binding_id"],
        "declared_modes": manifest["continuity"]["modes"],
    }
    identity = {
        "schema": "wangp-dspy.wd-bxhc.character-media-identity/v1",
        "anchor": anchor,
        "image": {
            "path": "outputs/wd_bxhc_character_image.png", "sha256": sha256(IMAGE),
            "operation": "identity_edit", "mode": "image",
        },
        "video": {
            "path": "outputs/wd_bxhc_character_video.mp4", "sha256": sha256(VIDEO),
            "operation": "create", "mode": "video",
            "audio_source": "outputs/wd_bxhc_vibevoice_clone_two.prepared.wav",
            "audio_source_sha256": sha256(AUDIO),
        },
        "generation": {
            "model_used": False,
            "host_gpu_used": False,
            "image_transform": "2x LANCZOS resize, deterministic grayscale tint, contrast/color adjustment, 12px frame",
            "video_transform": "24 fps five-second zoompan from the generated image with the bound two-reference VibeVoice audio",
        },
        "explicit_generated_continuity_row_claimed": False,
    }
    IDENTITY.write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    native_similarity = hash_similarity(native_hash, image_hash)
    cross_mode_similarity = hash_similarity(image_hash, frame_hash)
    gates = {
        "schema": "wangp-dspy.wd-bxhc.character-media-gates/v1",
        "native_to_image_average_hash_similarity": native_similarity,
        "image_to_video_first_frame_average_hash_similarity": cross_mode_similarity,
        "image_statistics": image_stats,
        "image_nonblank": image_stats["luma_stddev"] > 1.0,
        "same_package_sha256": sha256(BUNDLE / "packages" / "portable-witness.wgpcharacter") == anchor["package_sha256"],
        "same_identity_fields": anchor["character_id"] == manifest["character_id"]
        and anchor["speaker_label"] == manifest["speaker_label"]
        and anchor["appearance_sha256"] == appearance["sha256"]
        and anchor["voice_sha256"] == manifest["voice"]["sha256"]
        and anchor["voice_binding_id"] == manifest["voice"]["voice_binding_id"]
        and anchor["declared_modes"] == ["image", "video"],
    }
    GATES.write_text(json.dumps(gates, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"identity": identity, "gates": gates}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
