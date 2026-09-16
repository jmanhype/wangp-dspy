"""Ref2VA continuation lane — validated config fields for the chain recipe.

Extends WanGPJobConfig's extra-dict usage with first-class fields per
docs/h3-continuation-recipe.md (Mode A/B), validated at construction.

Judge implementations for the audio_critic stage:
  - TranscriptJudge: whisper transcript vs intended script (word-match)
  - (vision judge: Qwen3.8 — separate module, API-side)
"""
from __future__ import annotations
import re
from difflib import SequenceMatcher
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import List, Optional

from predict.job_config import (
    CONTINUATION_FRAMES_MIN,
    normalize_continuation_frame_count,
    WanGPJobConfig,
    JobConfigError,
)

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
    audio_policy_discard_rendered: bool = False
    video_length: int = CONTINUATION_FRAMES_MIN
    requested_frames: int = CONTINUATION_FRAMES_MIN
    # Persisted continuation envelopes include this optional slot even when
    # it is null.  Keeping it on the typed object makes the envelope
    # round-trip lossless while preserving the existing runtime behavior.
    video_guide: Optional[str] = None
    # The September v2 dialogue lane predates the Picture-N prompt contract.
    # Keep that recipe selectable explicitly rather than weakening validation
    # for every continuation job.  Legacy mode still carries typed extras,
    # audio isolation, frame/grid checks, and the native audio policy; it
    # only permits the verbatim S1/S2 prose prompt used by the proven v2
    # control.
    legacy_v2_prompt: bool = False

    def validate(self) -> None:
        if not isinstance(self.legacy_v2_prompt, bool):
            raise JobConfigError("legacy_v2_prompt must be bool")
        if self.image_prompt_type not in ALLOWED_IMAGE_PROMPT:
            raise JobConfigError(f"image_prompt_type {self.image_prompt_type!r} not in {sorted(ALLOWED_IMAGE_PROMPT)}")
        if self.video_prompt_type not in ALLOWED_VIDEO_PROMPT:
            raise JobConfigError(f"video_prompt_type {self.video_prompt_type!r} not in {sorted(ALLOWED_VIDEO_PROMPT)}")
        if self.audio_prompt_type not in ALLOWED_AUDIO_PROMPT:
            raise JobConfigError(f"audio_prompt_type {self.audio_prompt_type!r} not allowed")
        # Mode B: audio conditioning requires a guide >= 2s (duration is
        # enforced at wav-prep); here: presence. The guide is an input, not
        # proof that generated native audio will pass downstream QC.
        if self.audio_prompt_type == "A" and not self.audio_guide:
            raise JobConfigError("audio_prompt_type 'A' requires audio_guide")
        if self.image_prompt_type == "S" and not self.image_start:
            raise JobConfigError("image_prompt_type 'S' requires image_start")
        # Native H3 audio is the output of conditioning, not a disposable
        # track. Legacy external-audio remux jobs must be re-planned rather
        # than weakening this native contract.
        if self.audio_prompt_type == "A" and self.audio_policy_discard_rendered is not False:
            raise JobConfigError("Ref2VA requires native audio (discard_rendered_audio=False); re-plan legacy remux jobs")
        for name, value in (("video_length", self.video_length),
                            ("requested_frames", self.requested_frames)):
            if isinstance(value, bool) or not isinstance(value, int):
                raise JobConfigError(
                    f"continuation {name} must be an int, got {value!r}")
            if value != normalize_continuation_frame_count(value):
                raise JobConfigError(
                    f"continuation {name} {value}f is off the H3 5+17k "
                    "grid (expected 56, 73, 90, ...)")
        if self.video_length != self.requested_frames:
            raise JobConfigError(
                "continuation video_length and requested_frames must "
                "match the same grid-aligned frame count")

    def to_extra(self) -> dict:
        self.validate()
        d = {
            "image_prompt_type": self.image_prompt_type,
            "video_prompt_type": self.video_prompt_type,
            "audio_prompt_type": self.audio_prompt_type,
            "audio_policy": {"discard_rendered_audio": self.audio_policy_discard_rendered},
            "video_source": None,
            "video_guide": self.video_guide,
            "keep_frames_video_source": self.keep_frames_video_source,
            "video_length": self.video_length,
            "requested_frames": self.requested_frames,
            "legacy_v2_prompt": self.legacy_v2_prompt,
        }
        if self.image_start:
            d["image_start"] = self.image_start
        if self.image_refs:
            d["image_refs"] = list(self.image_refs)
        if self.audio_guide:
            d["audio_guide"] = self.audio_guide
        return d

    @classmethod
    def from_dict(cls, payload: Mapping) -> "ContinuationExtras":
        """Normalize a persisted continuation envelope into typed fields.

        ``to_extra`` intentionally stores the audio policy as the nested
        ``audio_policy.discard_rendered_audio`` shape used by job manifests,
        while the typed object keeps a flat field for validation. Ref2VA
        audio jobs use false (preserve native output); true is reserved for
        explicit non-Ref2VA external-audio remux lanes. This loader is the
        single compatibility boundary between those shapes; it also accepts
        the optional ``video_guide`` slot emitted by older envelopes and
        remains strict about unknown fields.
        """
        if isinstance(payload, cls):
            return payload
        if not isinstance(payload, Mapping):
            raise JobConfigError(
                "continuation extras must be a mapping, got "
                f"{type(payload).__name__}")

        data = dict(payload)
        nested_policy = data.pop("audio_policy", None)
        if nested_policy is not None:
            if not isinstance(nested_policy, Mapping):
                raise JobConfigError(
                    "audio_policy must be a mapping when present")
            unknown_policy = set(nested_policy) - {
                "discard_rendered_audio"}
            if unknown_policy:
                raise JobConfigError(
                    "audio_policy contains unknown field(s): "
                    f"{sorted(unknown_policy)}")
            if "discard_rendered_audio" not in nested_policy:
                raise JobConfigError(
                    "audio_policy requires discard_rendered_audio")
            nested_value = nested_policy["discard_rendered_audio"]
            flat_value = data.get("audio_policy_discard_rendered")
            if flat_value is not None and flat_value != nested_value:
                raise JobConfigError(
                    "audio policy values disagree between nested and flat "
                    "forms")
            data["audio_policy_discard_rendered"] = nested_value

        allowed = {
            "image_prompt_type", "video_prompt_type", "audio_prompt_type",
            "image_start", "image_refs", "audio_guide", "video_source",
            "video_guide", "keep_frames_video_source",
            "audio_policy_discard_rendered", "video_length",
            "requested_frames",
            "legacy_v2_prompt",
        }
        unknown = set(data) - allowed
        if unknown:
            raise JobConfigError(
                "continuation extras contain unknown field(s): "
                f"{sorted(unknown)}")
        if "image_refs" in data:
            refs = data["image_refs"]
            if not isinstance(refs, (list, tuple)):
                raise JobConfigError("image_refs must be a list or tuple")
            data["image_refs"] = list(refs)
        try:
            return cls(**data)
        except TypeError as e:
            raise JobConfigError(
                f"invalid continuation extras fields: {e}") from e


