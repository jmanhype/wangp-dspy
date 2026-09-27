#!/usr/bin/env python3
"""Measure WD-obkn film-grain controls from the emitted FFV1 and H.264 bytes."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np


BUNDLE = Path(__file__).resolve().parent
ROOT = BUNDLE.parents[3]
SOURCE = ROOT / "datasets/runs/maestro-parity/WD-r81u/inputs/source.mp4"
LOSSLESS = BUNDLE / "replay/primary-0002-film-grain.mp4"
FINAL = BUNDLE / "outputs/wd_obkn_ffmpeg_film_grain_h264.mp4"
FFMPEG = "/opt/homebrew/bin/ffmpeg"
WIDTH, HEIGHT, FRAMES = 480, 832, 56
YUV_FRAME_BYTES = WIDTH * HEIGHT * 3 // 2


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def decode(path: Path, pixel_format: str, frame_bytes: int) -> bytes:
    argv = (
        FFMPEG, "-nostdin", "-v", "error", "-i", str(path), "-map", "0:v:0",
        "-f", "rawvideo", "-pix_fmt", pixel_format, "-",
    )
    result = subprocess.run(
        argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=300, check=True,
    )
    if len(result.stdout) != frame_bytes * FRAMES:
        raise RuntimeError(
            f"decoded {len(result.stdout)} bytes; expected {frame_bytes * FRAMES}"
        )
    return result.stdout


def normalized_autocorrelation(values: np.ndarray, transpose: bool) -> np.ndarray:
    frames = np.transpose(values, (0, 2, 1)) if transpose else values
    frames = frames.astype(np.float64, copy=False)
    frames -= frames.mean(axis=2, keepdims=True)
    spectrum = np.fft.rfft(frames, axis=2)
    covariance = np.fft.irfft(np.abs(spectrum) ** 2, n=frames.shape[2], axis=2)
    normalizer = frames.var(axis=2).sum(axis=(0, 1)) * frames.shape[2]
    return covariance[:, :, 1:].sum(axis=(0, 1)) / normalizer


def fit_support(autocorrelation: np.ndarray) -> tuple[float, float, float]:
    lags = np.arange(1, 16, dtype=np.float64)
    observations = autocorrelation[:15]
    slope, intercept = np.polyfit(lags, observations, 1)
    support = -1.0 / slope
    rmse = float(np.sqrt(np.mean((observations - (slope * lags + intercept)) ** 2)))
    return float(support), float(rmse), float(autocorrelation[15])


def frame_hashes(raw_yuv: bytes) -> list[str]:
    return [
        hashlib.sha256(raw_yuv[index:index + YUV_FRAME_BYTES]).hexdigest()
        for index in range(0, len(raw_yuv), YUV_FRAME_BYTES)
    ]


def main() -> None:
    source_raw = decode(SOURCE, "yuv420p", YUV_FRAME_BYTES)
    lossless_raw = decode(LOSSLESS, "yuv420p", YUV_FRAME_BYTES)
    final_raw = decode(FINAL, "yuv420p", YUV_FRAME_BYTES)
    luma_count = WIDTH * HEIGHT
    source_y = np.frombuffer(
        source_raw, dtype=np.uint8, count=FRAMES * luma_count,
    ).reshape(FRAMES, HEIGHT, WIDTH).astype(np.int16)
    lossless_y = np.frombuffer(
        lossless_raw, dtype=np.uint8, count=FRAMES * luma_count,
    ).reshape(FRAMES, HEIGHT, WIDTH).astype(np.int16)
    residual_y = lossless_y - source_y

    horizontal = normalized_autocorrelation(residual_y, transpose=True)
    vertical = normalized_autocorrelation(residual_y, transpose=False)
    horizontal_support, horizontal_rmse, horizontal_lag16 = fit_support(horizontal)
    vertical_support, vertical_rmse, vertical_lag16 = fit_support(vertical)

    block_means = residual_y.reshape(
        FRAMES, HEIGHT // 16, 16, WIDTH // 16, 16,
    ).mean(axis=(2, 4)).astype(np.float64)
    block_means -= block_means.mean(axis=2, keepdims=True)
    flattened = block_means.reshape(FRAMES, -1)
    norms = np.linalg.norm(flattened, axis=1)
    temporal_correlation = (flattened @ flattened.T) / np.outer(norms, norms)
    same_phase = []
    different_phase = []
    for first in range(FRAMES):
        for second in range(first + 1, FRAMES):
            values = same_phase if (second - first) % 3 == 0 else different_phase
            values.append(float(temporal_correlation[first, second]))
    persistence_estimate = float(np.median(same_phase))
    different_phase_median = float(np.median(different_phase))

    gbrp_frame_bytes = WIDTH * HEIGHT * 3
    source_gbrp = np.frombuffer(
        decode(SOURCE, "gbrp", gbrp_frame_bytes), dtype=np.uint8,
    ).reshape(3, FRAMES, HEIGHT, WIDTH).astype(np.int16)
    lossless_gbrp = np.frombuffer(
        decode(LOSSLESS, "gbrp", gbrp_frame_bytes), dtype=np.uint8,
    ).reshape(3, FRAMES, HEIGHT, WIDTH).astype(np.int16)
    residual_gbrp = lossless_gbrp - source_gbrp
    residual_blocks_gbrp = residual_gbrp.reshape(
        3, FRAMES, HEIGHT // 16, 16, WIDTH // 16, 16,
    ).mean(axis=(3, 5))
    channel_p99_abs = [
        float(np.quantile(np.abs(residual_blocks_gbrp[channel]), 0.99))
        for channel in range(3)
    ]
    channel_max_abs = [
        int(np.abs(residual_blocks_gbrp[channel]).max()) for channel in range(3)
    ]
    strength_proxy_p99_abs = float(np.mean(channel_p99_abs))
    strength_proxy_max_abs = int(max(channel_max_abs))

    matrices_path = BUNDLE / "measurement-matrices.npz"
    np.savez_compressed(
        matrices_path,
        spatial_autocorrelation_horizontal=np.asarray(horizontal[:32]),
        spatial_autocorrelation_vertical=np.asarray(vertical[:32]),
        temporal_correlation=temporal_correlation,
        block_mean_residual_luma=block_means,
        block_mean_residual_gbrp=residual_blocks_gbrp,
    )
    replay = json.loads((BUNDLE / "replay-execution.json").read_text())
    primary = json.loads((BUNDLE / "primary-execution.json").read_text())

    checks = {
        "source_unchanged": primary["source_unchanged"] is True,
        "lossless_replay_identical": replay["lossless_byte_identical"] is True,
        "h264_replay_identical": replay["final_byte_identical"] is True,
        "horizontal_support_16": 15.0 <= horizontal_support <= 17.0,
        "vertical_support_16": 15.0 <= vertical_support <= 17.0,
        "lag16_decorrelated": abs(horizontal_lag16) <= 0.10 and abs(vertical_lag16) <= 0.10,
        "persistence_0_5": 0.45 <= persistence_estimate <= 0.55,
        "different_phase_decorrelated": abs(different_phase_median) <= 0.05,
        "strength_12_amplitude_window": 8.0 <= strength_proxy_p99_abs <= 14.0,
        "strength_max_bounded": strength_proxy_max_abs <= 24,
    }
    result = {
        "schema": "wangp-dspy.wd-obkn-film-grain-measurement/v1",
        "verdict": "pass" if all(checks.values()) else "fail",
        "inputs": {
            "source": str(SOURCE),
            "lossless_intermediate": str(LOSSLESS),
            "final_h264": str(FINAL),
            "frame_count": FRAMES,
            "width": WIDTH,
            "height": HEIGHT,
        },
        "input_hashes": {
            "source_sha256": file_sha256(SOURCE),
            "lossless_sha256": file_sha256(LOSSLESS),
            "final_sha256": file_sha256(FINAL),
        },
        "algorithm_parameters": {
            "plane_for_support": "decoded yuv420p luma residual",
            "autocorrelation_lags_fitted": [1, 15],
            "support_tolerance": [15.0, 17.0],
            "lag_16_absolute_correlation_tolerance": 0.10,
            "persistence_statistic": "median block-residual correlation for frame pairs whose lag is divisible by three",
            "persistence_tolerance": [0.45, 0.55],
            "different_phase_statistic": "median block-residual correlation for pairs whose lag is not divisible by three",
            "different_phase_absolute_median_tolerance": 0.05,
            "strength_statistic": "mean across GBRP planes of 99th percentile absolute constant-block residual",
            "strength_proxy_tolerance": [8.0, 14.0],
            "strength_max_tolerance": 24,
        },
        "measurements": {
            "horizontal_support_pixels": horizontal_support,
            "horizontal_fit_rmse": horizontal_rmse,
            "horizontal_lag_16_correlation": horizontal_lag16,
            "vertical_support_pixels": vertical_support,
            "vertical_fit_rmse": vertical_rmse,
            "vertical_lag_16_correlation": vertical_lag16,
            "persistence_estimate": persistence_estimate,
            "different_phase_median_correlation": different_phase_median,
            "strength_proxy_p99_abs": strength_proxy_p99_abs,
            "strength_proxy_max_abs": strength_proxy_max_abs,
            "channel_p99_abs": channel_p99_abs,
            "channel_max_abs": channel_max_abs,
        },
        "matrices_path": matrices_path.name,
        "matrices_sha256": file_sha256(matrices_path),
        "decoded_frame_hashes": {
            "source": frame_hashes(source_raw),
            "lossless_intermediate": frame_hashes(lossless_raw),
            "final_h264": frame_hashes(final_raw),
        },
        "checks": checks,
    }
    output = BUNDLE / "measurement-results.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "verdict": result["verdict"],
        "measurements": result["measurements"],
        "checks": checks,
    }, indent=2))
    if result["verdict"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
