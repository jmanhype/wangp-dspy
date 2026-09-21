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

RECIPE_SCHEMA = "wangp-dspy.render-recipe/v3"
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
        for section in ("whisper", "vision", "av_sync", "media", "gates"):
            value = cut.get(section)
            if value is not None and not isinstance(value, Mapping):
                raise RecipeError(
                    f"final provenance cut {index} field {section!r} is not an object")
        whisper = cut.get("whisper")
        if isinstance(whisper, Mapping):
            for phase in ("pre", "post"):
                value = whisper.get(phase)
                if value is not None and not isinstance(value, Mapping):
                    raise RecipeError(
                        f"final provenance cut {index} whisper {phase!r} is not "
                        f"an object")
        av_sync = cut.get("av_sync")
        if isinstance(av_sync, Mapping):
            bar = av_sync.get("pass_bar")
            if bar is not None and not isinstance(bar, Mapping):
                raise RecipeError(
                    f"final provenance cut {index} field 'av_sync.pass_bar' is "
                    f"not an object")
    for name in (
        "inputs", "operator_approval", "final_media", "queue_evidence",
        "settings_hashes", "retry_policy", "reconciliation",
    ):
        value = payload.get(name)
        if value is not None and not isinstance(value, Mapping):
            raise RecipeError(f"final provenance field {name!r} is not an object")
    return payload


def _mapping_section(
    payload: Mapping[str, Any], name: str, *, where: str = "final provenance"
) -> Mapping[str, Any]:
    """A provenance section that must be a mapping when present."""
    value = payload.get(name)
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise RecipeError(f"{where} field {name!r} is not an object")
    return value


def _repository_tail(raw_path: str) -> Path | None:
    """The repository-relative tail of a recorded path, if it has one."""
    parts = Path(raw_path).parts
    for marker in ("datasets", "renders"):
        if marker in parts:
            return Path(*parts[parts.index(marker):])
    return None


def _pin_path(
    bundle: Path,
    repository_root: Path,
    raw_path: Any,
    *,
    label: str,
    run_directory: str | None = None,
) -> tuple[str, str]:
    """Pin one required artifact; return (stored relative path, live sha256).

    Stored paths are never absolute: an artifact owned by the run directory is
    stored bundle-relative, anything else repository-relative. That keeps two
    copies of the same run byte-identical.

    An artifact the run recorded as living in its own directory is read from the
    bundle under review and nowhere else: a missing in-bundle artifact is a typed
    failure, never a silent substitution of the same name from another checkout.
    Artifacts recorded elsewhere (queue database, per-cut acceptance media) are
    read from this repository, which is the authorized evidence root.
    """
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise RecipeError(f"{label}: the run did not record an artifact path")
    recorded = Path(raw_path)
    if recorded.is_absolute():
        if run_directory is not None and recorded.parent.name == run_directory:
            target = bundle / recorded.name
            if not target.is_file():
                raise RecipeError(
                    f"{label}: required artifact is missing from this run review "
                    f"bundle: {recorded.name}")
            return recorded.name, _sha256_file(target)
        tail = _repository_tail(raw_path)
        if tail is None:
            raise RecipeError(
                f"{label}: recorded path is outside the repository and cannot be "
                f"pinned portably: {raw_path}")
        target = repository_root / tail
        if not target.is_file():
            raise RecipeError(
                f"{label}: required artifact is missing from this checkout: "
                f"{tail.as_posix()}")
        return tail.as_posix(), _sha256_file(target)
    for candidate_root in (bundle, repository_root):
        target = candidate_root / recorded
        if target.is_file():
            return recorded.as_posix(), _sha256_file(target)
    raise RecipeError(f"{label}: required artifact is missing: {raw_path}")


def _run_directory_name(media: Mapping[str, Any]) -> str | None:
    """Basename of the run's own directory, as the run recorded it."""
    path = media.get("path")
    if not isinstance(path, str) or not path.strip():
        return None
    return Path(path).parent.name or None


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


def _cut_media(
    bundle: Path,
    repository_root: Path,
    cut: Mapping[str, Any],
    run_directory: str | None,
) -> dict[str, Any]:
    av_sync = cut.get("av_sync") or {}
    clip_index = cut.get("clip_index")
    stored, live = _pin_path(
        bundle, repository_root, av_sync.get("video_path"),
        label=f"cut {clip_index} video", run_directory=run_directory)
    return {
        "clip_index": clip_index,
        "recorded_video_sha256": av_sync.get("video_sha256"),
        "path": stored,
        "sha256": live,
    }


def _plan_hashes(provenance: Mapping[str, Any]) -> dict[str, Any]:
    """Canonical and raw plan identity, including path-keyed older formats."""
    approval = _mapping_section(provenance, "operator_approval")
    reconciliation = _mapping_section(provenance, "reconciliation")
    inputs = _mapping_section(provenance, "inputs")
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
    inputs = _mapping_section(provenance, "inputs")
    approval = _mapping_section(provenance, "operator_approval")
    media = _mapping_section(provenance, "final_media")
    queue = _mapping_section(provenance, "queue_evidence")
    settings = _mapping_section(provenance, "settings_hashes")
    retry_policy = _mapping_section(provenance, "retry_policy")
    run_directory = _run_directory_name(media)
    assembled_path, assembled_hash = _pin_path(
        bundle, root, media.get("path"), label="assembled media",
        run_directory=run_directory)
    queue_path, queue_hash = _pin_path(
        bundle, root, queue.get("database_path"), label="queue database")
    version_path = root / "VERSION"
    repository_version = (
        version_path.read_text(encoding="utf-8").strip()
        if version_path.is_file() else None
    )
    recorded_settings = {str(name): str(digest) for name, digest in settings.items()}
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
                "path": assembled_path,
                "sha256": assembled_hash,
            },
            "cuts": [
                _cut_media(bundle, root, cut, run_directory)
                for cut in provenance.get("cuts") or []
            ],
            "cut_gate_thresholds": [
                _cut_gate_thresholds(cut) for cut in provenance.get("cuts") or []
            ],
            "recorded_settings_hashes": recorded_settings,
            "retry_policy": dict(retry_policy),
            "queue_database": {
                "recorded_sha256": queue.get("database_sha256"),
                "path": queue_path,
                "sha256": queue_hash,
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
