"""Versioned render recipe: pin a run's logical inputs and detect drift.

The recipe records what a finished run *was*: the repository version, the brief
and plan identities, the resolved configuration, the model/settings hashes the
run recorded, the retry policy, the gate thresholds in force, and the media
hashes. Verifying a run against its recipe reports per-field drift so a reader
can tell whether the artifact in front of them is the one the recipe describes.

What it deliberately does not promise: a generative render is lossy, so an
identical recipe may still produce different pixels on a re-render (different
seed, model build, or host environment). That limit is recorded in the manifest
itself rather than implied away.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from wangp.config import HostConfig, load_host_config
from wangp.diagnostics import redact_sensitive

RECIPE_SCHEMA = "wangp-dspy.render-recipe/v1"
_CONFIG_FIELDS = ("target", "wgp_root", "pull_root", "wgp_python")
NOT_PROMISED = (
    "byte-identical pixels: a generative render is lossy, so the same recipe may "
    "produce different pixels when re-rendered with a different seed, model "
    "build, or host environment.",
    "anything the run did not record: an input absent from the run's provenance "
    "cannot be pinned by this recipe and is reported as missing rather than assumed.",
)


class RecipeError(ValueError):
    """A recipe could not be built, read, or verified."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(payload), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, default=str,
    ).encode("utf-8")


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
    if not (bundle / "final-provenance.json").is_file():
        raise RecipeError(
            f"final-provenance.json is missing: {bundle / 'final-provenance.json'}")
    return bundle


def _gate_thresholds(provenance: Mapping[str, Any]) -> dict[str, Any]:
    """Collect the declared pass bars and model identity from per-cut evidence."""
    thresholds: dict[str, Any] = {}
    for cut in provenance.get("cuts") or []:
        whisper = cut.get("whisper") or {}
        for phase in ("pre", "post"):
            bar = (whisper.get(phase) or {}).get("pass_bar")
            if bar is not None:
                thresholds.setdefault(f"whisper_{phase}_pass_bar", bar)
        vision = cut.get("vision") or {}
        if vision.get("pass_bar") is not None:
            thresholds.setdefault("vision_pass_bar", vision["pass_bar"])
        av_sync = cut.get("av_sync") or {}
        if av_sync.get("model_sha256"):
            thresholds.setdefault("syncnet_model_sha256", av_sync["model_sha256"])
        av_bar = av_sync.get("pass_bar")
        if isinstance(av_bar, dict):
            for name, value in av_bar.items():
                thresholds.setdefault(f"syncnet_{name}", value)
    return thresholds


def _cut_media_hashes(provenance: Mapping[str, Any]) -> list[dict[str, Any]]:
    hashes: list[dict[str, Any]] = []
    for cut in provenance.get("cuts") or []:
        av_sync = cut.get("av_sync") or {}
        hashes.append({
            "clip_index": cut.get("clip_index"),
            "video_sha256": av_sync.get("video_sha256"),
        })
    return hashes


def _configuration(config: HostConfig) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for field in _CONFIG_FIELDS:
        setting = getattr(config, field, None)
        resolved[field] = {
            "value": getattr(setting, "value", None),
            "source": getattr(setting, "source", None),
        }
    return resolved


def build_recipe(
    run: str | Path,
    repository_root: str | Path,
    *,
    config: HostConfig | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build the canonical recipe manifest for one finished run."""
    bundle = _run_bundle(run)
    root = Path(repository_root).expanduser().resolve()
    provenance = _read_json(bundle / "final-provenance.json")
    if not isinstance(provenance, dict):
        raise RecipeError(f"final provenance is not an object: {bundle}")
    inputs = provenance.get("inputs") or {}
    approval = provenance.get("operator_approval") or {}
    reconciliation = provenance.get("reconciliation") or {}
    media = provenance.get("final_media") or {}
    queue = provenance.get("queue_evidence") or {}
    version_path = root / "VERSION"
    repository_version = (
        version_path.read_text(encoding="utf-8").strip()
        if version_path.is_file() else None
    )
    resolved_host = config if config is not None else load_host_config(
        repository_root=root,
        environ=environ if environ is not None else os.environ,
    )
    recipe = {
        "schema_version": RECIPE_SCHEMA,
        "run_id": provenance.get("run_id") or bundle.name,
        "pinned": {
            "repository_version": repository_version,
            "plan": {
                "canonical_sha256": (
                    approval.get("canonical_plan_sha256")
                    or reconciliation.get("canonical_plan_sha256")),
                "raw_plan_sha256": inputs.get("plan_sha256"),
            },
            "brief": {
                "semantic_hash": approval.get("brief_hash"),
                "raw_sha256": (
                    approval.get("raw_brief_sha256") or inputs.get("brief_sha256")),
            },
            "configuration": _configuration(resolved_host),
            "model_and_settings_hashes": dict(provenance.get("settings_hashes") or {}),
            "retry_policy": dict(provenance.get("retry_policy") or {}),
            "gate_thresholds": _gate_thresholds(provenance),
            "media": {
                "assembled_sha256": media.get("sha256"),
                "cuts": _cut_media_hashes(provenance),
            },
            "queue_database_sha256": queue.get("database_sha256"),
        },
        "not_promised": list(NOT_PROMISED),
    }
    return redact_sensitive(recipe)


def write_recipe(recipe: Mapping[str, Any], path: str | Path) -> tuple[Path, str]:
    """Atomically write the canonical recipe; return its path and digest."""
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical(recipe) + b"\n"
    temporary = target.with_suffix(target.suffix + f".tmp-{os.getpid()}")
    temporary.write_bytes(payload)
    os.replace(temporary, target)
    return target, _sha256_bytes(payload)


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
    return {prefix: value}


def pinned_field_count(recipe: Mapping[str, Any]) -> int:
    """Number of scalar fields the recipe pins (for reporting)."""
    return len(_flatten(recipe.get("pinned") or {}))


_MISSING = object()


def diff_recipe(
    recipe: Mapping[str, Any],
    current: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Per-field drift between a recorded recipe and a freshly built one."""
    expected = _flatten(recipe.get("pinned") or {}, "pinned")
    observed = _flatten(current.get("pinned") or {}, "pinned")
    drift: list[dict[str, Any]] = []
    for field in sorted(expected):
        want = expected[field]
        got = observed.get(field, _MISSING)
        if got is _MISSING:
            status = "missing"
        elif want == got:
            status = "unchanged"
        else:
            status = "changed"
        drift.append({
            "field": field,
            "status": status,
            "expected": None if want is _MISSING else want,
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
    *,
    config: HostConfig | None = None,
    environ: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Verify a run against its recipe; returns every non-unchanged field."""
    recipe = load_recipe(recipe_path)
    current = build_recipe(
        run, repository_root, config=config, environ=environ)
    return [entry for entry in diff_recipe(recipe, current)
            if entry["status"] != "unchanged"]
