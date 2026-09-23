"""Deterministic exact-timeline pacing for director composition."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.director.composition import (
    DirectorError,
    DirectorMode,
    DirectorRequest,
)

FPS = 24
GRID_STEP_FRAMES = 17
GRID_BASE_FRAMES = 5
SUPPORTED_STRATEGIES = frozenset({"even", "beat", "exact_timecode", "window_count"})


@dataclass(frozen=True, slots=True)
class PacingWindow:
    index: int
    start_s: float
    end_s: float
    duration_s: float
    scene_index: int | None = None
    beats: tuple[dict[str, float | str], ...] = ()

    def mapping(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "start_s": self.start_s,
            "end_s": self.end_s,
            "duration_s": self.duration_s,
            "scene_index": self.scene_index,
            "beat_evidence": list(self.beats),
        }


def _error(code: str, observed: str, remediation: str, **metadata: Any) -> DirectorError:
    return DirectorError(
        code, observed, remediation,
        next_command="wgp director plan --request <request> --json",
        metadata=metadata,
    )


def _even(target_s: float, count: int) -> list[tuple[float, float]]:
    duration = target_s / count
    return [((index * duration), ((index + 1) * duration)) for index in range(count)]


def plan_windows(request: DirectorRequest) -> list[PacingWindow]:
    """Map one source to ordered, non-overlapping windows without generation."""

    strategy = request.pacing.strategy
    if strategy not in SUPPORTED_STRATEGIES:
        raise _error(
            "DIRECTOR_PACING_UNSUPPORTED",
            f"pacing strategy {strategy!r} is not supported",
            "Use even, beat, exact_timecode, or window_count pacing.",
            supported=sorted(SUPPORTED_STRATEGIES),
        )
    target_s = request.pacing.target_duration_s
    if request.mode is DirectorMode.screenplay:
        scene_durations = [scene.duration_s for scene in request.screenplay.scenes]
        scene_total = sum(scene_durations)
        if abs(scene_total - target_s) > 1e-6:
            raise _error(
                "DIRECTOR_PACING_CONFLICT",
                f"screenplay duration {scene_total:.9f}s does not match target {target_s:.9f}s",
                "Set pacing.target_duration_s to the sum of all scene durations.",
            )
        boundaries: list[tuple[float, float, int | None]] = []
        cursor = 0.0
        for scene in request.screenplay.scenes:
            end = cursor + scene.duration_s
            boundaries.append((cursor, end, scene.scene_index))
            cursor = end
        spans = boundaries
    elif strategy == "beat":
        if request.mode is not DirectorMode.music_video or request.audio is None:
            raise _error(
                "DIRECTOR_PACING_CONFLICT",
                "beat pacing requires mode=music_video and measured audio beats",
                "Use even pacing for prompt/audio, or supply beat evidence for music_video.",
            )
        beats = sorted(request.audio.beats, key=lambda beat: beat.time_s)
        if not beats:
            raise _error(
                "DIRECTOR_AUDIO_BEATS_MISSING",
                "music-video audio evidence contains zero beats",
                "Record measured beat times in the audio metadata before planning.",
            )
        times = [0.0]
        for beat in beats:
            if beat.time_s <= times[-1] or beat.time_s >= target_s:
                raise _error(
                    "DIRECTOR_AUDIO_BEATS_INVALID",
                    f"beat time {beat.time_s:.9f}s is duplicate, unsorted, or outside the audio duration",
                    "Record strictly increasing beat times inside the measured audio duration.",
                )
            if not beat.measurement.startswith("measured:"):
                raise _error(
                    "DIRECTOR_AUDIO_BEATS_INVALID",
                    f"beat at {beat.time_s:.9f}s lacks measured provenance",
                    "Prefix each beat measurement with the exact measured method and artifact identity.",
                )
            times.append(beat.time_s)
        times.append(target_s)
        spans = [(*span, None) for span in zip(times[:-1], times[1:])]
    elif strategy == "exact_timecode":
        start = request.pacing.exact_start_s
        end = request.pacing.exact_end_s
        if start is None or end is None:
            raise _error(
                "DIRECTOR_PACING_INVALID",
                "exact_timecode pacing requires exact_start_s and exact_end_s",
                "Supply both exact timecodes, or use even pacing.",
            )
        spans = [(start, end, None)]
        target_s = end - start
    else:
        count = request.pacing.clip_count
        if count is None:
            count = max(1, int(-(-target_s // request.pacing.max_clip_s)))
        if target_s / count > request.pacing.max_clip_s:
            raise _error(
                "DIRECTOR_PACING_INVALID",
                f"requested {count} windows exceeds max_clip_s={request.pacing.max_clip_s}",
                "Increase clip_count or max_clip_s while staying within the 60-minute contract.",
            )
        spans = [(*span, None) for span in _even(target_s, count)]

    windows = [
        PacingWindow(
            index=index,
            start_s=round(start, 9),
            end_s=round(end, 9),
            duration_s=round(end - start, 9),
            scene_index=scene_index,
            beats=tuple(
                beat.model_dump(mode="json")
                for beat in (request.audio.beats if request.audio is not None else ())
                if start <= beat.time_s < end
            ),
        )
        for index, (start, end, scene_index) in enumerate(spans, start=1)
    ]
    total = sum(window.duration_s for window in windows)
    if abs(total - target_s) > 1e-6 or any(window.duration_s <= 0 for window in windows):
        raise _error(
            "DIRECTOR_PACING_INVALID",
            f"window total {total:.9f}s does not preserve target {target_s:.9f}s",
            "Use pacing fields that divide the complete source duration without overlap.",
        )
    return windows


__all__ = ["PacingWindow", "SUPPORTED_STRATEGIES", "plan_windows"]
