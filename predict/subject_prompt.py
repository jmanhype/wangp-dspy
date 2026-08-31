"""Subject-mode prompt builder for the MiniMax Ref2VA full-reference format.

Zero-model, deterministic, pure: identical inputs produce a byte-identical
prompt string. Consumed by future render pipeline wiring (build_jobs is a
separate slice). No training/, metrics/, or evaluate/ module imports.

Structure copied from the verified working reference config (measured live on
3090, 2026-08-30): per-subject definitions citing <Picture 1>, ambient action
sentences, speaker binding "(S1) says: <d>[lang] ...</d>", non-speaker
"lips completely closed" clauses, [Shot 1] Static Shot, trailing soundscape
and non-diegetic music lines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

__all__ = [
    "SubjectSpec",
    "SceneCast",
    "SpeakerLine",
    "SubjectPromptError",
    "build_subject_prompt",
]


class SubjectPromptError(ValueError):
    """Raised for any rejected subject-mode prompt input."""


@dataclass(frozen=True)
class SubjectSpec:
    """One subject (character or environment element) in the scene."""

    subject_id: int
    name: str
    description: str  # identity + appearance + position
    source_picture: int = 1
    is_speaker: bool = False
    ambient_actions: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.subject_id, int) or self.subject_id < 1:
            raise SubjectPromptError(
                f"subject_id must be an int >= 1, got {self.subject_id!r}"
            )
        if not self.name.strip():
            raise SubjectPromptError(f"subject {self.subject_id}: name must be nonempty")
        if not self.description.strip():
            raise SubjectPromptError(
                f"subject {self.subject_id}: description must be nonempty"
            )
        if self.source_picture < 1:
            raise SubjectPromptError(
                f"subject {self.subject_id}: source_picture must be >= 1"
            )


@dataclass(frozen=True)
class SceneCast:
    """Full cast + scene framing for a subject-mode prompt."""

    subjects: Tuple[SubjectSpec, ...] = field(default_factory=tuple)
    environment_subject: bool = False  # first subject may be an environment
    style: str = ""
    shot_description: str = ""
    soundscape: str = ""
    music: str = "N/A"

    def __post_init__(self) -> None:
        object.__setattr__(self, "subjects", tuple(self.subjects))
        if not 1 <= len(self.subjects) <= 9:
            raise SubjectPromptError(
                f"SceneCast must contain 1 to 9 subjects (Ref2VA image-ref "
                f"limit), got {len(self.subjects)}"
            )
        for s in self.subjects:
            if not isinstance(s, SubjectSpec):
                raise SubjectPromptError(f"non-SubjectSpec entry in subjects: {s!r}")
        ids = [s.subject_id for s in self.subjects]
        if ids != list(range(1, len(ids) + 1)):
            raise SubjectPromptError(
                "subject_ids must be exactly 1..N in order, got " f"{ids}"
            )
        for label, val in (
            ("style", self.style),
            ("shot_description", self.shot_description),
            ("soundscape", self.soundscape),
        ):
            if not val.strip():
                raise SubjectPromptError(f"SceneCast.{label} must be nonempty")
        if not (self.music.strip() == "N/A" or self.music.strip()):
            raise SubjectPromptError("SceneCast.music must be 'N/A' or a description")


@dataclass(frozen=True)
class SpeakerLine:
    """The single spoken line, bound to one speaking subject."""

    subject_id: int
    text: str
    language: str = "English"
    voice_description: str = ""

    def __post_init__(self) -> None:
        if self.subject_id < 1:
            raise SubjectPromptError(f"SpeakerLine.subject_id must be >= 1")
        if not self.text.strip():
            raise SubjectPromptError("SpeakerLine.text must be nonempty")
        if not self.language.strip():
            raise SubjectPromptError("SpeakerLine.language must be nonempty")


def build_subject_prompt(cast: SceneCast, speaker_line: SpeakerLine) -> str:
    """Render the Ref2VA subject-mode prompt. Pure and deterministic."""
    speakers = [s for s in cast.subjects if s.is_speaker]
    if len(speakers) != 1:
        raise SubjectPromptError(
            f"exactly one subject must have is_speaker=True, got {len(speakers)}"
        )
    speaker = speakers[0]
    if speaker.subject_id != speaker_line.subject_id:
        raise SubjectPromptError(
            f"speaker_line.subject_id={speaker_line.subject_id} does not match "
            f"the subject marked is_speaker (subject_id={speaker.subject_id})"
        )

    # Ambient-action validation: every non-environment subject needs one.
    env_exposed = cast.environment_subject
    for s in cast.subjects:
        if env_exposed and s is cast.subjects[0]:
            continue  # environment subject may omit ambient actions
        if not s.ambient_actions.strip():
            raise SubjectPromptError(
                f"subject {s.subject_id} ({s.name}) requires nonempty "
                f"ambient_actions"
            )

    lines: List[str] = []
    # Subject definitions: identity/appearance ONLY — matching the verified
    # reference config, ambient actions, lips-closed clauses and the speaker
    # <d> binding flow as prose sentences inside the Detailed description
    # body below, never inside the subject definitions.
    for s in cast.subjects:
        lines.append(f"<Subject {s.subject_id}> (from <Picture {s.source_picture}>):")
        lines.append(f"{s.name} — {s.description}.")
        lines.append("")

    lines.append(
        "Summary: [reference generation] All subjects retain their exact "
        "identities, appearances, and positions from <Picture 1> throughout."
    )
    lines.append("")
    lines.append("Retention analysis:")
    for s in cast.subjects:
        lines.append(
            f"<Subject {s.subject_id}> fully preserved: identity, wardrobe, "
            f"and framing held for the full duration."
        )
    lines.append("")
    lines.append("Detailed description:")
    lines.append(cast.style.strip())
    # One prose sentence per character, in subject order, inside the body.
    body: List[str] = []
    for s in cast.subjects:
        sentence = f"<Subject {s.subject_id}> {s.ambient_actions.strip()}"
        if s is not speaker:
            sentence += ", their lips completely closed"
        body.append(sentence + ".")
    vd = speaker_line.voice_description.strip()
    voice = f" The {vd}" if vd else ""
    body.append(
        f"The {speaker.name}{voice} (S1) says: "
        f"<d>[{speaker_line.language}] {speaker_line.text.strip()}</d>."
    )
    lines.append(
        f"[Shot 1] Static Shot. {cast.shot_description.strip()} "
        + " ".join(body)
        + " All other subjects remain silent with their lips closed "
        "throughout. No camera movement; all motion is in-scene."
    )
    lines.append("")
    lines.append(f"Overall soundscape: {cast.soundscape.strip()}")
    lines.append(f"Non-diegetic music: {cast.music.strip()}")

    return "\n".join(lines).rstrip("\n") + "\n"
