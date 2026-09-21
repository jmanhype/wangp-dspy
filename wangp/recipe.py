"""Versioned render recipe: pin a run's logical inputs and detect drift.

A recipe records what a finished run *was* -- the repository version, the run
identity, the brief and plan identities, the retry policy, the per-cut gate
thresholds in force, and the artifacts and inputs the run recorded -- and a
verifier that reports per-field drift against the current state of the run.

Verification re-reads the world rather than re-reading the manifest: referenced
files are re-hashed from their current bytes, and a field the run never recorded
is reported as ``missing`` instead of being assumed equal to another absent
value. That is the difference between a recipe that documents a run and one that
can actually catch a tampered artifact.

Not promised: a generative render is lossy, so an identical recipe may still
produce different pixels on a re-render (different seed, model build, or host
environment). That limit is recorded in the manifest itself.
"""

from __future__ import annotations

import hashlib
import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from wangp.diagnostics import redact_sensitive

RECIPE_SCHEMA = "wangp-dspy.render-recipe/v2"
NOT_PROMISED = (
    "byte-identical pixels: a generative render is lossy, so the same recipe may "
    "produce different pixels when re-rendered with a different seed, model "
    "build, or host environment.",
    "anything the run did not record: an input absent from the run's provenance "
    "cannot be pinned, and verification reports it as missing rather than "
    "assuming it matches.",
    "the machine that verifies: host configuration of the verifying checkout is "
    "recorded as context only and is never compared against the recipe.",
)


class RecipeError(ValueError):
    """A recipe or a run's evidence could not be built, read, or verified."""


