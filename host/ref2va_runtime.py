"""Production Ref2VA runtime closure — the seam that WIRES the
existing Ref2VA primitives end-to-end without touching the generic
H3 adapter:

    Ref2VAProfile.build_settings  (typed settings; existing contract)
      -> injected render callable (exactly once; production
         points this at WanGP/SshHost on the remote GPU host — NEVER
         hardcoded here)
      -> write_audio_manifest + readback_validate (existing)
      -> preserve the generated native A/V render byte-for-byte at the
         legacy remux.mp4 filename required by downstream callers
      -> evaluate_audio_artifact (existing audio-reactive lane)
      -> JSON-serializable evidence (hashes + QC + eligibility)

Fail-closed: any missing/mismatched artifact, containment escape,
native-preservation hash mismatch, judge crash, or policy violation
raises the typed Ref2VARuntimeError BEFORE any QC/GEPA eligibility can
be claimed.

PR #51 review hardening:
- ALL four paths (settings/raw/source/remux) are containment-checked
  BEFORE any filesystem write, mkdir, or injected render call.
- The render callable's RETURNED path is revalidated (containment +
  source != raw + on-disk) before the manifest is written and the
  native render is preserved.
- A prebuilt settings_doc is runtime-validated (see
  _validate_settings_doc for the exact, honestly-scoped boundary).
- Policy construction failures and AudioDataPlaneError are wrapped
  as Ref2VARuntimeError — no raw ValueError leaks.

Historical seam note: ``runner`` and ``safe_argv_runner`` remain in the
public input/API surface for compatibility, but the native Ref2VA path never
invokes a planner or runner to replace generated audio.
``plan_remux_command`` remains reserved for non-Ref2VA external-audio lanes.
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
from predict.speaker_manifest import (
    SpeakerManifestError, readback_validate_speaker_manifest,
    write_speaker_manifest,
)
from predict.render_profiles import (
    ProfileError, Ref2VAProfile,
)
from predict.model_types import REF2VA_MODEL_TYPE
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
    must be supplied — never both, never neither. ``render`` is the
    active injected seam that produces the raw native H3 render file
    (tests use tiny fixtures; production points at WanGP/SshHost).
    ``runner`` is retained for constructor/API compatibility with the
    legacy remux seam; this native runtime does not call it.
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
    # Continuation jobs carry a grid contract. The optional probe is an
    # injected seam for tests; production defaults to local ffprobe after
    # the remux has been materialized in the pull namespace.
    continuation: bool = False
    frame_probe: Optional[Callable[[Path], int]] = None
    completed_render_recovery: Optional[dict] = None

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


def _probe_frame_count(path: Path) -> int:
    """Count final video frames without shell interpretation."""
    proc = subprocess.run([
        "ffprobe", "-v", "error", "-count_frames",
        "-select_streams", "v:0", "-show_entries",
        "stream=nb_read_frames", "-of", "csv=p=0", str(path),
    ], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise Ref2VARuntimeError(
            f"post-remux ffprobe failed for {path}: "
            f"{(proc.stderr or '').strip()[:200]}")
    try:
        return int((proc.stdout or "").strip().split(",")[-1])
    except (TypeError, ValueError) as exc:
        raise Ref2VARuntimeError(
            f"post-remux ffprobe returned no frame count for {path}: "
            f"{(proc.stdout or '')!r}") from exc


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

    A complete reconstruction of the original briefs and profile decision
    is not possible from this envelope. The host boundary separately probes
    the actual guide and records mapped conditioning evidence. This runtime
    validates the native wire shape and local manifest/path contracts rather
    than claiming to repeat all planning or host checks. Enforced here:
      - dict type
      - model_type == predict.model_types.REF2VA_MODEL_TYPE
      - audio_prompt_type == 'A'
      - sanctioned audio manifest block present (all four keys) via
        build_audio_manifest + readback_validate
      - audio_policy typed through AudioPolicy
      - discard_rendered_audio is False (native audio preserved)
      - ref2va_wire_settings accepts the doc as a native single-cut
        envelope with no multishot/script dispatch fields
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
    if policy.discard_rendered_audio is not False:
        raise Ref2VARuntimeError(
            "Ref2VA native audio policy requires discard_rendered_audio=False")
    from predict.ref2va_settings import ref2va_wire_settings, Ref2VASettingsError
    try:
        ref2va_wire_settings(settings_doc)
    except Ref2VASettingsError as exc:
        raise Ref2VARuntimeError(str(exc)) from exc
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
    speaker_manifest = settings_doc.get("speaker_manifest")
    if speaker_manifest is not None:
        try:
            # Validate the exact schema before any GPU work.  The sidecar is
            # written/read back after the render, but malformed attribution
            # must fail at the runtime boundary as well.
            from predict.speaker_manifest import SpeakerManifest
            SpeakerManifest.from_dict(speaker_manifest)
        except SpeakerManifestError as e:
            raise Ref2VARuntimeError(
                f"settings doc speaker_manifest rejected: {e}") from e
    return settings_doc


def safe_argv_runner(argv: list) -> int:
    """Conservative legacy/shared argv runner: exec WITHOUT a shell.

    The runtime cannot inspect what an injected callable does
    internally — this helper only guarantees that WHEN it is used,
    the argv list is executed directly (no shell interpretation of
    metacharacters). argv must be a list of str; anything else is a
    typed rejection. Returns the process exit code. Native Ref2VA
    preservation does not invoke this helper; it remains available to
    explicit non-Ref2VA remux callers.
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

    # Anti-substitution pre-flight: the input guide/source must never
    # masquerade as the generated native output by occupying the raw
    # render path.
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

    # (b2) REVALIDATE the returned raw path: containment, source/raw
    # separation, and on-disk existence — BEFORE any manifest write or
    # native preservation. A render callable returning a substituted
    # path (including the audio source itself) fails closed here.
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
    # Continuation jobs additionally persist the versioned speaker/turn
    # attribution beside the audio manifest.  Legacy Ref2VA jobs remain
    # byte-compatible and simply omit this optional block.
    speaker_manifest = settings_doc.get("speaker_manifest")
    if speaker_manifest is not None:
        try:
            speaker_path = write_speaker_manifest(speaker_manifest, raw)
            readback_validate_speaker_manifest(
                json.loads(speaker_path.read_text(encoding="utf-8")),
                speaker_manifest)
        except (SpeakerManifestError, json.JSONDecodeError, OSError) as e:
            raise Ref2VARuntimeError(
                f"speaker manifest gate rejected: {e}") from e

    # Preserve the native A/V container byte-for-byte. The legacy remux.mp4
    # filename is retained for caller compatibility; evidence explicitly
    # names the native carrier and preserves the raw/final hashes.
    import shutil
    try:
        if remux.resolve() != raw.resolve():
            shutil.copyfile(raw, remux)
        if _sha256_file(raw) != _sha256_file(remux):
            raise Ref2VARuntimeError("native audio/video preservation hash mismatch")
    except OSError as exc:
        raise Ref2VARuntimeError(f"native artifact preservation failed: {exc}") from exc

    # Validate the FINAL legacy-named artifact after preservation. This
    # retains the historical frame-count output invariant (the old external
    # remux could truncate 56 frames to 53) even though a byte-identical
    # native copy cannot alter the stream.
    if inp.continuation:
        try:
            expected = int(settings_doc.get("video_length") or 0)
        except (TypeError, ValueError):
            expected = 0
        if expected > 0:
            probe = inp.frame_probe or _probe_frame_count
            try:
                actual = int(probe(remux))
            except Ref2VARuntimeError:
                raise
            except Exception as exc:
                raise Ref2VARuntimeError(
                    f"post-remux frame validation probe failed: {exc}") from exc
            if actual != expected:
                raise Ref2VARuntimeError(
                    "post-remux continuation frame-count validation failed: "
                    f"expected {expected}f, got {actual}f in {str(remux)!r}")

    # (g) evaluate the final legacy-named native artifact through the
    # existing lane, forwarding critic_version to the ACTUAL QC. Native
    # preservation does not itself constitute a QC pass.
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
        "audio_carrier": "native_h3",
        "final_artifact_path": str(remux),
        "native_preserved": True,
    }
    return evidence
