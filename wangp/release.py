"""Read-only release readiness verification from committed evidence."""

from __future__ import annotations

import re
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from services.director.run_ledger import (
    RepositoryIdentityError, repository_identity)
from wangp import __version__
from wangp.diagnostics import redact_sensitive
from wangp.recipe import RECIPE_SCHEMA, RecipeError, build_recipe

ACCEPTED_RECIPE_SCHEMA = "wangp-dspy.render-recipe/v3"
RECIPE_EVIDENCE_RUN = Path("datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921")


class ReleaseError(ValueError):
    """A typed release-readiness or release-input failure."""

    def __init__(self, message: str,
                 verification: "ReleaseVerification | None" = None) -> None:
        super().__init__(message)
        self.verification = verification


@dataclass(frozen=True)
class ReleaseCheck:
    """One stable release-readiness observation."""

    name: str
    status: str
    expected: Any
    observed: Any
    source: str
    message: str | None = None

@dataclass(frozen=True)
class ReleaseVerification:
    """The complete, secret-free release-readiness verdict."""

    version: str
    ready: bool
    tag: str
    checks: tuple[ReleaseCheck, ...]
    tag_created: bool = False
    guidance: str = "no tag was created"

    def mapping(self) -> dict[str, Any]:
        return redact_sensitive(asdict(self))


def _failed(checks: list[ReleaseCheck], version: str) -> ReleaseError:
    failures = [check for check in checks if check.status != "pass"]
    detail = "; ".join(check.message or check.name for check in failures)
    verification = ReleaseVerification(
        version, False, f"v{version}", tuple(checks),
        guidance=f"resolve failed checks before tagging v{version}; no tag was created")
    return ReleaseError(detail, verification)


def _version_check(root: Path) -> tuple[ReleaseCheck, str]:
    version_path = root / "VERSION"
    pyproject_path = root / "pyproject.toml"
    try:
        repository_version = version_path.read_text(encoding="utf-8").strip()
        metadata = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        project = metadata.get("project")
        if not isinstance(project, Mapping):
            raise ReleaseError(f"version: {pyproject_path} has no [project] mapping")
        package_version = project.get("version")
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise ReleaseError(
            f"version: cannot read release version sources: {exc}") from exc

    observed = {"VERSION": repository_version, "pyproject.toml": package_version,
                "wangp.__version__": __version__}
    passed = (repository_version == package_version == __version__
              and bool(repository_version))
    message = None if passed else "version sources disagree: " + ", ".join(
        f"{name}={value!r}" for name, value in observed.items())
    current = str(package_version or repository_version or __version__)
    return ReleaseCheck("version", "pass" if passed else "failed", current,
                        observed, "VERSION, pyproject.toml, wangp/__init__.py",
                        message), current


def _changelog_check(root: Path, version: str) -> ReleaseCheck:
    changelog_path = root / "CHANGELOG.md"
    try:
        changelog = changelog_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ReleaseError(f"changelog: cannot read {changelog_path}: {exc}") from exc
    pattern = rf"(?m)^## \[{re.escape(version)}\](?:\s|$)"
    found = re.search(pattern, changelog) is not None
    return ReleaseCheck(
        "changelog", "pass" if found else "failed", version,
        version if found else None, "CHANGELOG.md", None if found else
        f"changelog has no root '## [{version}]' entry for the current version")


def _recipe_check(root: Path, version: str) -> ReleaseCheck:
    evidence = root / RECIPE_EVIDENCE_RUN
    try:
        recipe = build_recipe(evidence, root, context_configuration={},
                              environ={})
    except (RecipeError, OSError, UnicodeError) as exc:
        artifact = getattr(exc, "filename", None) or evidence
        if isinstance(exc, (OSError, UnicodeError)):
            message = (f"recipe_schema: cannot read committed recipe artifact "
                       f"{artifact}: {exc}")
        else:
            message = f"recipe_schema: committed recipe evidence failed: {exc}"
        check = ReleaseCheck(
            "recipe_schema", "failed", ACCEPTED_RECIPE_SCHEMA,
            {"artifact": str(artifact), "error": str(exc)},
            "wangp/recipe.py, datasets/runs/pull/"
            "lf004-operator-dogfood-56f-recovery-20260921", message)
        verification = ReleaseVerification(
            version, False, f"v{version}", (check,),
            guidance=f"resolve failed checks before tagging v{version}; "
                     "no tag was created")
        raise ReleaseError(message, verification) from exc
    observed = recipe.get("schema_version")
    passed = observed == ACCEPTED_RECIPE_SCHEMA and observed == RECIPE_SCHEMA
    return ReleaseCheck(
        "recipe_schema", "pass" if passed else "failed", ACCEPTED_RECIPE_SCHEMA,
        observed, "wangp/recipe.py, datasets/runs/pull/"
        "lf004-operator-dogfood-56f-recovery-20260921", None if passed else
        f"unsupported recipe schema {observed!r}; expected {ACCEPTED_RECIPE_SCHEMA!r}")


def _tree_check(root: Path) -> ReleaseCheck:
    identity = repository_identity(root)
    keys = ("commit_sha", "clean_tree", "dirty_tree", "changed_path_count",
            "untracked_path_count", "status_sha256", "tracked_diff_sha256",
            "untracked_content_sha256")
    observed = {key: identity.get(key) for key in keys}
    clean = (observed["clean_tree"] is True and observed["dirty_tree"] is False
             and observed["changed_path_count"] == 0
             and observed["untracked_path_count"] == 0)
    return ReleaseCheck(
        "tree", "pass" if clean else "failed",
        "clean_tree=true changed_path_count=0 untracked_path_count=0", observed,
        "services.director.run_ledger.repository_identity", None if clean else
        f"tree is dirty: changed_path_count={observed['changed_path_count']!r}, "
        f"untracked_path_count={observed['untracked_path_count']!r}")


def verify_release(repository_root: Path) -> ReleaseVerification:
    """Verify release readiness without creating a Git object or artifact."""

    root = Path(repository_root).expanduser().resolve()
    if not root.is_dir():
        raise ReleaseError(f"repository root does not exist: {root}")

    version_check, version = _version_check(root)
    checks = [version_check, _changelog_check(root, version),
              _recipe_check(root, version)]
    try:
        checks.append(_tree_check(root))
    except RepositoryIdentityError as exc:
        checks.append(ReleaseCheck(
            "tree", "failed", "clean_tree=true", {"error": str(exc)},
            "services.director.run_ledger.repository_identity",
            f"repository identity failed closed: {exc}"))
        raise _failed(checks, version) from exc
    if any(check.status != "pass" for check in checks):
        raise _failed(checks, version)
    return ReleaseVerification(version, True, f"v{version}", tuple(checks),
                               guidance=f"v{version} is tag-ready; no tag was created")