class _Unrecorded:
    """Sentinel: the run did not record this value."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "<unrecorded>"


UNRECORDED = _Unrecorded()


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(payload), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, default=str,
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RecipeError(f"file is missing: {path}") from exc
    except (OSError, UnicodeError) as exc:
        raise RecipeError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RecipeError(f"{path} is not valid JSON: {exc}") from exc


def _run_bundle(run: str | Path) -> Path:
    bundle = Path(run).expanduser().resolve()
    if bundle.is_file():
        bundle = bundle.parent
    if not bundle.is_dir():
        raise RecipeError(f"run directory does not exist: {bundle}")
    provenance_path = bundle / "final-provenance.json"
    if not provenance_path.is_file():
        raise RecipeError(f"final-provenance.json is missing: {provenance_path}")
    return bundle


def _provenance(bundle: Path) -> dict[str, Any]:
    payload = _read_json(bundle / "final-provenance.json")
    if not isinstance(payload, dict):
        raise RecipeError(
            f"final provenance is not an object: {bundle / 'final-provenance.json'}")
    cuts = payload.get("cuts")
    if cuts is not None and not isinstance(cuts, list):
        raise RecipeError("final provenance field 'cuts' is not a list")
    for index, cut in enumerate(cuts or []):
        if not isinstance(cut, Mapping):
            raise RecipeError(
                f"final provenance cut {index} is not an object")
    return payload


def _recorded_file(bundle: Path, raw_path: Any) -> dict[str, Any] | None:
    """Describe one referenced file by re-hashing its current bytes.

    A review bundle is verified as it sits on disk: when the recorded path is
    absolute (provenance stores the worktree that produced it) but a file of the
    same name exists inside this bundle, the in-bundle copy is the artifact under
    review and is the one hashed.
    """
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    recorded = Path(raw_path)
    in_bundle = bundle / recorded.name
    if in_bundle.is_file():
        candidate = in_bundle.resolve()
    elif recorded.is_absolute():
        candidate = recorded
    else:
        candidate = (bundle / recorded).resolve()
    if not candidate.is_file():
        return {"path": str(candidate), "sha256": None, "present": False}
    return {"path": str(candidate), "sha256": _sha256_file(candidate), "present": True}


def _cut_gate_thresholds(cut: Mapping[str, Any]) -> dict[str, Any]:
    """Per-cut pass bars, so a change in any single cut is visible."""
    thresholds: dict[str, Any] = {"clip_index": cut.get("clip_index")}
    whisper = cut.get("whisper") or {}
    for phase in ("pre", "post"):
        bar = (whisper.get(phase) or {}).get("pass_bar")
        thresholds[f"whisper_{phase}_pass_bar"] = bar
    vision = cut.get("vision") or {}
    thresholds["vision_pass_bar"] = vision.get("pass_bar")
    av_sync = cut.get("av_sync") or {}
    thresholds["syncnet_model_sha256"] = av_sync.get("model_sha256")
    av_bar = av_sync.get("pass_bar")
    if isinstance(av_bar, Mapping):
        thresholds["syncnet_min_confidence"] = av_bar.get("min_confidence")
        thresholds["syncnet_max_abs_offset_frames_25fps"] = av_bar.get(
            "max_abs_offset_frames_25fps")
    return thresholds


def _cut_media(bundle: Path, cut: Mapping[str, Any]) -> dict[str, Any]:
    av_sync = cut.get("av_sync") or {}
    recorded = av_sync.get("video_sha256")
    raw_path = av_sync.get("video_path")
    entry: dict[str, Any] = {
        "clip_index": cut.get("clip_index"),
        "recorded_video_sha256": recorded,
        "video": _recorded_file(bundle, raw_path),
    }
    return entry


def _plan_hashes(provenance: Mapping[str, Any]) -> dict[str, Any]:
    """Canonical and raw plan identity, including path-keyed older formats."""
    approval = provenance.get("operator_approval") or {}
    reconciliation = provenance.get("reconciliation") or {}
    inputs = provenance.get("inputs") or {}
    canonical = approval.get("canonical_plan_sha256") or reconciliation.get(
        "canonical_plan_sha256")
    raw = inputs.get("plan_sha256")
    if raw is None:
        # Older runs key recorded hashes by plan path instead of a named field.
        candidates = [
            value for key, value in inputs.items()
            if isinstance(value, str) and str(key).endswith("plan.json")
        ]
        raw = candidates[0] if len(candidates) == 1 else None
    return {"canonical_sha256": canonical, "raw_plan_sha256": raw}


def build_recipe(
    run: str | Path,
    repository_root: str | Path,
    *,
    context_configuration: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build the canonical recipe manifest for one finished run."""
    bundle = _run_bundle(run)
    root = Path(repository_root).expanduser().resolve()
    provenance = _provenance(bundle)
    if context_configuration is None:
        # Informational only: which host this checkout resolves. Recorded in
        # `context` and never compared, because it is not run-owned evidence.
        context_configuration = _local_context_configuration(root, environ)
    inputs = provenance.get("inputs") or {}
    approval = provenance.get("operator_approval") or {}
    media = provenance.get("final_media") or {}
    queue = provenance.get("queue_evidence") or {}
    version_path = root / "VERSION"
    repository_version = (
        version_path.read_text(encoding="utf-8").strip()
        if version_path.is_file() else None
    )
    recorded_settings = {
        str(name): str(digest)
        for name, digest in (provenance.get("settings_hashes") or {}).items()
    }
    recipe = {
        "schema_version": RECIPE_SCHEMA,
        "pinned": {
            "run_id": provenance.get("run_id"),
            "repository_version": repository_version,
            "plan": _plan_hashes(provenance),
            "brief": {
                "semantic_hash": approval.get("brief_hash"),
                "raw_sha256": (
                    approval.get("raw_brief_sha256") or inputs.get("brief_sha256")),
            },
            "assembled_media": {
                "recorded_sha256": media.get("sha256"),
                "file": _recorded_file(bundle, media.get("path")),
            },
            "cuts": [_cut_media(bundle, cut) for cut in provenance.get("cuts") or []],
            "cut_gate_thresholds": [
                _cut_gate_thresholds(cut) for cut in provenance.get("cuts") or []
            ],
            "recorded_settings_hashes": recorded_settings,
            "retry_policy": dict(provenance.get("retry_policy") or {}),
            "queue_database": {
                "recorded_sha256": queue.get("database_sha256"),
                "file": _recorded_file(bundle, queue.get("database_path")),
            },
        },
        # Informational only: the verifying machine's own configuration. Never
        # compared, because it is not evidence produced by the run.
        "context": {
            "configuration": dict(context_configuration or {}),
            "environ_keys": sorted(str(key) for key in (environ or {}) if str(key).startswith("WANGP_")),
        },
        "not_promised": list(NOT_PROMISED),
    }
    return redact_sensitive(recipe)


