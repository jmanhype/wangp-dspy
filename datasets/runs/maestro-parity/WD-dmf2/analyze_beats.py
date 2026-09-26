#!/usr/bin/env python3
"""Measure WD-dmf2 music-video beat boundaries from the WD-rous source."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import librosa


BUNDLE = Path(__file__).resolve().parent
SOURCE = (Path(__file__).resolve().parent
          / "../WD-rous/outputs/wd_rous_ace_generate.wav").resolve()


def main() -> int:
    samples, sample_rate = librosa.load(str(SOURCE), mono=True, sr=None)
    duration_s = float(len(samples) / sample_rate)
    tempo, frame_numbers = librosa.beat.beat_track(
        y=samples, sr=sample_rate, trim=False, units="frames", tightness=100
    )
    beat_times = librosa.frames_to_time(frame_numbers, sr=sample_rate)
    onset_envelope = librosa.onset.onset_strength(
        y=samples, sr=sample_rate
    )
    onset_peak = float(onset_envelope.max())
    candidates = [
        float(time_s) for time_s in beat_times
        if 1.0 <= float(time_s) < duration_s - 1.0
    ]
    selected = [
        round(min(candidates, key=lambda value: abs(value - duration_s / 2.0)), 6)
    ] if candidates else []
    selected_confidences = []
    for time_s in selected:
        frame = int(round(float(time_s) * sample_rate / 512))
        raw_confidence = float(onset_envelope[min(frame, len(onset_envelope) - 1)])
        selected_confidences.append(
            round(raw_confidence / onset_peak, 6) if onset_peak > 0 else 0.0
        )
    payload = {
        "schema_version": "wangp-dspy.director-beat-measurement/v1",
        "source_path": str(SOURCE),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "sample_rate_hz": int(sample_rate),
        "channels": 1,
        "duration_s": duration_s,
        "method": "librosa.beat.beat_track(y=mono, sr=native, trim=False, units=frames, tightness=100)",
        "librosa_version": librosa.__version__,
        "all_beat_times_s": [round(float(value), 6) for value in beat_times],
        "selected_beat_times_s": selected,
        "selected_beat_confidences": selected_confidences,
        "onset_peak_strength": onset_peak,
        "tempo_bpm": float(tempo) if not hasattr(tempo, "item") else float(tempo.item()),
    }
    destination = BUNDLE / "planning" / "beat-analysis.json"
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
