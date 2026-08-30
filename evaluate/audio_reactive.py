"""Closure 2 — artifact-grounded audio-reactive evaluation lane.

A SEPARATE lane on top of the merged PR #47 primitives:
- predict/audio_manifest.py (readback_validate, require_manifest_for_render,
  audio_payload_hash)
- qc/audio_critic (the existing audio QC stage — G3/G4)

Zero-model by default: judge=None produces honest Qwen2-Audio-7B
placeholders with scores None and eligibility False until a real
judge result AND remux evidence exist. No GPU, no render, no ffmpeg
execution here — hashes and gates only. This lane does NOT touch
evaluate/render_qc.py, evaluate/metrics, or
training/run_baseline_then_gepa.py (preservation-tested).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from predict.audio_manifest import (
    AudioManifestError, MANIFEST_FILENAME, readback_validate,
    require_manifest_for_render,
)
from qc.audio_critic.ref2va_stage import (
    Ref2VAQCStageError, run_ref2va_qc_stage,
)

__all__ = [
    "AudioReactiveEvalError", "AudioReactiveInput",
    "evaluate_audio_artifact", "compare_audio_reactive",
]

_JUDGE_PLACEHOLDER_MODEL = "Qwen2-Audio-7B"
_SCORE_FIELDS = ("mouth_sync", "audio_fidelity",
                 "visual_motion_match", "audio_artifacts")


class AudioReactiveEvalError(ValueError):
    """Typed rejection. Missing/invalid artifacts are NEVER silent None."""


@dataclass(frozen=True)
class AudioReactiveInput:
    """Typed input for ONE audio-bearing artifact directory.

    render_path / settings_path must exist; remux_path is optional
    (eligibility requires it, evaluation does not). No fake render —
    the render file must be a real file on disk (produced elsewhere).
    """
    render_path: Path
    settings_path: Path
    remux_path: Optional[Path] = None
    audio_source: dict = field(default_factory=dict)
    candidate_label: str = ""
    seed: Optional[int] = None

    def __post_init__(self):
        for name in ("render_path", "settings_path"):
            p = Path(getattr(self, name))
            if not p.is_file():
                raise AudioReactiveEvalError(
                    f"{name}: artifact file missing: {p} — this lane "
                    "evaluates real artifacts only, no fake renders")
        if self.remux_path is not None and not Path(
                self.remux_path).is_file():
            raise AudioReactiveEvalError(
                f"remux_path: given but missing: {self.remux_path}")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def evaluate_audio_artifact(artifact: AudioReactiveInput, *,
                            judge: Optional[Callable] = None) -> dict:
    """Evaluate one audio-bearing artifact directory.

    Pipeline: manifest readback gate -> sha256 of every present file
    -> G3/G4 QC stage (existing stage module) -> eligibility.
    Deterministic, JSON-serializable result dict.
    """
    if not isinstance(artifact, AudioReactiveInput):
        raise AudioReactiveEvalError(
            f"artifact must be AudioReactiveInput, got "
            f"{type(artifact).__name__}")

    render = Path(artifact.render_path)
    if not render.is_file():
        raise AudioReactiveEvalError(
            f"render artifact missing: {render} — this lane evaluates "
            "real artifacts only, no fake renders")
    settings = Path(artifact.settings_path)
    if not settings.is_file():
        raise AudioReactiveEvalError(
            f"settings artifact missing: {settings} — typed rejection, "
            "never silent None")
    try:
        settings_doc = json.loads(
            Path(artifact.settings_path).read_text(encoding="utf-8"))
        manifest = require_manifest_for_render(render)
        readback_validate(manifest, settings_doc)
    except AudioManifestError as e:
        raise AudioReactiveEvalError(f"manifest gate rejected: {e}") from e
    except (json.JSONDecodeError, OSError) as e:
        raise AudioReactiveEvalError(
            f"settings doc unreadable: {e}") from e

    manifest_path = render.parent / MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise AudioReactiveEvalError(
            f"manifest vanished since validation: {manifest_path}")
    artifact_hashes = {"render": _sha256_file(render),
                       "manifest": _sha256_file(manifest_path)}
    remux_exists = (artifact.remux_path is not None
                    and Path(artifact.remux_path).is_file())
    if remux_exists:
        artifact_hashes["remux"] = _sha256_file(Path(artifact.remux_path))

    try:
        qc = run_ref2va_qc_stage(settings_doc, judge=judge)
    except Ref2VAQCStageError as e:
        raise AudioReactiveEvalError(str(e)) from e
    qc_d = qc.to_dict()

    judged = all(qc_d.get(f) is not None for f in _SCORE_FIELDS)
    remux_evidence = remux_exists and "remux" in artifact_hashes
    eligible_for_qc = judged and remux_evidence
    eligible_for_gepa = eligible_for_qc
    target = (sum(qc_d[f] for f in _SCORE_FIELDS) / len(_SCORE_FIELDS)
              if judged else None)

    if eligible_for_qc:
        verdict, reason = ("judged",
                           f"judged by {qc_d.get('critic_model')}; "
                           "remux evidence present")
    elif not judged and not remux_evidence:
        verdict, reason = ("pending",
                           "no judge result and no remux evidence — "
                           f"honest {_JUDGE_PLACEHOLDER_MODEL} placeholder")
    elif not judged:
        verdict, reason = ("pending",
                           "judge has not run — honest "
                           f"{_JUDGE_PLACEHOLDER_MODEL} placeholder, "
                           "scores None")
    else:
        verdict, reason = ("pending",
                           "judged but remux evidence missing — "
                           "eligibility withheld")

    return {
        "candidate_label": artifact.candidate_label,
        "seed": artifact.seed,
        "audio_source": dict(artifact.audio_source),
        "artifact_hashes": artifact_hashes,
        "manifest_hash": artifact_hashes["manifest"],
        "remux_evidence": remux_evidence,
        "qc": qc_d,
        "target_qc_score": target,
        "gate_failures": 0,
        "eligible_for_qc": eligible_for_qc,
        "eligible_for_gepa": eligible_for_gepa,
        "verdict": verdict,
        "reason": reason,
        "provenance": {
            "lane": "audio_reactive",
            "judge_used": judge is not None,
            "critic_model": qc_d.get("critic_model"),
        },
    }


def compare_audio_reactive(baseline: dict, challenger: dict) -> dict:
    """Pure baseline-vs-challenger comparison, this lane ONLY.

    - both records must be eligible (judged + remux evidence)
    - target QC scores must be numeric (text-only scores rejected)
    - challenger must not increase gate failures
    """
    for label, rec in (("baseline", baseline), ("challenger", challenger)):
        if not (isinstance(rec, dict) and rec.get("eligible_for_gepa")):
            raise AudioReactiveEvalError(
                f"{label} record not eligible for this audio lane — "
                "both sides must be judged artifacts with remux evidence")
    scores = {}
    for label, rec in (("baseline", baseline), ("challenger", challenger)):
        s = rec.get("target_qc_score")
        if isinstance(s, bool) or not isinstance(s, (int, float)):
            raise AudioReactiveEvalError(
                f"{label} target_qc_score must be numeric to compare — "
                f"text-only scores are rejected (got {s!r})")
        scores[label] = float(s)
    if challenger.get("gate_failures", 0) > baseline.get("gate_failures", 0):
        raise AudioReactiveEvalError(
            "challenger increased gate failures "
            f"({baseline.get('gate_failures', 0)} -> "
            f"{challenger.get('gate_failures', 0)}) — rejected")
    if scores["challenger"] > scores["baseline"]:
        decision = "challenger"
    elif scores["challenger"] < scores["baseline"]:
        decision = "baseline"
    else:
        decision = "tie"
    return {
        "lane": "audio_reactive",
        "decision": decision,
        "baseline_score": scores["baseline"],
        "challenger_score": scores["challenger"],
        "baseline_hashes": baseline.get("artifact_hashes"),
        "challenger_hashes": challenger.get("artifact_hashes"),
    }