def words(s: str) -> set:
    return set(re.findall(r"[a-z']+", s.lower()))


def _word_tokens(s: str) -> List[str]:
    return re.findall(r"[a-z']+", s.lower())


def transcript_wer(said: str, intended: str) -> float:
    """Token-level WER: insertions and repetitions lower the score.

    The earlier unordered-set comparison treated “cookie cookie cookie” as a
    perfect match for “cookie”.  Sequence edit distance preserves order and
    penalizes every extra generated word.
    """
    hyp, ref = _word_tokens(said), _word_tokens(intended)
    if not ref:
        return 1.0 if hyp else 0.0
    previous = list(range(len(ref) + 1))
    for i, h in enumerate(hyp, 1):
        current = [i]
        for j, r in enumerate(ref, 1):
            current.append(min(
                previous[j] + 1,             # deletion
                current[j - 1] + 1,          # insertion
                previous[j - 1] + (h != r),  # substitution
            ))
        previous = current
    return previous[-1] / len(ref)


def transcript_match_score(said: str, intended: str) -> float:
    """Sequence-sensitive transcript similarity: ``1 - token WER``."""
    if not _word_tokens(intended):
        return 0.0
    return max(0.0, 1.0 - transcript_wer(said, intended))


def _turn_transcript_scores(said: str, intended_turns: List[str]) -> List[float]:
    """Attribute sequence-edit errors to each intended dialogue turn."""
    turn_tokens = [_word_tokens(turn) for turn in intended_turns]
    turn_ids = [index for index, tokens in enumerate(turn_tokens)
                for _ in tokens]
    reference = [token for tokens in turn_tokens for token in tokens]
    hypothesis = _word_tokens(said)
    errors = [0] * len(turn_tokens)

    matcher = SequenceMatcher(None, hypothesis, reference, autojunk=False)
    for tag, hyp_start, hyp_end, ref_start, ref_end \
            in matcher.get_opcodes():
        if tag == "equal":
            continue

        # Replace/delete consumes one intended token per reference index.
        for ref_index in range(ref_start, ref_end):
            errors[turn_ids[ref_index]] += 1
        # Any excess hypothesis words are insertions attributed to the
        # nearest intended turn.
        if hyp_end - hyp_start > ref_end - ref_start:
            extra = (hyp_end - hyp_start) - (ref_end - ref_start)
            turn = 0 if ref_end == 0 else turn_ids[ref_end - 1]
            if turn < len(errors):
                errors[turn] += extra

    return [
        max(0.0, 1.0 - (errors[index] / len(tokens)))
        if tokens else 0.0
        for index, tokens in enumerate(turn_tokens)
    ]


def transcript_judge(settings_doc: dict, *, said: str, intended_turns: List[str],
                     pass_bar: float = 0.5) -> dict:
    """Transcript evidence helper: transcript-vs-intended-turns.

    Returns transcript evidence fields (worst-turn word match, bar, turn
    count, and pass flag). It is evidence about generated speech, not an
    automatic Ref2VA QC pass and not a claim of phonetic A/V synchrony.
    """
    # Align the complete transcript against all intended turns, then require
    # every turn to meet the bar. This prevents a long correctly transcribed
    # turn from masking a completely omitted short turn.
    scores = _turn_transcript_scores(said, intended_turns)
    worst = min(scores) if scores else 0.0
    return {
        "transcript_words_match": round(worst, 3),
        "transcript_pass_bar": pass_bar,
        "turn_count": len(intended_turns),
        "turn_scores": [round(score, 3) for score in scores],
        "passes": worst >= pass_bar,
    }
