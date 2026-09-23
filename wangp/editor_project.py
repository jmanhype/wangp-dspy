"""Typed, non-destructive multi-track editor project model."""
from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


PROJECT_SCHEMA = "wangp-dspy.editor-project/v1"
_SHA256 = re.compile(r"[0-9a-f]{64}")


class EditorProjectError(ValueError):
    """A typed, fail-closed editor project rejection."""

    def __init__(
        self,
        code: str,
        observed: str,
        remediation: str,
        *,
        next_command: str = "wgp editor validate --project <project> --json",
        **metadata: Any,
    ) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation
        self.next_command = next_command
        self.metadata = dict(metadata)


class TrackKind(str, Enum):
    video = "video"
    audio = "audio"
    image = "image"
    text = "text"


class TransitionKind(str, Enum):
    cut = "cut"
    dissolve = "dissolve"
    dip = "dip"
    wipe = "wipe"


class ReviewDecision(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    comment = "comment"


class SourceAsset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    asset_id: str = Field(min_length=1)
    kind: TrackKind
    path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    byte_size: int = Field(gt=0)

    @field_validator("sha256")
    @classmethod
    def _hash(cls, value: str) -> str:
        if _SHA256.fullmatch(value) is None:
            raise ValueError("source sha256 must be 64 lowercase hexadecimal characters")
        return value


class Clip(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    clip_id: str = Field(min_length=1)
    kind: TrackKind
    source_id: str | None = None
    label: str = Field(min_length=1)
    text: str | None = None
    timeline_start_s: float = Field(ge=0.0)
    timeline_duration_s: float = Field(gt=0.0, le=60 * 60)
    source_in_s: float = Field(ge=0.0)
    source_out_s: float = Field(gt=0.0)

    @model_validator(mode="after")
    def _source_shape(self) -> "Clip":
        if self.source_out_s <= self.source_in_s:
            raise ValueError("source_out_s must be greater than source_in_s")
        if self.kind is TrackKind.text:
            if self.source_id is not None or not self.text:
                raise ValueError("text clips use inline text and no source_id")
        elif self.source_id is None or self.text is not None:
            raise ValueError(f"{self.kind.value} clips require source_id and forbid inline text")
        return self


class Track(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    track_id: str = Field(min_length=1)
    kind: TrackKind
    name: str = Field(min_length=1)
    order: int = Field(ge=0)
    clips: tuple[Clip, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def _clips_match_and_do_not_overlap(self) -> "Track":
        for clip in self.clips:
            if clip.kind is not self.kind:
                raise ValueError(f"clip {clip.clip_id} does not match track kind")
        ordered = sorted(self.clips, key=lambda clip: clip.timeline_start_s)
        if tuple(ordered) != self.clips:
            raise ValueError("track clips must be stored in timeline order")
        for left, right in zip(self.clips, self.clips[1:], strict=False):
            if left.timeline_start_s + left.timeline_duration_s > right.timeline_start_s + 1e-9:
                raise ValueError(f"clips {left.clip_id} and {right.clip_id} overlap")
        return self


class Transition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    transition_id: str = Field(min_length=1)
    kind: TransitionKind
    from_clip_id: str
    to_clip_id: str
    duration_s: float = Field(ge=0.0, le=10.0)


class ReviewMark(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mark_id: str = Field(min_length=1)
    clip_id: str
    decision: ReviewDecision
    reviewer: str = Field(min_length=1)
    comment: str
    revision: int = Field(ge=0)


def _validated_update(model: BaseModel, model_type: type[BaseModel], **changes: Any) -> BaseModel:
    payload = model.model_dump()
    payload.update(changes)
    return model_type.model_validate(payload)


class EditorProject(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str
    name: str = Field(min_length=1)
    reviewer: str = Field(min_length=1)
    revision: int = Field(ge=0)
    sources: tuple[SourceAsset, ...] = Field(default_factory=tuple)
    tracks: tuple[Track, ...] = Field(min_length=1)
    transitions: tuple[Transition, ...] = Field(default_factory=tuple)
    review_marks: tuple[ReviewMark, ...] = Field(default_factory=tuple)

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != PROJECT_SCHEMA:
            raise ValueError(f"schema_version must be {PROJECT_SCHEMA!r}")
        return value

    @model_validator(mode="after")
    def _references(self) -> "EditorProject":
        source_ids = {source.asset_id for source in self.sources}
        if len(source_ids) != len(self.sources):
            raise ValueError("source asset_id values must be unique")
        track_ids = {track.track_id for track in self.tracks}
        if len(track_ids) != len(self.tracks):
            raise ValueError("track_id values must be unique")
        if sorted(track.order for track in self.tracks) != list(range(len(self.tracks))):
            raise ValueError("track order values must be consecutive from zero")
        clip_ids: set[str] = set()
        clip_track: dict[str, TrackKind] = {}
        for track in self.tracks:
            for clip in track.clips:
                if clip.clip_id in clip_ids:
                    raise ValueError(f"duplicate clip_id {clip.clip_id}")
                clip_ids.add(clip.clip_id)
                clip_track[clip.clip_id] = track.kind
                if clip.source_id is not None and clip.source_id not in source_ids:
                    raise ValueError(f"clip {clip.clip_id} references unknown source")
        for transition in self.transitions:
            if transition.from_clip_id not in clip_ids or transition.to_clip_id not in clip_ids:
                raise ValueError(f"transition {transition.transition_id} references an unknown clip")
            if clip_track[transition.from_clip_id] is not TrackKind.video:
                raise ValueError("video transitions must reference video clips")
            if transition.kind is TransitionKind.cut and transition.duration_s != 0.0:
                raise ValueError("cut transition duration must be zero")
        for mark in self.review_marks:
            if mark.clip_id not in clip_ids:
                raise ValueError(f"review mark {mark.mark_id} references an unknown clip")
        return self

    def _with_tracks(self, tracks: tuple[Track, ...]) -> "EditorProject":
        return _validated_update(self, EditorProject, **{
            "tracks": [track.model_dump() for track in tracks],
            "revision": self.revision + 1,
        })

    def _track(self, track_id: str) -> Track:
        return next(track for track in self.tracks if track.track_id == track_id)

    def _replace_in_track(self, track_id: str, clips: tuple[Clip, ...]) -> "EditorProject":
        changed = tuple(
            _validated_update(track, Track, clips=[clip.model_dump() for clip in clips])
            if track.track_id == track_id else track
            for track in self.tracks
        )
        return self._with_tracks(changed)

    def add_clip(self, track_id: str, clip: Clip) -> "EditorProject":
        track = self._track(track_id)
        return self._replace_in_track(track_id, tuple(sorted((*track.clips, clip), key=lambda item: item.timeline_start_s)))

    def replace_clip(self, clip: Clip) -> "EditorProject":
        for track in self.tracks:
            if any(item.clip_id == clip.clip_id for item in track.clips):
                clips = tuple(clip if item.clip_id == clip.clip_id else item for item in track.clips)
                return self._replace_in_track(track.track_id, tuple(sorted(clips, key=lambda item: item.timeline_start_s)))
        raise EditorProjectError("EDITOR_CLIP_NOT_FOUND", f"clip does not exist: {clip.clip_id}", "Edit a clip in this project.")

    def move_clip(self, clip_id: str, timeline_start_s: float) -> "EditorProject":
        for track in self.tracks:
            clip = next((item for item in track.clips if item.clip_id == clip_id), None)
            if clip is not None:
                return self.replace_clip(clip.model_copy(update={"timeline_start_s": timeline_start_s}))
        raise EditorProjectError("EDITOR_CLIP_NOT_FOUND", f"clip does not exist: {clip_id}", "Edit a clip in this project.")

    def trim_clip(self, clip_id: str, source_in_s: float, source_out_s: float, timeline_duration_s: float) -> "EditorProject":
        for track in self.tracks:
            if any(item.clip_id == clip_id for item in track.clips):
                selected = next(item for item in track.clips if item.clip_id == clip_id)
                return self.replace_clip(_validated_update(selected, Clip, **{
                    "source_in_s": source_in_s,
                    "source_out_s": source_out_s,
                    "timeline_duration_s": timeline_duration_s,
                }))
        raise EditorProjectError("EDITOR_CLIP_NOT_FOUND", f"clip does not exist: {clip_id}", "Edit a clip in this project.")

    def update_text(self, clip_id: str, text: str) -> "EditorProject":
        for track in self.tracks:
            clip = next((item for item in track.clips if item.clip_id == clip_id), None)
            if clip is not None:
                if clip.kind is not TrackKind.text:
                    raise EditorProjectError("EDITOR_CLIP_NOT_TEXT", f"clip is not text: {clip_id}", "Select a text clip.")
                return self.replace_clip(_validated_update(clip, Clip, text=text))
        raise EditorProjectError("EDITOR_CLIP_NOT_FOUND", f"clip does not exist: {clip_id}", "Edit a clip in this project.")

    def reorder_track(self, track_id: str, ordered_clip_ids: tuple[str, ...]) -> "EditorProject":
        track = self._track(track_id)
        by_id = {clip.clip_id: clip for clip in track.clips}
        if set(ordered_clip_ids) != set(by_id) or len(ordered_clip_ids) != len(by_id):
            raise EditorProjectError("EDITOR_REORDER_INVALID", f"reorder is not a permutation of {track_id}", "Pass every clip ID exactly once.")
        starts = sorted(clip.timeline_start_s for clip in track.clips)
        clips = tuple(
            _validated_update(by_id[clip_id], Clip, timeline_start_s=start)
            for clip_id, start in zip(ordered_clip_ids, starts, strict=True)
        )
        return self._replace_in_track(track_id, clips)

    def add_transition(self, transition: Transition) -> "EditorProject":
        return _validated_update(self, EditorProject, **{
            "transitions": [*(item.model_dump() for item in self.transitions), transition.model_dump()],
            "revision": self.revision + 1,
        })

    def add_review_mark(self, mark: ReviewMark) -> "EditorProject":
        return _validated_update(self, EditorProject, **{
            "review_marks": [*(item.model_dump() for item in self.review_marks), mark.model_dump()],
            "revision": self.revision + 1,
        })


def canonical_project_json(project: EditorProject) -> str:
    return json.dumps(project.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def project_sha256(project: EditorProject) -> str:
    return hashlib.sha256(canonical_project_json(project).encode("utf-8")).hexdigest()


__all__ = [
    "Clip", "EditorProject", "EditorProjectError", "PROJECT_SCHEMA", "ReviewDecision",
    "ReviewMark", "SourceAsset", "Track", "TrackKind", "Transition", "TransitionKind",
    "canonical_project_json", "project_sha256",
]
