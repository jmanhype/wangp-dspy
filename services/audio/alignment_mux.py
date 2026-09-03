"""Alignment-mux audio policy (PR feat/ops-hardening).

Whisper both audio tracks (reference guide mux vs drifted re-mux
candidate), compute the median start-time offset across matched
segments, and emit an ffmpeg -itsoffset shift plan for the guide mux.

Tests mock the transcript fn — this module itself has NO whisper
dependency; the transcript callable is injected (production wiring
points it at the S4 faster-whisper seam).
"""
from __future__ import annotations

from typing import Callable, List, Optional, Sequence, Tuple

# shifts below this are considered measurement noise — no shift
DEFAULT_THRESHOLD_S = 0.05

Segment = Tuple[float, float, str]


def compute_alignment_offset(reference: Sequence[Segment],
                             candidate: Sequence[Segment]) -> float:
    """Median per-segment start offset: candidate.start - ref.start,
    matched by order. Positive = candidate runs LATE (shift earlier)."""
    if len(reference) != len(candidate) or not reference:
        raise ValueError(
            f"segment counts must match and be nonempty: "
            f"{len(reference)} vs {len(candidate)}")
    offsets = sorted(c[0] - r[0] for r, c in zip(reference, candidate))
    n = len(offsets)
    mid = n // 2
    return (offsets[mid] if n % 2
            else (offsets[mid - 1] + offsets[mid]) / 2.0)


def alignment_shift_argv(offset_s: float, guide_wav: str,
                         out_wav: str) -> list:
    """The proven shift shape: itsoffset (seconds, 2dp) + stream copy."""
    return ["ffmpeg", "-y", "-itsoffset", f"{offset_s:.2f}",
            "-i", guide_wav, "-c:a", "copy", out_wav]


def alignment_mux(tracks: Sequence[str],
                  transcripts: Callable[[Sequence[str]],
                                        List[List[Segment]]],
                  out_wav: str = "guide_shifted.wav",
                  threshold_s: float = DEFAULT_THRESHOLD_S) -> dict:
    """audio_policy: whisper both tracks, compute the offset, plan the
    guide-mux shift. Returns the plan dict (offset_s, mode,
    shift_argv) — execution of the argv is the caller's host seam."""
    if len(tracks) != 2:
        raise ValueError(
            f"alignment_mux needs exactly 2 tracks (reference, "
            f"candidate), got {len(tracks)}")
    ref_segs, cand_segs = transcripts(list(tracks))
    offset = compute_alignment_offset(ref_segs, cand_segs)
    if abs(offset) < threshold_s:
        return {"mode": "no_shift", "offset_s": offset,
                "shift_argv": None,
                "reference": tracks[0], "candidate": tracks[1]}
    return {"mode": "shift_guide_mux", "offset_s": offset,
            "shift_argv": alignment_shift_argv(offset, tracks[1],
                                               out_wav),
            "reference": tracks[0], "candidate": tracks[1]}


__all__ = ["compute_alignment_offset", "alignment_shift_argv",
           "alignment_mux", "DEFAULT_THRESHOLD_S"]
