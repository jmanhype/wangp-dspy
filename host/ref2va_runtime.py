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

PR #51 review hardening:
- ALL four paths (settings/raw/source/remux) are containment-checked
  BEFORE any filesystem write, mkdir, or injected render call.
- The render callable's RETURNED path is revalidated (containment +
  G4 source != raw + on-disk) before manifest/remux; remux argv is
  replanned against the ACTUAL raw path.
- A prebuilt settings_doc is runtime-validated (see
  _validate_settings_doc for the exact, honestly-scoped boundary).
- Policy construction failures and AudioDataPlaneError are wrapped
  as Ref2VARuntimeError — no raw ValueError leaks.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Sequence, Union

from evaluate.audio_reactive import (
    AudioReactiveEvalError as AudioReactiveError,
    AudioReactiveInput, evaluate_audio_artifact,
)
from predict.audio_dataplane import AudioDataPlaneError, AudioPolicy
from predict.audio_manifest import (
    AudioManifestError, build_audio_manifest, readback_validate,
    write_audio_manifest,
)
from predict.render_profiles import (
    ProfileError, REF2VA_MODEL_TYPE, Ref2VAProfile,
)
from qc.audio_critic.ref2va_stage import (
    Ref2VAQCStageError, plan_remux_command,
)

__all__ = ["Ref2VARuntimeError", "Ref2VARuntimeInput",
           "run_ref2va_runtime", "safe_argv_runner"]

RenderFn = Callable[[Any], Union[str, os.PathLike]]
RunnerFn = Callable[[list], int]
JudgeFn = Callable[..., dict]

_SCORE_FIELDS = ("mouth_sync", "audio_fidelity",
                 "visual_motion_match", "audio_artifacts")


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
    semantics belong to the caller, who must exec without a shell —
    see ``safe_argv_runner`` for a conservative default).
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


def _contained(path, sanctioned_dirs: Sequence[str]) -> bool:
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


def _require_contained(label: str, path,
                       sanctioned_dirs: Sequence[str]) -> Path:
    if not _contained(path, sanctioned_dirs):
        raise Ref2VARuntimeError(
            f"containment violation: {label} {str(path)!r} does not "
            f"resolve under the sanctioned dirs "
            f"{list(sanctioned_dirs)} — refusing before any write, "
            "render, or manifest activity")
    return Path(path)


def _policy_from_doc(settings_doc: dict) -> AudioPolicy:
    """Typed policy reconstruction; ANY construction failure is a
    Ref2VARuntimeError (no raw ValueError/AudioDataPlaneError leak)."""
    d = dict(settings_doc.get("audio_policy") or {})
    if "remux_window" in d and isinstance(d["remux_window"], list):
        d["remux_window"] = tuple(d["remux_window"])
    try:
        return AudioPolicy(**d)
    except AudioDataPlaneError as e:
        raise Ref2VARuntimeError(f"audio policy rejected: {e}") from e
    except TypeError as e:
        raise Ref2VARuntimeError(
            f"audio policy malformed: {e}") from e


def _validate_settings_doc(settings_doc, sanctioned_dirs) -> dict:
    """Runtime validation of a settings doc BEFORE any render/write.

    Honest boundary (documented, per review): a COMPLETE
    Ref2VAProfile reconstruction (briefs/decision, <Picture/Audio N>
    token contiguity, guide==shot duration, 4-15s cap, image_refs)
    is NOT re-derivable from the persisted doc — the script text is
    flattened and the durations/decision are not carried. What IS
    enforced here, fail-closed:
      - dict type
      - model_type == 'ref2va_lip_sync'
      - audio_prompt_type == 'A'
      - sanctioned audio manifest block present (all four keys) via
        build_audio_manifest + readback_validate
      - audio_policy typed through AudioPolicy
      - discard_rendered_audio is True (G4)
      - audio_guide is a readable path contained in sanctioned_dirs
    """
    if not isinstance(settings_doc, dict):
        raise Ref2VARuntimeError(
            f"settings doc must be a dict, got "
            f"{type(settings_doc).__name__}")
    if settings_doc.get("model_type") != REF2VA_MODEL_TYPE:
        raise Ref2VARuntimeError(
            "settings doc model_type must be "
            f"{REF2VA_MODEL_TYPE!r}, got "
            f"{settings_doc.get('model_type')!r}")
    if str(settings_doc.get("audio_prompt_type", "")).strip().upper() \
            != "A":
        raise Ref2VARuntimeError(
            "settings doc audio_prompt_type must be 'A', got "
            f"{settings_doc.get('audio_prompt_type')!r}")
    try:
        readback_validate(build_audio_manifest(settings_doc),
                          settings_doc)
    except AudioManifestError as e:
        raise Ref2VARuntimeError(
            f"settings doc audio block rejected: {e}") from e
    policy = _policy_from_doc(settings_doc)
    if policy.discard_rendered_audio is not True:
        raise Ref2VARuntimeError(
            "G4: settings doc discard_rendered_audio must be True — "
            "rendered audio is NEVER trusted")
    guide = settings_doc.get("audio_guide")
    if not isinstance(guide, str) or not guide.strip():
        raise Ref2VARuntimeError(
            f"settings doc audio_guide must be a non-empty path "
            f"string, got {guide!r}")
    if not Path(guide).is_file():
        raise Ref2VARuntimeError(
            f"settings doc audio_guide not readable: {guide}")
    _require_contained("settings doc audio_guide", guide,
                       sanctioned_dirs)
    return settings_doc


