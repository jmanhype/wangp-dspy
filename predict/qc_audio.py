"""WD-a1d9/S3 — Ref2VA audio QC stage (honest placeholders).

NO judge runs in this slice (no GPU budget): qc_ref2va_audio returns
Ref2VAAudioQC placeholders with critic_model='Qwen2-Audio-7B' NAMED,
scores None, judged=False, and notes that say so explicitly — it never
pretends a judge ran. G3/G4 enforcement: QC refuses any artifact whose
audio did not pass through the discard/remux policy (manifest sidecar
required + discard_rendered_audio must be True).
"""
from __future__ import annotations

from dataclasses import dataclass

from predict.audio_dataplane import AudioDataPlaneError, Ref2VAAudioQC
from predict.audio_manifest import AudioManifest, AudioManifestError

__all__ = ["QCRefusalError", "Ref2VAAudioQCResult", "qc_ref2va_audio"]


@dataclass(frozen=True)
class Ref2VAAudioQCResult(Ref2VAAudioQC):
    """Ref2VAAudioQC + an explicit judged flag so a placeholder can
    never be mistaken for a judge's verdict."""
    judged: bool = False


class QCRefusalError(ValueError):
    """G3/G4: artifact never passed through the audio policy."""


def qc_ref2va_audio(render_output: str) -> Ref2VAAudioQCResult:
    try:
        manifest = AudioManifest.for_render(render_output)
    except AudioManifestError as e:
        raise QCRefusalError(
            "G3/G4 refusal: " + str(e)) from e
    pol = manifest.payload.get("audio_policy") or {}
    if not pol.get("discard_rendered_audio", False):
        raise QCRefusalError(
            "G3/G4 refusal: manifest audio_policy has "
            "discard_rendered_audio != True — rendered audio must "
            "never be trusted and must pass through the remux policy")
    # honest placeholder: critic named, no scores claimed
    return Ref2VAAudioQCResult(
        critic_model="Qwen2-Audio-7B",
        notes="not yet judged — Qwen2-Audio-7B judge has not run; "
              "scores are placeholders (None); manifest policy gate "
              "PASSED")
