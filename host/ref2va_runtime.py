"""Production Ref2VA runtime closure — the seam that WIRES the
existing Ref2VA primitives end-to-end without touching the generic
H3 adapter:

    Ref2VAProfile.build_settings  (typed settings; existing contract)
      -> injected render callable (exactly once; production later
         points this at WanGP/SshHost on the remote GPU host — NEVER
         hardcoded here)
      -> write_audio_manifest + readback_validate (existing)
      -> plan_remux_command with EXPLICIT keeper/full-mix source
         (existing planner; argv list only, no shell)
      -> injected argv runner (rc must be 0; remux must exist)
      -> evaluate_audio_artifact (existing audio-reactive lane)
      -> JSON-serializable evidence (hashes + QC + eligibility)

Fail-closed: any missing/mismatched artifact, containment escape,
nonzero ffmpeg, judge crash, or G4 policy violation raises the typed
Ref2VARuntimeError BEFORE any QC/GEPA eligibility can be claimed.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Sequence, Union

from evaluate.audio_reactive import (
    AudioReactiveEvalError as AudioReactiveError,
    AudioReactiveInput, evaluate_audio_artifact,
)
from predict.audio_dataplane import AudioPolicy
from predict.audio_manifest import (
    AudioManifestError, readback_validate, write_audio_manifest,
)
from predict.render_profiles import ProfileError, Ref2VAProfile
from qc.audio_critic.ref2va_stage import (
    Ref2VAQCStageError, plan_remux_command,
)

__all__ = ["Ref2VARuntimeError", "Ref2VARuntimeInput",
           "run_ref2va_runtime"]

RenderFn = Callable[[Any], Union[str, os.PathLike]]
RunnerFn = Callable[[list], int]
JudgeFn = Callable[..., dict]


class Ref2VARuntimeError(RuntimeError):
    """Typed fail-closed rejection for the Ref2VA runtime."""


@dataclass
class Ref2VARuntimeInput:
    """Typed input for ONE Ref2VA production run.

    Either ``profile_build_kwargs`` (validated through
    Ref2VAProfile.build_settings) or a pre-validated ``settings_doc``
    must be supplied — never both, never neither. ``render`` /
    ``runner`` are injected seams: the render callable produces the
    raw H3 render file (tests use tiny fixtures; production points at
    WanGP/SshHost later); the runner receives an ARGV LIST (shell
    semantics belong to the caller, who must exec without a shell).
    """
    briefs: Sequence
    decision: Any
    raw_render_path: Path
    audio_source_path: Path
    remux_output_path: Path
    settings_path: Path
    sanctioned_dirs: Sequence[str]
    render: RenderFn
    runner: RunnerFn
    profile_build_kwargs: Optional[dict] = None
    settings_doc: Optional[dict] = None
    judge: Optional[JudgeFn] = None
    critic_version: Optional[str] = None

    def __post_init__(self):
        has_kw = self.profile_build_kwargs is not None
        has_doc = self.settings_doc is not None
        if has_kw == has_doc:
            raise Ref2VARuntimeError(
                "supply exactly one of profile_build_kwargs (validated "
                "through Ref2VAProfile) or settings_doc — got "
                f"kwargs={has_kw} doc={has_doc}")
        for name in ("render", "runner"):
            if not callable(getattr(self, name)):
                raise Ref2VARuntimeError(
                    f"{name}: must be an injected callable, got "
                    f"{type(getattr(self, name)).__name__}")
        if not self.sanctioned_dirs:
            raise Ref2VARuntimeError(
                "sanctioned_dirs: required for path containment — "
                "got none")


def _sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _policy_from_doc(settings_doc: dict) -> AudioPolicy:
    d = dict(settings_doc.get("audio_policy") or {})
    if "remux_window" in d:
        d["remux_window"] = tuple(d["remux_window"])
    return AudioPolicy(**d)


def run_ref2va_runtime(inp: Ref2VARuntimeInput) -> dict:
    """Execute the full Ref2VA closure. Returns JSON-serializable
    evidence; raises Ref2VARuntimeError on ANY fail-closed path."""
    if not isinstance(inp, Ref2VARuntimeInput):
        raise Ref2VARuntimeError(
            f"inp must be Ref2VARuntimeInput, got "
            f"{type(inp).__name__}")

    # (a) validate/build settings through the existing profile contract
    if inp.profile_build_kwargs is not None:
        try:
            settings_doc = Ref2VAProfile().build_settings(
                inp.briefs, inp.decision, **inp.profile_build_kwargs)
        except ProfileError as e:
            raise Ref2VARuntimeError(f"settings build rejected: {e}") from e
    else:
        settings_doc = dict(inp.settings_doc)
    settings_path = Path(inp.settings_path)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(settings_doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")

    raw = Path(inp.raw_render_path)
    source = Path(inp.audio_source_path)
    remux = Path(inp.remux_output_path)

    # G4 (pre-flight): the explicit audio source must NEVER be the raw
    # render — rendered audio is never trusted.
    try:
        if source.resolve() == raw.resolve():
            raise Ref2VARuntimeError(
                "G4: audio_source_path must not be the raw render — "
                "rendered audio is NEVER trusted; supply the explicit "
                "keeper/full-mix source")
    except OSError as e:  # pragma: no cover - resolve failure
        raise Ref2VARuntimeError(f"audio source unreadable: {e}") from e

    # (b) injected render callable — exactly once
    out = inp.render(inp)
    if out is not None:
        raw = Path(out)

    # (c) require readable raw render
    if not raw.is_file():
        raise Ref2VARuntimeError(
            f"raw render missing after render(): {raw} — the runtime "
            "requires a real on-disk artifact")

    # (d) deterministic manifest next to the raw render + readback
    try:
        manifest_path = write_audio_manifest(settings_doc, raw)
        readback_validate(
            json.loads(manifest_path.read_text(encoding="utf-8")),
            settings_doc)
    except (AudioManifestError, json.JSONDecodeError, OSError) as e:
        raise Ref2VARuntimeError(f"manifest gate rejected: {e}") from e

    # (e) plan remux: EXPLICIT source, containment enforced by the
    # existing planner (argv list only — no shell strings anywhere)
    policy = _policy_from_doc(settings_doc)
    try:
        argv = plan_remux_command(
            policy=policy, render_path=str(raw),
            source_path=str(source),
            keeper_window=tuple(policy.remux_window),
            output_path=str(remux),
            sanctioned_dirs=list(inp.sanctioned_dirs))
    except Ref2VAQCStageError as e:
        raise Ref2VARuntimeError(str(e)) from e

    # (f) execute via injected runner; rc=0 + readable remux required
    rc = inp.runner(argv)
    if rc != 0:
        raise Ref2VARuntimeError(
            f"ffmpeg/remux runner returned rc={rc} — nonzero remux "
            "exit is a hard failure")
    if not remux.is_file():
        raise Ref2VARuntimeError(
            f"remux output missing after rc=0 runner: {remux} — "
            "eligibility requires real remux evidence")

    # (g) evaluate the REMUX artifact through the existing lane
    try:
        artifact = AudioReactiveInput(
            render_path=raw, settings_path=settings_path,
            remux_path=remux,
            audio_source={"explicit_source": str(source)})
    except AudioReactiveError as e:
        raise Ref2VARuntimeError(f"artifact gate rejected: {e}") from e
    try:
        res = evaluate_audio_artifact(artifact, judge=inp.judge)
    except AudioReactiveError as e:
        raise Ref2VARuntimeError(str(e)) from e
    except Exception as e:  # judge crash etc.
        raise Ref2VARuntimeError(
            f"evaluation failed ({type(e).__name__}): {e}") from e

    # (h) JSON-serializable evidence
    evidence = dict(res)
    evidence["settings_hash"] = _sha256_file(settings_path)
    evidence["raw_render_hash"] = evidence["artifact_hashes"]["render"]
    evidence["manifest_hash"] = evidence["artifact_hashes"]["manifest"]
    evidence["remux_hash"] = evidence["artifact_hashes"]["remux"]
    evidence["runtime"] = {
        "raw_render_path": str(raw),
        "remux_output_path": str(remux),
        "explicit_audio_source": str(source),
        "critic_version": inp.critic_version,
        "lane": "ref2va_runtime",
    }
    return evidence