def safe_argv_runner(argv: list) -> int:
    """Conservative default argv runner: exec WITHOUT a shell.

    The runtime cannot inspect what an injected callable does
    internally — this helper only guarantees that WHEN it is used,
    the argv list is executed directly (no shell interpretation of
    metacharacters). argv must be a list of str; anything else is a
    typed rejection. Returns the process exit code.
    """
    if not isinstance(argv, list) or not all(
            isinstance(a, str) for a in argv):
        raise Ref2VARuntimeError(
            "safe_argv_runner: argv must be a LIST of str (exec'd "
            f"without a shell), got {type(argv).__name__}")
    return subprocess.run(argv, check=False).returncode


def run_ref2va_runtime(inp: Ref2VARuntimeInput) -> dict:
    """Execute the full Ref2VA closure. Returns JSON-serializable
    evidence; raises Ref2VARuntimeError on ANY fail-closed path."""
    if not isinstance(inp, Ref2VARuntimeInput):
        raise Ref2VARuntimeError(
            f"inp must be Ref2VARuntimeInput, got "
            f"{type(inp).__name__}")

    # (0) containment FIRST — before any mkdir, write, render, or
    # manifest activity. Every requested path must resolve under the
    # sanctioned dirs.
    settings_path = _require_contained(
        "settings_path", inp.settings_path, inp.sanctioned_dirs)
    raw = _require_contained(
        "raw_render_path", inp.raw_render_path, inp.sanctioned_dirs)
    source = _require_contained(
        "audio_source_path", inp.audio_source_path,
        inp.sanctioned_dirs)
    remux = _require_contained(
        "remux_output_path", inp.remux_output_path,
        inp.sanctioned_dirs)
    if not source.is_file():
        raise Ref2VARuntimeError(
            f"audio source unreadable: {source}")

    # (a) validate/build settings through the existing profile
    # contract (a prebuilt settings_doc is runtime-validated here
    # too — see _validate_settings_doc for the exact boundary)
    if inp.profile_build_kwargs is not None:
        try:
            settings_doc = Ref2VAProfile().build_settings(
                inp.briefs, inp.decision, **inp.profile_build_kwargs)
        except ProfileError as e:
            raise Ref2VARuntimeError(f"settings build rejected: {e}") from e
    else:
        settings_doc = inp.settings_doc
    settings_doc = _validate_settings_doc(
        settings_doc, inp.sanctioned_dirs)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(settings_doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")

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

    # (b2) REVALIDATE the returned raw path: containment, G4, and
    # on-disk — BEFORE any manifest write or remux planning. A render
    # callable returning a substituted path (including the audio
    # source itself) fails closed here.
    if not _contained(raw, inp.sanctioned_dirs):
        raise Ref2VARuntimeError(
            f"containment violation: render() returned "
            f"{str(raw)!r} which does not resolve under the "
            f"sanctioned dirs {list(inp.sanctioned_dirs)}")
    try:
        if source.resolve() == raw.resolve():
            raise Ref2VARuntimeError(
                "G4: render() returned the audio source as the raw "
                "render — rendered audio is NEVER trusted")
    except OSError as e:
        raise Ref2VARuntimeError(f"render path unreadable: {e}") from e

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

    # (e) plan remux against the ACTUAL raw path: EXPLICIT source,
    # containment enforced by the existing planner (argv list only —
    # no shell strings anywhere)
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

    # (g) evaluate the REMUX artifact through the existing lane,
    # forwarding the critic_version so it reaches the ACTUAL QC
    try:
        artifact = AudioReactiveInput(
            render_path=raw, settings_path=settings_path,
            remux_path=remux,
            audio_source={"explicit_source": str(source)})
    except AudioReactiveError as e:
        raise Ref2VARuntimeError(f"artifact gate rejected: {e}") from e
    try:
        res = evaluate_audio_artifact(
            artifact, judge=inp.judge, critic_version=inp.critic_version)
    except AudioReactiveError as e:
        raise Ref2VARuntimeError(str(e)) from e
    except Exception as e:  # judge crash etc.
        raise Ref2VARuntimeError(
            f"evaluation failed ({type(e).__name__}): {e}") from e

    # (g2) when judged, the ACTUAL qc critic_version must match the
    # input version — a disconnect fails closed, never silently
    qc_ver = (res.get("qc") or {}).get("critic_version")
    judged = all((res.get("qc") or {}).get(f) is not None
                 for f in _SCORE_FIELDS)
    if judged and qc_ver != inp.critic_version:
        raise Ref2VARuntimeError(
            f"critic_version disconnect: input "
            f"{inp.critic_version!r} but QC reported {qc_ver!r} "
            "while judged — refusing to claim eligibility on a "
            "mismatched critic identity")

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
        "critic_version": qc_ver,
        "lane": "ref2va_runtime",
    }
    return evidence
