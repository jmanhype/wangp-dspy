"""Chain Plan schema — H3 last-frame chaining plan objects.

Ported (logic only, no ComfyUI dependency) from:
- joeygambino/MiniMax-H3-Multishot-Workflow (last-frame chaining,
  plates stand down after shot 1)
- RwGrid/ComfyUI-MiniMaxH3-Contex-Loop H3_CHAIN_FORMAT_GUIDE
  (Chain Plan JSON: global_prompt + per-clip cards with audio timing,
  speaker attribution, resume-safe state)

Frame math at 24fps on this repo's 17k+5 frame grid (5/22/39/56/73/...
frames) is retained for the legacy multishot chain. The validated Ref2Va
dialogue lane has an explicit continuation_mode: every clip is grid-aligned
from the 56-frame minimum (~2.33s) and no overlap subtraction is applied.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional, Tuple

from predict.job_config import (
    CONTINUATION_FRAMES_MIN,
    normalize_continuation_frame_count,
)

_SN_RE = re.compile(r"^S\d+$")
_STATUS_VALUES = ("pending", "in_progress", "completed", "failed")
_DEFAULT_FPS = 24


class SchemaError(ValueError):
    """Typed chain-plan construction failure."""


@dataclass(frozen=True)
class ChainCharacter:
    """A character with a STABLE SN tag pinned across every clip."""

    name: str
    sn_tag: str
    description: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise SchemaError("character name must be nonempty")
        if not _SN_RE.match(self.sn_tag or ""):
            raise SchemaError(
                f"sn_tag must match SN<digits> (e.g. S1), got {self.sn_tag!r}")
        if not self.description.strip():
            raise SchemaError(f"{self.sn_tag}: description must be nonempty")


@dataclass(frozen=True)
class ClipAudio:
    """Per-clip audio card: source path + timeline placement.

    start_s: offset of this clip in the episode's global audio timeline.
    padded_duration_s: clip length after apad (equals clip duration).
    """

    path: str
    start_s: float
    padded_duration_s: float

    def __post_init__(self) -> None:
        if not self.path.strip():
            raise SchemaError("audio path must be nonempty")
        for attr in ("start_s", "padded_duration_s"):
            v = getattr(self, attr)
            if not isinstance(v, (int, float)) or float(v) < 0:
                raise SchemaError(f"audio {attr} must be >= 0: {v!r}")
        object.__setattr__(self, "start_s", float(self.start_s))
        object.__setattr__(self, "padded_duration_s",
                           float(self.padded_duration_s))


@dataclass(frozen=True)
class ChainClip:
    """One clip card in the Chain Plan.

    previous_clip_end_frame: {"clip_index": int, "frame": int} — the
    previous clip's last frame (0-based), which becomes this clip's
    FIRST frame via the model's trained continuation task. None only
    for clip 1.
    """

    index: int
    shot_prompt: str
    speaker_sn: str
    duration_s: float
    frames: int
    audio: ClipAudio
    seed: int
    end_pose: Optional[str] = None  # natural-language keyframe target
    status: str = "pending"
    previous_clip_end_frame: Optional[Dict[str, int]] = None

    def __post_init__(self) -> None:
        if self.end_pose is not None and not self.end_pose.strip():
            raise SchemaError(
                f"clip {self.index}: end_pose must be nonempty when set")
        if not isinstance(self.index, int) or self.index < 1:
            raise SchemaError(f"clip index must be int >= 1: {self.index!r}")
        if not _SN_RE.match(self.speaker_sn or ""):
            raise SchemaError(
                f"speaker_sn must match SN<digits>, got {self.speaker_sn!r}")
        d = float(self.duration_s)
        if d <= 0:
            raise SchemaError(f"clip {self.index}: duration_s must be > 0")
        object.__setattr__(self, "duration_s", d)
        if not isinstance(self.frames, int) or self.frames <= 0:
            raise SchemaError(
                f"clip {self.index}: frames must be positive int")
        if not isinstance(self.audio, ClipAudio):
            raise SchemaError(f"clip {self.index}: audio must be ClipAudio")
        if self.status not in _STATUS_VALUES:
            raise SchemaError(
                f"clip {self.index}: status must be one of "
                f"{_STATUS_VALUES}, got {self.status!r}")
        p = self.previous_clip_end_frame
        if p is not None:
            if (not isinstance(p, dict) or "clip_index" not in p
                    or "frame" not in p):
                raise SchemaError(
                    f"clip {self.index}: previous_clip_end_frame must be "
                    "{'clip_index': int, 'frame': int}")


@dataclass(frozen=True)
class ChainPlan:
    """Chain Plan JSON root: global prompt + characters + clip cards."""

    global_prompt: str
    characters: Tuple[ChainCharacter, ...] = field(default_factory=tuple)
    clips: Tuple[ChainClip, ...] = field(default_factory=tuple)
    overlap_frames: int = 22
    fps: int = _DEFAULT_FPS
    continuation_mode: bool = False

    def __post_init__(self) -> None:
        if not self.global_prompt.strip():
            raise SchemaError("global_prompt must be nonempty")
        object.__setattr__(self, "characters", tuple(self.characters))
        object.__setattr__(self, "clips", tuple(self.clips))
        if not self.characters:
            raise SchemaError("chain plan needs at least one character")
        if not self.clips:
            raise SchemaError("chain plan needs at least one clip")
        if not isinstance(self.overlap_frames, int) or self.overlap_frames < 0:
            raise SchemaError(f"overlap_frames must be int >= 0")
        if not isinstance(self.continuation_mode, bool):
            raise SchemaError("continuation_mode must be bool")
        if self.continuation_mode and self.overlap_frames != 0:
            raise SchemaError(
                "continuation_mode uses grid-aligned clips and requires "
                "overlap_frames=0")
        tags = [c.sn_tag for c in self.characters]
        if len(set(tags)) != len(tags):
            raise SchemaError(f"duplicate sn_tags in characters: {tags}")
        idxs = [c.index for c in self.clips]
        if idxs != list(range(1, len(idxs) + 1)):
            raise SchemaError(f"clip indices must be 1..N, got {idxs}")

    # ── JSON round-trip ─────────────────────────────────────────────

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, doc: Dict[str, Any]) -> "ChainPlan":
        try:
            chars = tuple(ChainCharacter(**c) for c in doc["characters"])
            clips = []
            for c in doc["clips"]:
                c = dict(c)
                c["audio"] = ClipAudio(**c["audio"])
                clips.append(ChainClip(**c))
            return cls(global_prompt=doc["global_prompt"], characters=chars,
                       clips=tuple(clips),
                       overlap_frames=doc.get("overlap_frames", 22),
                       fps=doc.get("fps", _DEFAULT_FPS),
                       continuation_mode=doc.get("continuation_mode", False))
        except KeyError as e:
            raise SchemaError(f"missing field in chain plan JSON: {e}") from e


def _frames_on_grid(frames: int) -> bool:
    """17k+5 frame grid (5/22/39/56/73/...)."""
    return frames >= 5 and (frames - 5) % 17 == 0


def validate_chain_plan(plan: ChainPlan) -> None:
    """Cross-clip invariants. Raises SchemaError with a named reason."""
    fps = plan.fps
    eps = 1e-6

    known_sns = {c.sn_tag for c in plan.characters}

    for clip in plan.clips:
        # SN tags stable: a clip's speaker_sn must exist in the roster
        # (S1 is always the same character because the roster is the map).
        if clip.speaker_sn not in known_sns:
            raise SchemaError(
                f"clip {clip.index}: speaker_sn {clip.speaker_sn!r} not in "
                f"character roster {sorted(known_sns)} — SN tags must be "
                "stable across clips")
        if clip.status not in ("pending", "in_progress", "completed", "failed"):
            raise SchemaError(
                f"clip {clip.index}: status {clip.status!r} is not "
                "resume-safe (pending|in_progress|completed|failed)")
        # Speaker-attributed prompt must name the speaking SN tag.
        if clip.speaker_sn not in clip.shot_prompt:
            raise SchemaError(
                f"clip {clip.index}: shot_prompt must be speaker-attributed "
                f"(contain {clip.speaker_sn})")
        if plan.continuation_mode:
            if clip.frames != normalize_continuation_frame_count(clip.frames):
                raise SchemaError(
                    f"clip {clip.index}: continuation frames must be "
                    f"grid-aligned from {CONTINUATION_FRAMES_MIN}f, "
                    f"got {clip.frames}")
        else:
            # Frames on-grid. Clip 1 carries its FULL grid length; later
            # clips are overlap-adjusted, so their effective count is
            # checked against the grid in the sequence loop below.
            base = (clip.frames if clip.index == 1
                    else clip.frames + plan.overlap_frames)
            if not _frames_on_grid(base):
                raise SchemaError(
                    f"clip {clip.index}: effective grid length {base}f "
                    f"(frames={clip.frames}, overlap="
                    f"{0 if clip.index == 1 else plan.overlap_frames}) is "
                    "off the 17k+5 grid (5/22/39/56/73/...)")
        # Frames/duration agreement.
        if abs(clip.duration_s * fps - clip.frames) > 0.5:
            raise SchemaError(
                f"clip {clip.index}: frames {clip.frames} != "
                f"duration_s*fps ({clip.duration_s * fps:.1f})")
        # Apad: padded duration equals clip duration.
        if abs(clip.audio.padded_duration_s - clip.duration_s) > eps:
            raise SchemaError(
                f"clip {clip.index}: audio padded_duration_s "
                f"{clip.audio.padded_duration_s} != clip duration "
                f"{clip.duration_s}")

    # Clip 1: full length, no chaining ref.
    first = plan.clips[0]
    full1 = first.frames
    if first.previous_clip_end_frame is not None:
        raise SchemaError(
            "clip 1 must not carry previous_clip_end_frame (nothing "
            "precedes it)")

    # Later clips: overlap-adjusted frame counts + chaining refs.
    expected_start = 0.0
    prev = first
    for clip in plan.clips[1:]:
        expected_frames = clip.frames
        if plan.continuation_mode:
            if expected_frames != normalize_continuation_frame_count(
                    expected_frames):
                raise SchemaError(
                    f"clip {clip.index}: continuation frames must be "
                    f"grid-aligned from {CONTINUATION_FRAMES_MIN}f, "
                    f"got {expected_frames}")
        elif not _frames_on_grid(expected_frames + plan.overlap_frames):
            raise SchemaError(
                f"clip {clip.index}: frames {expected_frames} + overlap "
                f"{plan.overlap_frames} is off the 17k+5 grid — later "
                "clips must be overlap-adjusted grid durations")
        if clip.previous_clip_end_frame is None:
            raise SchemaError(
                f"clip {clip.index}: previous_clip_end_frame required "
                "for every clip after the first (last-frame chaining)")
        ref = clip.previous_clip_end_frame
        if ref["clip_index"] != prev.index:
            raise SchemaError(
                f"clip {clip.index}: previous_clip_end_frame.clip_index "
                f"{ref['clip_index']} != actual previous clip "
                f"{prev.index}")
        if ref["frame"] != prev.frames - 1:
            raise SchemaError(
                f"clip {clip.index}: previous_clip_end_frame.frame "
                f"{ref['frame']} != previous clip's last frame "
                f"({prev.frames - 1})")
        expected_start += prev.duration_s
        prev = clip

    # Recompute cumulative audio starts over full sequence.
    cursor = 0.0
    for clip in plan.clips:
        if abs(clip.audio.start_s - cursor) > eps:
            raise SchemaError(
                f"clip {clip.index}: audio start_s {clip.audio.start_s} "
                f"!= cumulative timeline position {cursor} — audio "
                "timings must align to the total episode duration")
        cursor += clip.duration_s
    _ = full1  # first clip full length is implied by its grid frames


__all__ = [
    "SchemaError", "ChainCharacter", "ClipAudio", "ChainClip", "ChainPlan",
    "validate_chain_plan",
]
