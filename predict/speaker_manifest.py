"""Versioned speaker/turn manifest for single-speaker Ref2VA renders."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


class SpeakerManifestError(ValueError):
    """Typed rejection of missing or ambiguous speaker attribution."""


SCHEMA = "wangp-dspy.speaker-manifest/v1"
FILENAME = "speaker_manifest.json"


@dataclass(frozen=True)
class SpeakerTurn:
    turn_index: int
    speaker_id: str
    picture_n: int
    audio_path: str
    intended_text: str

    def __post_init__(self):
        if self.turn_index < 1:
            raise SpeakerManifestError("turn_index: must start at 1")
        if not isinstance(self.speaker_id, str) or not re.fullmatch(
                r"S\d+", self.speaker_id):
            raise SpeakerManifestError(
                f"speaker_id: expected SN tag (S1, S2, ...), got {self.speaker_id!r}")
        if self.picture_n < 1:
            raise SpeakerManifestError("picture_n: must be positive")
        if not isinstance(self.audio_path, str) or not self.audio_path:
            raise SpeakerManifestError("audio_path: required")
        if not isinstance(self.intended_text, str) or not self.intended_text.strip():
            raise SpeakerManifestError("intended_text: required")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SpeakerManifest:
    turns: tuple[SpeakerTurn, ...]
    schema: str = SCHEMA

    def __post_init__(self):
        if self.schema != SCHEMA:
            raise SpeakerManifestError(
                f"schema: expected {SCHEMA!r}, got {self.schema!r}")
        if not self.turns:
            raise SpeakerManifestError("turns: at least one turn is required")
        indexes = [t.turn_index for t in self.turns]
        if indexes != list(range(1, len(indexes) + 1)):
            raise SpeakerManifestError(
                f"turns: indexes must be contiguous from 1, got {indexes}")
        if len({t.speaker_id for t in self.turns}) < 1:
            raise SpeakerManifestError("turns: speaker_id cannot be empty")

    def to_dict(self) -> dict:
        return {"schema": self.schema,
                "turns": [turn.to_dict() for turn in self.turns]}

    @classmethod
    def from_dict(cls, payload: Mapping) -> "SpeakerManifest":
        if not isinstance(payload, Mapping):
            raise SpeakerManifestError("manifest: expected an object")
        try:
            turns = tuple(SpeakerTurn(**turn) for turn in payload["turns"])
            return cls(turns=turns, schema=payload.get("schema", ""))
        except KeyError as exc:
            raise SpeakerManifestError(f"manifest missing key: {exc.args[0]}") from exc


def build_speaker_manifest(turns: Iterable[SpeakerTurn | Mapping]) -> dict:
    normalized = []
    for item in turns:
        normalized.append(item if isinstance(item, SpeakerTurn)
                          else SpeakerTurn(**dict(item)))
    return SpeakerManifest(tuple(normalized)).to_dict()


def write_speaker_manifest(payload: Mapping | SpeakerManifest,
                            render_output: str | Path) -> Path:
    manifest = (payload if isinstance(payload, SpeakerManifest)
                else SpeakerManifest.from_dict(payload))
    path = Path(render_output).parent / FILENAME
    path.write_text(json.dumps(manifest.to_dict(), indent=2,
                               sort_keys=True) + "\n", encoding="utf-8")
    return path


def readback_validate_speaker_manifest(payload: Mapping,
                                       expected: Mapping) -> bool:
    actual = SpeakerManifest.from_dict(payload).to_dict()
    wanted = SpeakerManifest.from_dict(expected).to_dict()
    if actual != wanted:
        raise SpeakerManifestError("speaker manifest readback mismatch")
    return True


__all__ = ["SCHEMA", "FILENAME", "SpeakerManifestError", "SpeakerTurn",
           "SpeakerManifest", "build_speaker_manifest", "write_speaker_manifest",
           "readback_validate_speaker_manifest"]
