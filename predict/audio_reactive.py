"""AudioReactiveSpec — typed manifest contract for the Ref2VA
audio-reactive lane (hermes-86ad4c4a).

Single authority for the audio-side fields the lane owes downstream
consumers: source master audio + Demucs vocal stem + Whisper vocal
map, the audio guide actually submitted with the job, the keeper
window, soundtrack/H3 audio policies, Qwen2-Audio critic fields and
the mouth/audio/visual QC fields.

Construction IS validation (typed AudioReactiveError), matching the
WanGPJobConfig convention. Zero-model, no GPU work.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

AUDIO_PROMPT_TYPE = "A"
H3_AUDIO_POLICY = "discard_then_remux"
FINAL_SOUNDTRACK_POLICY = "master_audio"
QWEN2_AUDIO_MODEL_DEFAULT = "qwen2-audio-7b-instruct"


class AudioReactiveError(ValueError):
    """Typed audio-reactive contract failure."""


def _require_file(field: str, path: str) -> str:
    if not path or not isinstance(path, str):
        raise AudioReactiveError(f"{field} must be a nonempty path")
    if not os.path.isfile(path):
        raise AudioReactiveError(
            f"{field} not readable at build time: {path!r}")
    return path


@dataclass(frozen=True)
class AudioReactiveSpec:
    """Typed, validated audio-reactive contract (frozen)."""

    # source chain
    master_audio: str
    vocal_stem: str            # Demucs 'vocals' stem of master_audio
    vocal_map: str             # Whisper word/segment map over the stem
    audio_guide: str           # the REAL guide submitted with the job
    # keeper window (seconds into the master)
    keeper_window_start_s: float
    keeper_window_duration_s: float
    # lane typing (Ref2VA is the only 'A' carrier — G1)
    audio_prompt_type: str = AUDIO_PROMPT_TYPE
    h3_audio_policy: str = H3_AUDIO_POLICY
    final_soundtrack_policy: str = FINAL_SOUNDTRACK_POLICY
    # Qwen2-Audio critic
    qwen2_audio_model: str = QWEN2_AUDIO_MODEL_DEFAULT
    qwen2_audio_critic: Optional[str] = None
    # QC verdicts (filled by QC; None = not yet assessed)
    mouth_sync: Optional[str] = None
    audio_quality: Optional[str] = None
    visual_regression: Optional[str] = None

    def __post_init__(self) -> None:
        for f in ("master_audio", "vocal_stem", "vocal_map",
                  "audio_guide"):
            _require_file(f, getattr(self, f))
        if str(self.audio_prompt_type).strip().upper() != AUDIO_PROMPT_TYPE:
            raise AudioReactiveError(
                f"audio_prompt_type must be 'A' (Ref2VA is the only "
                f"sanctioned carrier — G1), got {self.audio_prompt_type!r}")
        if self.h3_audio_policy != H3_AUDIO_POLICY:
            raise AudioReactiveError(
                f"h3_audio_policy must be {H3_AUDIO_POLICY!r}, got "
                f"{self.h3_audio_policy!r}")
        if self.final_soundtrack_policy != FINAL_SOUNDTRACK_POLICY:
            raise AudioReactiveError(
                "final_soundtrack_policy must be "
                f"{FINAL_SOUNDTRACK_POLICY!r}, got "
                f"{self.final_soundtrack_policy!r}")
        if not (self.keeper_window_start_s >= 0.0
                and self.keeper_window_duration_s > 0.0):
            raise AudioReactiveError(
                f"keeper window invalid: start "
                f"{self.keeper_window_start_s}s duration "
                f"{self.keeper_window_duration_s}s (need start >= 0, "
                "duration > 0)")

    # ── manifest contract (plain JSON, stable shape) ────────────────

    def to_manifest(self) -> dict:
        return {
            "audio_prompt_type": self.audio_prompt_type,
            "audio_guide": self.audio_guide,
            "source": {
                "master_audio": self.master_audio,
                "vocal_stem": self.vocal_stem,
                "vocal_map": self.vocal_map,
            },
            "keeper_window": {
                "start_s": self.keeper_window_start_s,
                "duration_s": self.keeper_window_duration_s,
            },
            "policy": {
                "h3_audio": self.h3_audio_policy,
                "final_soundtrack": self.final_soundtrack_policy,
            },
            "critic": {
                "model": self.qwen2_audio_model,
                "critic": self.qwen2_audio_critic,
            },
            "qc": {
                "mouth_sync": self.mouth_sync,
                "audio_quality": self.audio_quality,
                "visual_regression": self.visual_regression,
            },
        }

    @classmethod
    def from_manifest(cls, doc: dict) -> "AudioReactiveSpec":
        src, win = doc.get("source", {}), doc.get("keeper_window", {})
        critic, qc = doc.get("critic", {}), doc.get("qc", {})
        return cls(
            master_audio=src["master_audio"],
            vocal_stem=src["vocal_stem"],
            vocal_map=src["vocal_map"],
            audio_guide=doc["audio_guide"],
            keeper_window_start_s=win["start_s"],
            keeper_window_duration_s=win["duration_s"],
            audio_prompt_type=doc.get(
                "audio_prompt_type", AUDIO_PROMPT_TYPE),
            h3_audio_policy=doc.get("policy", {}).get(
                "h3_audio", H3_AUDIO_POLICY),
            final_soundtrack_policy=doc.get("policy", {}).get(
                "final_soundtrack", FINAL_SOUNDTRACK_POLICY),
            qwen2_audio_model=critic.get(
                "model", QWEN2_AUDIO_MODEL_DEFAULT),
            qwen2_audio_critic=critic.get("critic"),
            mouth_sync=qc.get("mouth_sync"),
            audio_quality=qc.get("audio_quality"),
            visual_regression=qc.get("visual_regression"),
        )
