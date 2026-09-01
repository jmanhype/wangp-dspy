"""Director schema — typed, frozen, JSON round-trippable plan objects.

Architecture pattern reimplemented (not vendored) from Maestro's
app/services/director/schema.py (WanGP Non-Commercial Evaluation 1.1;
see docs/render-knowledge/maestro-port.md). Our shot/audio model is
the verified H3-Ref2VA envelope: one start-image master plate, one
audio guide whose duration must equal the shot duration exactly, and
shot lengths constrained to the 17k+5 frame grid.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Tuple


class SchemaError(ValueError):
    """Typed schema construction failure."""


@dataclass(frozen=True)
class DialogueBeat:
    """One screenplay beat from planner pass 1 (creative stage)."""

    index: int
    speaker: str
    text: str
    section: str = "main"

    def __post_init__(self) -> None:
        if not isinstance(self.index, int) or self.index < 1:
            raise SchemaError(f"beat index must be int >= 1: {self.index!r}")
        if not self.speaker.strip():
            raise SchemaError("beat speaker must be nonempty")
        if not self.text.strip():
            raise SchemaError("beat text must be nonempty")


@dataclass(frozen=True)
class CharacterProfile:
    """A film character and their identity-locking master plate."""

    name: str
    description: str
    master_plate_path: str
    facing_requirement: str = "camera"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise SchemaError("character name must be nonempty")
        if not self.description.strip():
            raise SchemaError(f"{self.name}: description must be nonempty")
        if not self.master_plate_path.strip():
            raise SchemaError(f"{self.name}: master_plate_path required")
        if self.facing_requirement not in ("camera", "profile"):
            raise SchemaError(
                f"{self.name}: facing_requirement must be "
                f"'camera'|'profile', got {self.facing_requirement!r}")


@dataclass(frozen=True)
class CameraPlan:
    """Camera intent for one shot (renderer policy reads framing/lighting)."""

    framing: str = "wide"
    movement: str = "static"
    lighting: str = "bright"

    def __post_init__(self) -> None:
        for attr in ("framing", "movement", "lighting"):
            if not getattr(self, attr).strip():
                raise SchemaError(f"CameraPlan.{attr} must be nonempty")


@dataclass(frozen=True)
class ShotPlan:
    """One rendered shot: plate in, guide audio in, job config out.

    audio_guide_ref: {"path": str, "duration_s": float} — the guide is
    sliced to EXACTLY duration_s, which must equal shot duration_s.
    """

    index: int
    speaker: str
    dialogue_ref: str
    camera_plan: CameraPlan
    start_image_ref: str
    audio_guide_ref: Dict[str, Any]
    duration_s: float
    section: str = "main"

    def __post_init__(self) -> None:
        if not isinstance(self.index, int) or self.index < 1:
            raise SchemaError(f"shot index must be int >= 1: {self.index!r}")
        if not self.speaker.strip():
            raise SchemaError("shot speaker must be nonempty")
        if not self.dialogue_ref.strip():
            raise SchemaError("shot dialogue_ref must be nonempty")
        if not isinstance(self.camera_plan, CameraPlan):
            raise SchemaError("camera_plan must be a CameraPlan")
        try:
            d = float(self.duration_s)
        except (TypeError, ValueError):
            raise SchemaError(f"duration_s must be numeric: {self.duration_s!r}")
        if d <= 0:
            raise SchemaError(f"duration_s must be > 0, got {d}")
        object.__setattr__(self, "duration_s", d)
        g = self.audio_guide_ref
        if (not isinstance(g, dict) or not str(g.get("path", "")).strip()
                or "duration_s" not in g):
            raise SchemaError(
                "audio_guide_ref must be {'path': str, 'duration_s': float}")


@dataclass(frozen=True)
class ProductionPlan:
    """A full film plan: characters + ordered shots."""

    film_id: str
    characters: Tuple[CharacterProfile, ...] = field(default_factory=tuple)
    shots: Tuple[ShotPlan, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.film_id.strip():
            raise SchemaError("film_id must be nonempty")
        object.__setattr__(self, "characters", tuple(self.characters))
        object.__setattr__(self, "shots", tuple(self.shots))
        idxs = [s.index for s in self.shots]
        if idxs != list(range(1, len(idxs) + 1)):
            raise SchemaError(f"shot indices must be 1..N, got {idxs}")
        for s in self.shots:
            if s.speaker not in {c.name for c in self.characters}:
                raise SchemaError(
                    f"shot {s.index}: unknown speaker {s.speaker!r}")

    # ── JSON round-trip ─────────────────────────────────────────────

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, doc: Dict[str, Any]) -> "ProductionPlan":
        try:
            chars = tuple(CharacterProfile(**c) for c in doc["characters"])
            shots = []
            for s in doc["shots"]:
                s = dict(s)
                s["camera_plan"] = CameraPlan(**s["camera_plan"])
                shots.append(ShotPlan(**s))
            return cls(film_id=doc["film_id"], characters=chars,
                       shots=tuple(shots))
        except KeyError as e:
            raise SchemaError(f"missing field in plan JSON: {e}") from e


__all__ = [
    "SchemaError", "DialogueBeat", "CharacterProfile", "CameraPlan",
    "ShotPlan", "ProductionPlan",
]
