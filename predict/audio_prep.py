"""Repo-owned turn-audio preparation for the Ref2VA continuation lane.

The renderer consumes one isolated speaker wav per cut. This module is the
only sanctioned place that turns a source wav into that guide: it probes the
source, trims or tail-pads to the grid-aligned cut duration, applies the
recipe's +9 dB gain, and verifies the resulting duration/RMS before returning
a path. The default runner uses argv lists (no shell); tests and remote hosts can inject a
runner without creating an off-road helper script.
"""
from __future__ import annotations

import math
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence


class AudioPreparationError(ValueError):
    """Typed, fail-closed rejection of an unsafe turn wav."""


@dataclass(frozen=True)
class PreparedTurnAudio:
    """Evidence returned after a turn wav has passed all gates."""

    source_path: str
    output_path: str
    speaker_id: str
    target_duration_s: float
    measured_duration_s: float
    boost_db: float
    rms_db: float
    single_speaker: bool = True

    def __post_init__(self) -> None:
        if not self.speaker_id or not isinstance(self.speaker_id, str):
            raise AudioPreparationError("speaker_id: required")
        if not self.single_speaker:
            raise AudioPreparationError(
                "single_speaker: turn contains more than one speaker")
        if self.target_duration_s <= 0:
            raise AudioPreparationError("target_duration_s: must be > 0")
        if self.measured_duration_s <= 0:
            raise AudioPreparationError("measured_duration_s: must be > 0")
        if self.measured_duration_s + 0.05 < self.target_duration_s:
            raise AudioPreparationError(
                "measured_duration_s: output is shorter than cut duration")
        if self.measured_duration_s > self.target_duration_s + 0.05:
            raise AudioPreparationError(
                "measured_duration_s: output exceeds cut duration")
        if not math.isfinite(self.rms_db) or self.rms_db < -60.0:
            raise AudioPreparationError(
                f"rms_db: silent/invalid turn ({self.rms_db!r})")

    def to_dict(self) -> dict:
        return {
            "source_path": self.source_path,
            "output_path": self.output_path,
            "speaker_id": self.speaker_id,
            "target_duration_s": self.target_duration_s,
            "measured_duration_s": self.measured_duration_s,
            "boost_db": self.boost_db,
            "rms_db": self.rms_db,
            "single_speaker": self.single_speaker,
        }


Runner = Callable[[Sequence[str]], object]


def _subprocess_runner(argv: Sequence[str]):
    return subprocess.run(list(argv), capture_output=True, text=True,
                          check=False)


def _duration_from_probe(result: object, field: str) -> float:
    rc = int(getattr(result, "returncode", 0))
    raw = str(getattr(result, "stdout", "") or "").strip()
    if rc != 0 or not raw:
        raise AudioPreparationError(f"{field}: ffprobe failed")
    try:
        value = float(raw.splitlines()[-1].strip())
    except (TypeError, ValueError) as exc:
        raise AudioPreparationError(
            f"{field}: ffprobe returned non-numeric duration {raw!r}") from exc
    if not math.isfinite(value) or value <= 0:
        raise AudioPreparationError(f"{field}: duration must be > 0")
    return value


_MEAN_VOLUME_RE = re.compile(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB",
                             re.IGNORECASE)


def _rms_from_probe(result: object) -> float:
    rc = int(getattr(result, "returncode", 0))
    text = "\n".join((str(getattr(result, "stderr", "") or ""),
                       str(getattr(result, "stdout", "") or "")))
    match = _MEAN_VOLUME_RE.search(text)
    if rc != 0 or match is None:
        raise AudioPreparationError("rms_db: volumedetect failed")
    return float(match.group(1))


def prepare_turn_audio(
    source_path: str,
    output_path: str,
    *,
    speaker_id: str,
    target_duration_s: float = 2.0,
    boost_db: float = 9.0,
    single_speaker: bool = True,
    min_rms_db: float = -60.0,
    runner: Optional[Runner] = None,
) -> PreparedTurnAudio:
    """Prepare and verify one speaker-isolated wav.

    A source longer than the target is trimmed. A shorter source is padded
    with a silent tail to the target; this is required for grid-aligned H3
    continuation cuts (for example, 2.0s dialogue in a 56-frame/2.333s
    shot).

    ``runner`` receives one argv list for each ffprobe/ffmpeg invocation and
    must return an object with ``returncode``, ``stdout`` and ``stderr``
    attributes (``subprocess.CompletedProcess`` by default).  No shell syntax
    is ever used, so paths containing spaces remain safe.
    """
    if not isinstance(source_path, str) or not os.path.isfile(source_path):
        raise AudioPreparationError(f"source_path: not readable: {source_path}")
    if not isinstance(speaker_id, str) or not speaker_id.strip():
        raise AudioPreparationError("speaker_id: required")
    if not single_speaker:
        raise AudioPreparationError(
            "single_speaker: source must contain exactly one speaker")
    if target_duration_s <= 0:
        raise AudioPreparationError("target_duration_s: must be > 0")
    if abs(float(boost_db) - 9.0) > 0.25:
        raise AudioPreparationError(
            f"boost_db: continuation recipe pins +9 dB, got {boost_db!r}")
    if min_rms_db < -100:
        raise AudioPreparationError("min_rms_db: unreasonable floor")

    run = runner or _subprocess_runner
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    source_probe = run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "default=nw=1:nk=1",
                        source_path])
    source_duration = _duration_from_probe(source_probe, "source_duration_s")
    pad_duration = max(0.0, float(target_duration_s) - source_duration)
    audio_filters = [f"volume={float(boost_db):.2f}dB"]
    if pad_duration > 0.01:
        audio_filters.append(f"apad=pad_dur={pad_duration:.6f}")

    render = run([
        "ffmpeg", "-y", "-i", source_path, "-t", f"{target_duration_s:.6f}",
        "-af", ",".join(audio_filters), "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", str(output),
    ])
    if int(getattr(render, "returncode", 0)) != 0 or not output.is_file():
        raise AudioPreparationError("output_path: ffmpeg trim/boost failed")

    output_probe = run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "default=nw=1:nk=1",
                        str(output)])
    measured_duration = _duration_from_probe(output_probe,
                                             "measured_duration_s")
    if measured_duration > float(target_duration_s) + 0.05:
        raise AudioPreparationError(
            f"measured_duration_s: {measured_duration:.3f}s exceeds cut")

    rms_probe = run(["ffmpeg", "-v", "error", "-i", str(output),
                     "-af", "volumedetect", "-f", "null", "-"])
    rms_db = _rms_from_probe(rms_probe)
    if rms_db < float(min_rms_db):
        raise AudioPreparationError(
            f"rms_db: {rms_db:.2f} dB below minimum {min_rms_db:.2f} dB")

    return PreparedTurnAudio(
        source_path=source_path, output_path=str(output), speaker_id=speaker_id,
        target_duration_s=float(target_duration_s),
        measured_duration_s=measured_duration, boost_db=float(boost_db),
        rms_db=rms_db, single_speaker=True)


__all__ = ["AudioPreparationError", "PreparedTurnAudio", "prepare_turn_audio"]
