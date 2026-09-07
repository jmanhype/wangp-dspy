"""Ref2VA continuation lane — validated config fields for the chain recipe.

Extends WanGPJobConfig's extra-dict usage with first-class fields per
docs/h3-continuation-recipe.md (Mode A/B), validated at construction.

Judge implementations for the audio_critic stage:
  - TranscriptJudge: whisper transcript vs intended script (word-match)
  - (vision judge: Qwen3.8 — separate module, API-side)
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Optional

from predict.job_config import WanGPJobConfig, JobConfigError

# Speaker attribution — VALIDATED 2026-09-06 (operator verdict "yes"):
# seed frame + ONE face ref of the SILENT character (Picture-N bound) keeps
# the audio guide intact (2 refs = under dilution threshold; 3 refs killed it,
# "Unmight Night Shurkey" gibberish) and holds the non-speaker's mouth closed
# while the audio binds the speaker. Community corroboration: MiniMax-H3
# issue #17 — multi-voice conditioning bleeds globally; single-voice-per-render
# (per-turn isolation) avoids it by construction.
SILENT_CHAR_REF_FIELDS = ("image_refs",)  # refs = [seed, silent_face]; see experiment v2
ALLOWED_IMAGE_PROMPT = {"S", ""}
ALLOWED_VIDEO_PROMPT = {"I", ""}   # "" = Mode A packed (no refs path)
ALLOWED_AUDIO_PROMPT = {"A", ""}


def build_picture_n_speaker_prompt(
    *,
    speaker_sn: str,
    silent_sn: str,
    line: str,
    speaker_picture: int = 1,
    silent_picture: int = 2,
) -> str:
    """Build the typed single-speaker Picture-N prompt envelope.

    Picture 1 is the speaking identity and Picture 2 is the one silent-face
    reference. Keeping these bindings in one builder prevents a free-form
    prompt from silently swapping mouth/audio attribution.
    """
    if not isinstance(speaker_sn, str) or not re.fullmatch(r"S\d+", speaker_sn):
        raise JobConfigError(f"speaker_sn must be an SN tag like S1, got {speaker_sn!r}")
    if not isinstance(silent_sn, str) or not re.fullmatch(r"S\d+", silent_sn):
        raise JobConfigError(f"silent_sn must be an SN tag like S2, got {silent_sn!r}")
    if speaker_sn == silent_sn:
        raise JobConfigError("speaker_sn and silent_sn must identify different characters")
    if speaker_picture < 1 or silent_picture < 1 or speaker_picture == silent_picture:
        raise JobConfigError("speaker/silent Picture-N bindings must be distinct positive integers")
    if not isinstance(line, str) or not line.strip():
        raise JobConfigError("dialogue line must be non-empty")
    return (
        f"{speaker_sn} (Picture {speaker_picture}) is the only speaker. "
        f"{silent_sn} (Picture {silent_picture}) listens silently with lips "
        f"closed throughout. {speaker_sn} says: <d>[English] {line.strip()}</d>"
    )


def validate_picture_n_speaker_prompt(prompt: str, *, speaker_picture: int = 1,
                                     silent_picture: int = 2) -> None:
    """Fail closed unless a continuation prompt carries both bindings."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise JobConfigError("continuation speaker prompt must be non-empty")
    required = (f"Picture {speaker_picture}", f"Picture {silent_picture}",
                "only speaker", "lips closed", "<d>[English]")
    missing = [token for token in required if token not in prompt]
    if missing:
        raise JobConfigError(
            f"continuation speaker prompt missing Picture-N binding token(s): {missing}")


@dataclass(frozen=True)
class ContinuationExtras:
    """Mode A/B continuation fields (validated)."""
    image_prompt_type: str = "S"
    video_prompt_type: str = "I"
    audio_prompt_type: str = "A"
    image_start: Optional[str] = None
    image_refs: List[str] = field(default_factory=list)
    audio_guide: Optional[str] = None
    video_source: Optional[str] = None
    keep_frames_video_source: str = ""
    audio_policy_discard_rendered: bool = True
    video_length: int = 48
    requested_frames: int = 48

    def validate(self) -> None:
        if self.image_prompt_type not in ALLOWED_IMAGE_PROMPT:
            raise JobConfigError(f"image_prompt_type {self.image_prompt_type!r} not in {sorted(ALLOWED_IMAGE_PROMPT)}")
        if self.video_prompt_type not in ALLOWED_VIDEO_PROMPT:
            raise JobConfigError(f"video_prompt_type {self.video_prompt_type!r} not in {sorted(ALLOWED_VIDEO_PROMPT)}")
        if self.audio_prompt_type not in ALLOWED_AUDIO_PROMPT:
            raise JobConfigError(f"audio_prompt_type {self.audio_prompt_type!r} not allowed")
        # Mode B: audio requires a guide >= 2s enforced at wav-prep; here: presence
        if self.audio_prompt_type == "A" and not self.audio_guide:
            raise JobConfigError("audio_prompt_type 'A' requires audio_guide")
        if self.image_prompt_type == "S" and not self.image_start:
            raise JobConfigError("image_prompt_type 'S' requires image_start")
        # G4: rendered audio never trusted when a guide is used
        if self.audio_prompt_type == "A" and not self.audio_policy_discard_rendered:
            raise JobConfigError("G4: discard_rendered_audio must be True when guiding audio")
        if self.video_length != 48 or self.requested_frames != 48:
            raise JobConfigError(
                "continuation video_length/requested_frames are pinned "
                "to exactly 48 frames (2.0s @ 24fps)")

    def to_extra(self) -> dict:
        self.validate()
        d = {
            "image_prompt_type": self.image_prompt_type,
            "video_prompt_type": self.video_prompt_type,
            "audio_prompt_type": self.audio_prompt_type,
            "audio_policy": {"discard_rendered_audio": self.audio_policy_discard_rendered},
            "video_source": None,
            "video_guide": None,
            "keep_frames_video_source": self.keep_frames_video_source,
            "video_length": self.video_length,
            "requested_frames": self.requested_frames,
        }
        if self.image_start:
            d["image_start"] = self.image_start
        if self.image_refs:
            d["image_refs"] = list(self.image_refs)
        if self.audio_guide:
            d["audio_guide"] = self.audio_guide
        return d


def words(s: str) -> set:
    return set(re.findall(r"[a-z']+", s.lower()))


def transcript_match_score(said: str, intended: str) -> float:
    """Word-overlap score vs intended line (0..1). PASS bar: >= 0.5."""
    a, b = words(said), words(intended)
    if not b:
        return 0.0
    return len(a & b) / len(b)


def transcript_judge(settings_doc: dict, *, said: str, intended_turns: List[str],
                     pass_bar: float = 0.5) -> dict:
    """Judge callable for run_ref2va_qc_stage: transcript-vs-script per turn.

    Returns the four score fields as required by the stage schema (map:
    words_match = min over turns; others verbatim-honest placeholders).
    """
    scores = [transcript_match_score(said, t) for t in intended_turns]
    worst = min(scores) if scores else 0.0
    return {
        "transcript_words_match": round(worst, 3),
        "transcript_pass_bar": pass_bar,
        "turn_count": len(intended_turns),
        "passes": worst >= pass_bar,
    }
