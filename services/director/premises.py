"""Repo-owned Lost Futures premise index and deterministic resolver."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence


class PremiseIndexError(ValueError):
    """Typed rejection of a malformed or ambiguous premise index."""


@dataclass(frozen=True)
class Premise:
    id: str
    title: str
    logline: str
    characters: tuple[dict, ...]
    # Optional until every legacy Lost Futures entry has a registered visual
    # anchor. Acceptance/production bundles must provide it when present.
    style_ref: str = ""

    def __post_init__(self):
        if not self.id.strip() or not self.title.strip() or not self.logline.strip():
            raise PremiseIndexError("premise id/title/logline must be nonempty")
        if len(self.characters) < 2:
            raise PremiseIndexError(
                f"premise {self.id}: at least two characters are required")
        if any(not isinstance(c, Mapping) for c in self.characters):
            raise PremiseIndexError(f"premise {self.id}: character entries must be objects")
        names = [c.get("name") for c in self.characters]
        sns = [c.get("sn_tag") for c in self.characters]
        if len(set(names)) != len(names) or len(set(sns)) != len(sns):
            raise PremiseIndexError(f"premise {self.id}: character names/sn_tags must be unique")
        for c in self.characters:
            if not all(str(c.get(k, "")).strip() for k in ("name", "sn_tag", "description")):
                raise PremiseIndexError(
                    f"premise {self.id}: each character needs name/sn_tag/description")


def _default_index_path() -> Path:
    return Path(__file__).resolve().parents[2] / "datasets" / "lost-futures" / "index.json"


def load_lost_futures_index(path: Optional[str | Path] = None) -> tuple[Premise, ...]:
    index_path = Path(path) if path is not None else _default_index_path()
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PremiseIndexError(f"unable to read Lost Futures index {index_path}: {exc}") from exc
    if payload.get("schema") != "wangp-dspy.lost-futures-index/v1":
        raise PremiseIndexError(f"index schema mismatch: {payload.get('schema')!r}")
    try:
        premises = tuple(Premise(
            id=str(item["id"]), title=str(item["title"]),
            logline=str(item["logline"]),
            characters=tuple(dict(c) for c in item["characters"]),
            style_ref=str(item.get("style_ref", "")).strip())
                         for item in payload["premises"])
    except (KeyError, TypeError) as exc:
        raise PremiseIndexError(f"index premise entry malformed: {exc}") from exc
    if not premises:
        raise PremiseIndexError("index contains no premises")
    if len({p.id for p in premises}) != len(premises):
        raise PremiseIndexError("index premise ids must be unique")
    return premises


def resolve_premise(premise_id: Optional[str] = None, *,
                    index: Optional[Sequence[Premise]] = None) -> Premise:
    premises = tuple(index) if index is not None else load_lost_futures_index()
    if premise_id is None:
        return premises[0]
    for premise in premises:
        if premise.id == premise_id:
            return premise
    raise PremiseIndexError(
        f"unknown Lost Futures premise {premise_id!r}; available ids: "
        f"{[p.id for p in premises]}")


__all__ = ["PremiseIndexError", "Premise", "load_lost_futures_index",
           "resolve_premise"]
