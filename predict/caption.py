"""CaptionSpec / CaptionArtifact — the caption stage contract (WD-obun,
S7 film lane).

Doctrine:
- CAPTIONS ARE AN EXPLICIT STAGE: a typed CaptionSpec flows through the
  pipeline and lands as a CaptionArtifact in PipelineResult.captions.
  Captions are never embedded in prompt text — the caption stage is a
  separate, auditable pipeline boundary like render or QC.
- TYPED: malformed specs (empty text, bad timecodes, overlapping cues,
  unknown language) are typed rejections (CaptionValidationError),
  never warnings.
- DETERMINISTIC: artifact_sha is sha256 over canonical JSON of the
  normalized spec + source video — same inputs, byte-identical output.
- PROVENANCE-LINKED: every artifact names its source video; the sha
  binds spec AND video, so a re-render invalidates stale captions.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

# SRT-flavored allowlist: workflow languages the operator has ruled on
# (kept explicit — an unknown language is a typo until ruled otherwise).
ACCEPTED_LANGUAGES = frozenset({"en", "es", "ja", "zh"})


class CaptionValidationError(Exception):
    """Typed rejection of an invalid caption spec/artifact."""


def _norm(text: str) -> str:
    return " ".join((text or "").split())


def _validate_timecode(start: float, end: float) -> None:
    if start < 0 or end < 0:
        raise CaptionValidationError(
            "timecodes must be non-negative "
            f"(got start={start}, end={end})")
    if start >= end:
        raise CaptionValidationError(
            f"cue start < end required (got {start} >= {end})")


@dataclass(frozen=True)
class CaptionCue:
    start: float
    end: float
    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.start, (int, float)) or \
                isinstance(self.start, bool):
            raise CaptionValidationError("cue start must be numeric")
        if not isinstance(self.end, (int, float)) or \
                isinstance(self.end, bool):
            raise CaptionValidationError("cue end must be numeric")
        if not _norm(self.text):
            raise CaptionValidationError(
                "cue text must be a nonempty string")


@dataclass(frozen=True)
class CaptionSpec:
    cues: tuple
    language: str = "en"

    def __post_init__(self) -> None:
        cues = tuple(self.cues) if not isinstance(self.cues, tuple) \
            else self.cues
        object.__setattr__(self, "cues", cues)
        if not cues:
            raise CaptionValidationError(
                "CaptionSpec requires at least one cue")
        if self.language not in ACCEPTED_LANGUAGES:
            raise CaptionValidationError(
                f"language {self.language!r} not in accepted allowlist "
                f"{sorted(ACCEPTED_LANGUAGES)}")
        prev_end = None
        for cue in cues:
            _validate_timecode(cue.start, cue.end)
            if prev_end is not None and cue.start < prev_end:
                raise CaptionValidationError(
                    f"cues overlap: a cue ending at {prev_end} is "
                    f"followed by one starting at {cue.start}")
            prev_end = cue.end
        # normalized (sorted, whitespace-collapsed) view for determinism
        object.__setattr__(self, "cues", tuple(sorted(
            (CaptionCue(c.start, c.end, _norm(c.text)) for c in cues),
            key=lambda c: (c.start, c.end, c.text))))


@dataclass(frozen=True)
class CaptionArtifact:
    spec: CaptionSpec
    source_video: str
    artifact_sha: str

    def to_srt(self) -> str:
        def ts(t: float) -> str:
            h, rem = divmod(int(t * 1000), 3_600_000)
            m, rem = divmod(rem, 60_000)
            s, ms = divmod(rem, 1_000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
        lines = []
        for i, c in enumerate(self.spec.cues, 1):
            lines += [str(i), f"{ts(c.start)} --> {ts(c.end)}", c.text, ""]
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps({
            "source_video": self.source_video,
            "language": self.spec.language,
            "artifact_sha": self.artifact_sha,
            "cues": [{"start": c.start, "end": c.end, "text": c.text}
                     for c in self.spec.cues],
        }, sort_keys=True, indent=2) + "\n"


def build_captions(spec: CaptionSpec, source_video: str) -> CaptionArtifact:
    if not isinstance(source_video, str) or not source_video.strip():
        raise CaptionValidationError(
            "source_video must be a nonempty path")
    payload = json.dumps(
        {"cues": [(c.start, c.end, c.text) for c in spec.cues],
         "language": spec.language, "video": source_video},
        sort_keys=True, separators=(",", ":"))
    return CaptionArtifact(spec=spec, source_video=source_video,
                           artifact_sha=hashlib.sha256(
                               payload.encode()).hexdigest())
