"""WD-a1d9-followup — S3 Ref2VA QC stage + remux command PLANNER.

Spec: docs/specs/s3-audio-manifest-qc.md (D2 + D3).

D2 remux planner (legacy/shared): emits the ffmpeg command as an ARGV
LIST only (never a shell string); inputs/outputs must resolve under the
job's sanctioned dirs (path-containment, GLM note N1). EXECUTION stays
with an explicit caller — this module never runs the command. Ref2VA
native lanes do not use this planner; it remains for explicit
non-Ref2VA external-audio remux lanes with discard_rendered_audio=True.

D3 QC stage: fills Ref2VAAudioQC fields. Schema-only path uses judge
placeholders — critic_model='Qwen2-Audio-7B' present but scores None
until a judge runs (honest placeholders, model identity verbatim,
never fake scores). Policy enforcement is lane-specific: Ref2VA requires
discard_rendered_audio=False and generated native audio; non-Ref2VA remux
lanes require discard_rendered_audio=True. Neither policy setting is an
automatic QC pass — the configured evidence gates still decide.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple

from predict.audio_dataplane import (
    AudioDataPlaneError, AudioGuideProvenance, AudioPolicy, Ref2VAAudioQC,
)
from qc.audio_critic.whisper_gate import WhisperGateError, run_whisper_gate
from qc.audio_critic.vision_judge import VisionJudgeError, run_vision_judge

__all__ = ["Ref2VAQCStageError", "plan_remux_command",
           "run_ref2va_qc_stage"]


class Ref2VAQCStageError(ValueError):
    """Typed rejection for the remux planner + QC stage.

    Vision-gate rejections carry the judge's component scores and raw model
    text through this wrapper so the durable executor can preserve them.
    """

    def __init__(self, message: str, *, vision_scores=None,
                 vision_raw_response=None, whisper_evidence=None):
        super().__init__(message)
        self.vision_scores = dict(vision_scores or {})
        self.vision_raw_response = (
            str(vision_raw_response)
            if vision_raw_response is not None else None)
        self.whisper_evidence = dict(whisper_evidence or {})


_SCORE_FIELDS = ("mouth_sync", "audio_fidelity",
                 "visual_motion_match", "audio_artifacts")


def _contained(path: str, sanctioned_dirs: Sequence[str]) -> bool:
    """True iff path resolves under one of the sanctioned dirs.
    Resolves symlinks and '..' so dotted/relative escapes fail."""
    try:
        p = Path(path).resolve()
    except OSError:
        return False
    for d in sanctioned_dirs:
        try:
            root = Path(d).resolve()
        except OSError:
            continue
        if p == root or root in p.parents:
            return True
    return False


def plan_remux_command(*, policy: AudioPolicy, render_path: str,
                       source_path: Optional[str] = None,
                       keeper_window: Tuple[float, float],
                       output_path: str,
                       sanctioned_dirs: Sequence[str]) -> list:
    """Plan an explicit non-Ref2VA remux ffmpeg command. ARGV LIST ONLY —
    the caller executes it via subprocess without a shell.

    Legacy/shared semantics (discard/remux): the video stream is copied
    from the render, rendered audio is discarded, and audio is taken
    from the explicit external source restricted to the keeper window
    (-ss/-t). This is not the native Ref2VA path.
    """
    if not isinstance(policy, AudioPolicy):
        raise Ref2VAQCStageError(
            f"policy must be AudioPolicy, got {type(policy).__name__}")
    for label, p in (("render_path", render_path),
                     ("output_path", output_path)):
        if not _contained(p, sanctioned_dirs):
            raise Ref2VAQCStageError(
                f"containment violation: {label} {p!r} does not resolve "
                f"under the sanctioned dirs {list(sanctioned_dirs)}")

    # G4 corrective: the audio input is the caller's EXPLICIT keeper /
    # full-mix source path — never silently the render path. No fallback.
    if source_path is None:
        raise Ref2VAQCStageError(
            "G4: plan_remux_command requires an explicit source_path "
            "(keeper/full-mix source); falling back to render_path as "
            "the audio input is forbidden — rendered audio is NEVER "
            "trusted")
    if not _contained(source_path, sanctioned_dirs):
        raise Ref2VAQCStageError(
            f"containment violation: remux source {source_path!r} does not "
            f"resolve under the sanctioned dirs")

    start, end = float(keeper_window[0]), float(keeper_window[1])
    duration = end - start
    return [
        "ffmpeg", "-y",
        "-i", str(render_path),                 # 0: H3 render (video)
        "-ss", f"{start:.6f}", "-t", f"{duration:.6f}",
        "-i", str(source_path),                    # 1: source window (audio)
        "-map", "0:v:0",                        # video from render
        "-map", "1:a:0",                        # audio from source
        "-c:v", "copy",                         # never re-encode video
        "-c:a", "aac", "-b:a", "192k",
        # AAC priming can make ``-shortest`` truncate a grid-aligned video
        # (the observed 56-frame cut became 53 frames). Bound output time
        # explicitly so audio packet timing cannot shorten the video.
        "-t", f"{duration:.6f}",
        str(output_path),
    ]


def run_ref2va_qc_stage(settings_doc: dict, *, judge: Optional[Callable],
                        critic_version: Optional[str] = None,
                        pre_audio_path: Optional[str] = None,
                        post_audio_path: Optional[str] = None,
                        intended_text: Optional[str] = None,
                        whisper_transcriber: Optional[Callable] = None,
                        whisper_pass_bar: float = 0.6,
                        evidence_path: Optional[str] = None,
                        video_path: Optional[str] = None,
                        expected_speaker: Optional[str] = None,
                        expected_action: Optional[str] = None,
                        vision_judge: Optional[Callable] = None,
                        vision_pass_bar: float = 0.7,
                        reference_image_path: Optional[str] = None
                        ) -> Ref2VAAudioQC:
    """Lane-aware Ref2VA-family audio QC stage, then fills QC evidence.

    - Policy enforcement: Ref2VA settings must carry
      discard_rendered_audio=False because generated native audio is the
      carrier. Explicit non-Ref2VA external-audio remux settings must
      carry discard_rendered_audio=True.
    - judge=None (schema-only): honest placeholders — critic_model
      present verbatim, scores None until a judge runs.
    - judge=callable: fills the four score fields from the judge's
      dict; critic identity reported verbatim.
    - Whisper evidence, when requested, reads the input guide as ``pre``
      and the generated native output as ``post``; identical paths are
      rejected so a guide cannot masquerade as generated output.
    - Vision evidence, when requested, checks still-image mouth activity,
      action, and speaker attribution. It does not measure phonetic A/V
      synchrony. Meeting these evidence bars is distinct from an implicit
      pass for merely carrying native audio.
    """
    if not isinstance(settings_doc, dict):
        raise Ref2VAQCStageError(
            f"settings doc must be a dict, got "
            f"{type(settings_doc).__name__}")
    policy_d = settings_doc.get("audio_policy")
    if not isinstance(policy_d, dict):
        raise Ref2VAQCStageError(
            "G4: settings doc carries no audio_policy — QC refuses "
            "artifacts whose audio did not pass through the "
            "discard/remux policy")
    if type(policy_d.get("discard_rendered_audio")) is not bool:
        raise Ref2VAQCStageError(
            "audio policy requires a boolean discard_rendered_audio")
    from predict.model_types import REF2VA_MODEL_TYPE
    if (settings_doc.get("model_type") == REF2VA_MODEL_TYPE
            and policy_d["discard_rendered_audio"] is not False):
        raise Ref2VAQCStageError("Ref2VA requires native audio, not guide replacement")
    if (settings_doc.get("model_type") != REF2VA_MODEL_TYPE
            and policy_d["discard_rendered_audio"] is not True):
        raise Ref2VAQCStageError("G4: non-Ref2VA remux lanes require discard_rendered_audio=True")

    def persist_evidence(whisper_payload, vision_payload=None) -> None:
        if not evidence_path:
            return
        try:
            p = Path(evidence_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(
                {"whisper_gates": whisper_payload,
                 "vision_judge": vision_payload},
                indent=2, sort_keys=True) + "\n")
        except OSError as exc:
            raise Ref2VAQCStageError(
                f"evidence_path: unable to persist Whisper evidence: {exc}"
            ) from exc

    whisper_requested = any(x is not None for x in (
        pre_audio_path, post_audio_path, intended_text,
        whisper_transcriber))
    whisper_evidence = None
    if whisper_requested:
        if not pre_audio_path or not post_audio_path or not intended_text:
            raise Ref2VAQCStageError(
                "Whisper pre/post gate requires pre_audio_path, "
                "post_audio_path, and intended_text")
        if Path(pre_audio_path).resolve() == Path(post_audio_path).resolve():
            raise Ref2VAQCStageError("post Whisper must read native render, not the input guide")
        whisper_evidence = None
        try:
            pre = run_whisper_gate(
                pre_audio_path, intended_text, transcriber=whisper_transcriber,
                phase="pre", pass_bar=whisper_pass_bar)
        except WhisperGateError as exc:
            partial = None
            if exc.evidence is not None:
                partial = exc.evidence.to_dict()
            persist_evidence({"pre": partial, "post": None})
            raise Ref2VAQCStageError(
                str(exc), whisper_evidence={
                    "pre": partial, "post": None}) from exc
        try:
            post = run_whisper_gate(
                post_audio_path, intended_text, transcriber=whisper_transcriber,
                phase="post", pass_bar=whisper_pass_bar)
        except WhisperGateError as exc:
            partial = None
            if exc.evidence is not None:
                partial = exc.evidence.to_dict()
            whisper_evidence = {"pre": pre.to_dict(), "post": partial}
            persist_evidence(whisper_evidence)
            raise Ref2VAQCStageError(
                str(exc), whisper_evidence=whisper_evidence) from exc
        whisper_evidence = {"pre": pre.to_dict(), "post": post.to_dict()}

    vision_requested = any(x is not None for x in (
        video_path, expected_speaker, expected_action, vision_judge))
    vision_evidence = None
    if vision_requested:
        if not video_path or not expected_speaker or not expected_action:
            raise Ref2VAQCStageError(
                "vision gate requires video_path, expected_speaker, and expected_action")
        try:
            vision_evidence = run_vision_judge(
                video_path, expected_speaker=expected_speaker,
                expected_action=expected_action, judge=vision_judge,
                pass_bar=vision_pass_bar,
                reference_image_path=reference_image_path).to_dict()
        except VisionJudgeError as exc:
            persist_evidence(whisper_evidence)
            raise Ref2VAQCStageError(
                str(exc), vision_scores=getattr(exc, "scores", None),
                vision_raw_response=getattr(exc, "raw_response", None),
                whisper_evidence=whisper_evidence,
            ) from exc

    if judge is None:
        qc = Ref2VAAudioQC(critic_version=None,
                           whisper_gates=whisper_evidence,
                           vision_judge=vision_evidence)
    else:
        scores = judge(settings_doc=settings_doc)
        unknown = [k for k in scores if k not in _SCORE_FIELDS]
        if unknown:
            raise Ref2VAQCStageError(
                f"judge returned unknown score field(s) {unknown}; "
                f"expected {list(_SCORE_FIELDS)}")
        try:
            qc = Ref2VAAudioQC(critic_version=critic_version,
                               whisper_gates=whisper_evidence,
                               vision_judge=vision_evidence, **scores)
        except AudioDataPlaneError as e:
            raise Ref2VAQCStageError(f"judge scores out of range: {e}") from e
    persist_evidence(whisper_evidence, vision_evidence)
    return qc
