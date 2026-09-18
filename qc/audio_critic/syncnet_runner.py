"""Host-side SyncNet v2 audiovisual synchrony runner.

The CLI consumes one native cut and a normalized speaker-mouth bbox, creates
three deterministic face crops around that bbox, compares SyncNet audio/lip
embeddings, and emits one JSON evidence object.  It is intended for the
WanGP Python environment (torch/OpenCV) through RenderHost.run_argv.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
from scipy.fft import dct
from scipy.io import wavfile


SYNCNET_MODEL_URL = (
    "https://www.robots.ox.ac.uk/~vgg/software/lipsync/data/"
    "syncnet_v2.model")
SYNCNET_MODEL_SHA256 = (
    "961e8696f888fce4f3f3a6c3d5b3267cf5b343100b238e79b2659bff2c605442")
SYNCNET_METHOD = "syncnet_v2_multicrop/v1"
DEFAULT_CROP_FACTORS = (4.0, 8.0, 12.0)
DEFAULT_MAX_OFFSET_FRAMES_25FPS = 10
DEFAULT_MIN_CONFIDENCE = 1.0


class SyncNetRunnerError(ValueError):
    """Typed host-runner failure."""


@dataclass(frozen=True)
class CropResult:
    factor: float
    offset_frames: int
    confidence: float
    minimum_distance: float


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _framesig(signal: np.ndarray, frame_len: int, frame_step: int) -> np.ndarray:
    if len(signal) <= frame_len:
        count = 1
    else:
        count = 1 + int(math.ceil((len(signal) - frame_len) / frame_step))
    padded_len = (count - 1) * frame_step + frame_len
    padded = np.concatenate(
        [signal, np.zeros(padded_len - len(signal), dtype=signal.dtype)])
    rows = np.tile(np.arange(frame_len), (count, 1))
    columns = np.tile(
        np.arange(0, count * frame_step, frame_step), (frame_len, 1)).T
    return padded[rows + columns]


def _filterbanks(nfilt: int, nfft: int, samplerate: int) -> np.ndarray:
    def hz_to_mel(value):
        return 2595.0 * np.log10(1.0 + value / 700.0)

    def mel_to_hz(value):
        return 700.0 * (10.0 ** (value / 2595.0) - 1.0)

    mel_points = np.linspace(
        hz_to_mel(0.0), hz_to_mel(samplerate / 2.0), nfilt + 2)
    bins = np.floor((nfft + 1) * mel_to_hz(mel_points) / samplerate)
    result = np.zeros((nfilt, nfft // 2 + 1), dtype=np.float64)
    for index in range(nfilt):
        left, center, right = bins[index:index + 3]
        for bin_index in range(int(left), int(center)):
            result[index, bin_index] = (
                (bin_index - left) / (center - left))
        for bin_index in range(int(center), int(right)):
            result[index, bin_index] = (
                (right - bin_index) / (right - center))
    return result


def mfcc(signal: np.ndarray, samplerate: int = 16000) -> np.ndarray:
    """Match python_speech_features.mfcc defaults used by SyncNet v2."""
    emphasized = np.concatenate(
        [signal[:1], signal[1:] - 0.97 * signal[:-1]])
    frames = _framesig(emphasized, 400, 160)
    spectrum = np.square(np.abs(np.fft.rfft(frames, 512))) / 512.0
    energy = np.sum(spectrum, axis=1)
    energy[energy == 0] = np.finfo(float).eps
    features = np.dot(spectrum, _filterbanks(26, 512, samplerate).T)
    features[features == 0] = np.finfo(float).eps
    coefficients = dct(
        np.log(features), type=2, axis=1, norm="ortho")[:, :13]
    lift = 1 + (22.0 / 2.0) * np.sin(np.pi * np.arange(13) / 22.0)
    coefficients *= lift
    coefficients[:, 0] = np.log(energy)
    return coefficients


def _read_video(path: Path) -> tuple[list[np.ndarray], float]:
    import cv2

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise SyncNetRunnerError(f"video is unreadable: {path}")
    frames = []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frames.append(frame)
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 24.0)
    capture.release()
    if len(frames) < 8:
        raise SyncNetRunnerError("at least eight video frames are required")
    if fps <= 0:
        raise SyncNetRunnerError("video FPS must be positive")
    return frames, fps


def _extract_audio(path: Path, destination: Path) -> tuple[int, np.ndarray]:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(path), "-vn", "-ac", "1",
        "-acodec", "pcm_s16le", "-ar", "16000", str(destination),
    ], check=True)
    return wavfile.read(destination)


def _crop_plan(bbox: Sequence[float], size: tuple[int, int],
               factor: float) -> tuple[int, int, int, int]:
    x, y, width, height = (float(value) for value in bbox)
    frame_width, frame_height = size
    center_x = (x + width / 2.0) * frame_width
    center_y = (y + height / 2.0) * frame_height
    crop_width = max(72, int(round(width * factor * frame_width)))
    crop_height = max(72, int(round(height * factor * frame_height)))
    x0 = max(0, min(frame_width - crop_width, int(center_x - crop_width / 2)))
    y0 = max(0, min(frame_height - crop_height, int(center_y - crop_height / 2)))
    return x0, y0, crop_width, crop_height


def _resampled_crop_frames(frames: list[np.ndarray], fps: float,
                           bbox: Sequence[float], factor: float,
                           output_size: int = 224) -> np.ndarray:
    import cv2

    count = int(math.ceil(len(frames) * fps / 25.0))
    source_size = (frames[0].shape[1], frames[0].shape[0])
    x0, y0, width, height = _crop_plan(bbox, source_size, factor)
    output = []
    for target_index in range(count):
        source_index = min(
            len(frames) - 1,
            int(round(target_index * fps / 25.0)))
        crop = frames[source_index][y0:y0 + height, x0:x0 + width]
        output.append(cv2.resize(crop, (output_size, output_size)))
    video = np.stack(output).astype(np.float32).transpose(3, 0, 1, 2)
    return np.expand_dims(video, axis=0)


def _evaluate_crops(video_path: Path, bbox: Sequence[float],
                    model_path: Path, factors: Sequence[float],
                    batch_size: int, vshift: int) -> list[CropResult]:
    import torch
    from qc.audio_critic.syncnet_model import SyncNetS

    if _sha256(model_path) != SYNCNET_MODEL_SHA256:
        raise SyncNetRunnerError("SyncNet model SHA-256 mismatch")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SyncNetS().to(device)
    state = torch.load(
        str(model_path), map_location=device, weights_only=True)
    model.load_state_dict(state)
    model.eval()
    frames, fps = _read_video(video_path)
    with tempfile.TemporaryDirectory(prefix="wangp-syncnet-") as temporary:
        sample_rate, audio = _extract_audio(
            video_path, Path(temporary) / "audio.wav")
        if sample_rate != 16000:
            raise SyncNetRunnerError("SyncNet requires 16 kHz audio")
        audio_features = mfcc(audio.astype(np.float64) / 32768.0).T
        results = []
        for factor in factors:
            video = _resampled_crop_frames(frames, fps, bbox, factor)
            usable = min(
                int(video.shape[2]), math.floor(len(audio) / 640)) - 4
            if usable < 2:
                raise SyncNetRunnerError("audio/video cut is too short")
            lip_features = []
            audio_projection = []
            with torch.no_grad():
                for start in range(0, usable, batch_size):
                    stop = min(usable, start + batch_size)
                    lip_batch = np.concatenate(
                        [video[:, :, index:index + 5]
                         for index in range(start, stop)], axis=0)
                    audio_batch = np.asarray(np.concatenate(
                        [audio_features[np.newaxis, np.newaxis, :,
                         index * 4:index * 4 + 20]
                         for index in range(start, stop)], axis=0),
                        dtype=np.float32)
                    lip_features.append(model.forward_lip(
                        torch.from_numpy(lip_batch).to(device)).cpu())
                    audio_projection.append(model.forward_aud(
                        torch.from_numpy(audio_batch).to(device)).cpu())
            lip = torch.cat(lip_features)
            speech = torch.cat(audio_projection)
            padded = torch.nn.functional.pad(speech, (0, 0, vshift, vshift))
            distances = []
            for index in range(len(lip)):
                window = padded[index:index + vshift * 2 + 1]
                distances.append(torch.nn.functional.pairwise_distance(
                    lip[index:index + 1].repeat(len(window), 1), window))
            mean_distance = torch.mean(torch.stack(distances, 1), 1)
            minimum, selected = torch.min(mean_distance, 0)
            confidence = torch.median(mean_distance) - minimum
            results.append(CropResult(
                factor=float(factor),
                offset_frames=int(vshift - int(selected.item())),
                confidence=float(confidence.item()),
                minimum_distance=float(minimum.item())))
        return results


def aggregate_results(results: Sequence[CropResult]) -> dict:
    offsets = [item.offset_frames for item in results]
    confidences = [item.confidence for item in results]
    offset = int(np.median(offsets))
    confidence = float(np.median(confidences))
    passed = (
        abs(offset) <= DEFAULT_MAX_OFFSET_FRAMES_25FPS
        and confidence >= DEFAULT_MIN_CONFIDENCE)
    return {
        "method": SYNCNET_METHOD,
        "model_sha256": SYNCNET_MODEL_SHA256,
        "crop_factors": [item.factor for item in results],
        "crop_results": [item.__dict__ for item in results],
        "offset_frames_25fps": offset,
        "offset_seconds": round(offset / 25.0, 6),
        "confidence": round(confidence, 6),
        "pass_bar": {
            "max_abs_offset_frames_25fps":
                DEFAULT_MAX_OFFSET_FRAMES_25FPS,
            "min_confidence": DEFAULT_MIN_CONFIDENCE,
        },
        "passed": passed,
        "phonetic_sync_verified": False,
    }


def run(video_path: str | Path, bbox: Sequence[float],
        model_path: str | Path,
        video_sha256: str | None = None) -> dict:
    path = Path(video_path)
    model = Path(model_path)
    if not path.is_file() or not model.is_file():
        raise SyncNetRunnerError("video and SyncNet model paths are required")
    if video_sha256 is not None and _sha256(path) != video_sha256:
        raise SyncNetRunnerError("video SHA-256 mismatch")
    results = _evaluate_crops(
        path, bbox, model, DEFAULT_CROP_FACTORS, batch_size=10, vshift=10)
    evidence = aggregate_results(results)
    evidence["video_path"] = str(path)
    evidence["speaker_mouth_bbox"] = [float(value) for value in bbox]
    if video_sha256 is not None:
        evidence["video_sha256"] = video_sha256
    return evidence


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="syncnet-runner")
    parser.add_argument("--video", required=True)
    parser.add_argument("--bbox", nargs=4, type=float, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--video-sha256")
    args = parser.parse_args(argv)
    try:
        payload = run(
            args.video, args.bbox, args.model,
            video_sha256=args.video_sha256)
    except Exception as exc:
        print(json.dumps({
            "status": "failed", "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({**payload, "status": "complete"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "SYNCNET_METHOD", "SYNCNET_MODEL_SHA256", "SYNCNET_MODEL_URL",
    "SyncNetRunnerError", "aggregate_results", "run",
]
