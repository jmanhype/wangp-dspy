"""Typed operator briefs for no-GPU Wangp film planning."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


CONTENT_BRIEF_SCHEMA = "wangp-dspy.content-brief/v1"
DEFAULT_DURATION_S = 56.0 / 24.0
_SN_TAG = re.compile(r"^S\d+$")
_ALLOWED_KEYS = {
    "schema_version", "title", "premise", "characters", "dialogue",
    "durations_s", "audio_paths",
}


class ContentBriefError(ValueError):
    """Typed rejection of an unsafe or incomplete operator brief."""


@dataclass(frozen=True, slots=True)
class ContentCharacter:
    name: str
    sn_tag: str
    description: str

    def mapping(self) -> dict[str, str]:
        return {
            "name": self.name,
            "sn_tag": self.sn_tag,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class DialogueLine:
    speaker: str
    text: str

    def mapping(self) -> dict[str, str]:
        return {"speaker": self.speaker, "text": self.text}


@dataclass(frozen=True, slots=True)
class ContentBrief:
    """A validated creative brief plus deterministic planning defaults."""

    title: str
    premise: str
    characters: tuple[ContentCharacter, ...]
    dialogue: tuple[DialogueLine, ...]
    durations_s: tuple[float, ...]
    audio_paths: tuple[str, ...] | None
    source_path: Path | None = None

    def mapping(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema_version": CONTENT_BRIEF_SCHEMA,
            "title": self.title,
            "premise": self.premise,
            "characters": [item.mapping() for item in self.characters],
            "dialogue": [item.mapping() for item in self.dialogue],
            "durations_s": list(self.durations_s),
        }
        if self.audio_paths is not None:
            value["audio_paths"] = list(self.audio_paths)
        return value

    @property
    def brief_hash(self) -> str:
        payload = json.dumps(
            self.mapping(), sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(payload).hexdigest()


def _nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContentBriefError(f"{field} must be a non-empty string")
    return value.strip()


def _positive_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContentBriefError(f"{field} must be a positive finite number")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ContentBriefError(f"{field} must be a positive finite number")
    return result


def load_content_brief(path: str | Path) -> ContentBrief:
    """Load and fully validate one operator JSON brief."""

    source = Path(path)
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContentBriefError(f"cannot read content brief {source}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ContentBriefError("content brief must be a JSON object")
    unknown = sorted(set(raw) - _ALLOWED_KEYS)
    if unknown:
        raise ContentBriefError(f"unknown content-brief field(s): {unknown}")
    if raw.get("schema_version") != CONTENT_BRIEF_SCHEMA:
        raise ContentBriefError(
            f"schema_version must be {CONTENT_BRIEF_SCHEMA!r}"
        )

    title = _nonempty(raw.get("title"), "title")
    premise = _nonempty(raw.get("premise"), "premise")

    raw_characters = raw.get("characters")
    if not isinstance(raw_characters, list) or len(raw_characters) < 2:
        raise ContentBriefError("characters must list at least two characters")
    characters: list[ContentCharacter] = []
    names: set[str] = set()
    sn_tags: set[str] = set()
    for index, item in enumerate(raw_characters):
        field = f"characters[{index}]"
        if not isinstance(item, dict):
            raise ContentBriefError(f"{field} must be an object")
        character = ContentCharacter(
            name=_nonempty(item.get("name"), f"{field}.name"),
            sn_tag=_nonempty(item.get("sn_tag"), f"{field}.sn_tag"),
            description=_nonempty(item.get("description"), f"{field}.description"),
        )
        if not _SN_TAG.fullmatch(character.sn_tag):
            raise ContentBriefError(f"{field}.sn_tag must look like S1, S2, ...")
        if character.name in names or character.sn_tag in sn_tags:
            raise ContentBriefError("character names and sn_tags must be unique")
        names.add(character.name)
        sn_tags.add(character.sn_tag)
        characters.append(character)

    raw_dialogue = raw.get("dialogue")
    if not isinstance(raw_dialogue, list) or not raw_dialogue:
        raise ContentBriefError("dialogue must contain at least one turn")
    dialogue: list[DialogueLine] = []
    for index, item in enumerate(raw_dialogue):
        field = f"dialogue[{index}]"
        if not isinstance(item, dict):
            raise ContentBriefError(f"{field} must be an object")
        line = DialogueLine(
            speaker=_nonempty(item.get("speaker"), f"{field}.speaker"),
            text=_nonempty(item.get("text"), f"{field}.text"),
        )
        if line.speaker not in names:
            raise ContentBriefError(
                f"{field}.speaker {line.speaker!r} is not in the character roster"
            )
        dialogue.append(line)

    raw_durations = raw.get("durations_s")
    if raw_durations is None:
        durations = tuple(DEFAULT_DURATION_S for _ in dialogue)
    elif isinstance(raw_durations, list) and len(raw_durations) == len(dialogue):
        durations = tuple(
            _positive_number(value, f"durations_s[{index}]")
            for index, value in enumerate(raw_durations)
        )
    else:
        raise ContentBriefError(
            "durations_s must be absent or contain one positive value per dialogue turn"
        )

    raw_audio = raw.get("audio_paths")
    if raw_audio is None:
        audio_paths: tuple[str, ...] | None = None
    elif isinstance(raw_audio, list) and len(raw_audio) == len(dialogue):
        audio_paths = tuple(
            _nonempty(value, f"audio_paths[{index}]")
            for index, value in enumerate(raw_audio)
        )
    else:
        raise ContentBriefError(
            "audio_paths must be absent or contain one path per dialogue turn"
        )

    return ContentBrief(
        title=title,
        premise=premise,
        characters=tuple(characters),
        dialogue=tuple(dialogue),
        durations_s=durations,
        audio_paths=audio_paths,
        source_path=source.resolve(),
    )


def _resolve_input(value: str, base: Path) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()


def _plate_path(plates_dir: Path, name: str) -> Path:
    matches = sorted(path for path in plates_dir.glob(f"{name}.*") if path.is_file())
    if not matches:
        raise ContentBriefError(f"missing plate for {name!r} in {plates_dir}")
    if len(matches) != 1:
        raise ContentBriefError(
            f"expected exactly one plate for {name!r}; found {len(matches)}"
        )
    return matches[0].resolve()


def build_run_film_inputs(
    brief: ContentBrief,
    plates_dir: str | Path,
    *,
    run_dir: str | Path,
) -> dict[str, Any]:
    """Resolve all brief inputs and write the equivalent run_film script."""

    if not isinstance(brief, ContentBrief):
        raise ContentBriefError("brief must be a ContentBrief")
    plates = Path(plates_dir).expanduser().resolve()
    destination = Path(run_dir).expanduser().resolve()
    if not plates.is_dir():
        raise ContentBriefError(f"plates directory does not exist: {plates}")

    resolved_plates = {
        "anchor": _plate_path(plates, "anchor"),
        **{
            character.name: _plate_path(plates, character.name)
            for character in brief.characters
        },
    }
    base = brief.source_path.parent if brief.source_path is not None else Path.cwd()
    resolved_audio = None
    if brief.audio_paths is not None:
        candidates = [_resolve_input(value, base) for value in brief.audio_paths]
        missing = [str(path) for path in candidates if not path.is_file()]
        if missing:
            raise ContentBriefError(f"missing audio file(s): {missing}")
        resolved_audio = [str(path) for path in candidates]

    # All fail-closed validation happens before the first output side effect.
    destination.mkdir(parents=True, exist_ok=True)
    script_path = destination / "script.txt"
    script_path.write_text(
        "".join(f"{line.speaker}: {line.text}\n" for line in brief.dialogue),
        encoding="utf-8",
    )
    return {
        "script_path": script_path,
        "characters": [item.mapping() for item in brief.characters],
        "durations": list(brief.durations_s),
        "audio_paths": resolved_audio,
        "plates": resolved_plates,
        "run_dir": destination,
    }