def _local_context_configuration(
    repository_root: Path,
    environ: Mapping[str, str] | None,
) -> dict[str, Any]:
    from wangp.config import load_host_config

    try:
        config = load_host_config(
            repository_root=repository_root,
            environ=environ if environ is not None else os.environ,
        )
    except Exception:  # configuration problems must never block a recipe
        return {}
    resolved: dict[str, Any] = {}
    for field in ("target", "wgp_root", "pull_root", "wgp_python"):
        setting = getattr(config, field, None)
        resolved[field] = {
            "value": getattr(setting, "value", None),
            "source": getattr(setting, "source", None),
        }
    return resolved


def write_recipe(recipe: Mapping[str, Any], path: str | Path) -> tuple[Path, str]:
    """Atomically write the canonical recipe; return its path and digest.

    Uses ``mkstemp`` in the destination directory, which creates the file with
    ``O_EXCL`` semantics and therefore cannot be redirected through a
    pre-created symlink at a predictable temp path.
    """
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical(recipe) + b"\n"
    handle, temporary_name = tempfile.mkstemp(
        dir=str(target.parent), prefix=f".{target.name}.", suffix=".tmp")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(payload)
        os.replace(temporary, target)
    except BaseException:
        with contextlib.suppress(OSError):
            temporary.unlink()
        raise
    return target, hashlib.sha256(payload).hexdigest()


def load_recipe(path: str | Path) -> dict[str, Any]:
    """Read a recipe, rejecting anything that is not this schema."""
    recipe_path = Path(path).expanduser().resolve()
    payload = _read_json(recipe_path)
    if not isinstance(payload, dict):
        raise RecipeError(f"recipe is not an object: {recipe_path}")
    if payload.get("schema_version") != RECIPE_SCHEMA:
        raise RecipeError(
            f"unsupported recipe schema {payload.get('schema_version')!r}; "
            f"expected {RECIPE_SCHEMA!r}")
    if not isinstance(payload.get("pinned"), dict):
        raise RecipeError(f"recipe has no 'pinned' mapping: {recipe_path}")
    return payload


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, Mapping):
        flat: dict[str, Any] = {}
        for key, item in value.items():
            flat.update(_flatten(item, f"{prefix}.{key}" if prefix else str(key)))
        return flat
    if isinstance(value, list):
        flat = {}
        for index, item in enumerate(value):
            flat.update(_flatten(item, f"{prefix}[{index}]"))
        return flat
    return {prefix: value}


def pinned_field_count(recipe: Mapping[str, Any]) -> int:
    """Number of scalar fields the recipe pins (for reporting)."""
    return len(_flatten(recipe.get("pinned") or {}))


_MISSING = object()


def _status(expected: Any, observed: Any) -> str:
    if expected is None or observed is _MISSING:
        # Nothing was recorded (or the run no longer records it): an absent value
        # never counts as agreement.
        return "missing"
    if expected == observed:
        return "unchanged"
    return "changed"


def diff_recipe(
    recipe: Mapping[str, Any],
    current: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Per-field drift between a recorded recipe and the current run state."""
    expected = _flatten(recipe.get("pinned") or {}, "pinned")
    observed = _flatten(current.get("pinned") or {}, "pinned")
    drift: list[dict[str, Any]] = []
    for field in sorted(expected):
        want = expected[field]
        got = observed.get(field, _MISSING)
        drift.append({
            "field": field,
            "status": _status(want, got),
            "expected": want,
            "observed": None if got is _MISSING else got,
        })
    for field in sorted(set(observed) - set(expected)):
        drift.append({
            "field": field,
            "status": "added",
            "expected": None,
            "observed": observed[field],
        })
    return drift


def verify_recipe(
    recipe_path: str | Path,
    run: str | Path,
    repository_root: str | Path,
) -> list[dict[str, Any]]:
    """Verify a run against its recipe; returns every non-unchanged field."""
    recipe = load_recipe(recipe_path)
    current = build_recipe(run, repository_root)
    return [entry for entry in diff_recipe(recipe, current)
            if entry["status"] != "unchanged"]
