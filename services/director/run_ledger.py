"""Repository identity and run-ledger primitives.

Finding 0 closes the shared-checkout hazard: a run must carry the exact
repository root and commit that produced its plan/jobs.  This module is
stdlib-only and deliberately fails closed when the requested path is not a
Git checkout or when Git returns an ambiguous result.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Mapping, Optional


class RepositoryIdentityError(RuntimeError):
    """The run cannot be attributed to a concrete repository revision."""


def _git(repo_root: Path, *args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise RepositoryIdentityError(
            f"unable to invoke git for repository {repo_root}: {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()[:240]
        raise RepositoryIdentityError(
            f"git {' '.join(args)} failed for {repo_root}: {detail}")
    value = proc.stdout.strip()
    if not value:
        raise RepositoryIdentityError(
            f"git {' '.join(args)} returned no value for {repo_root}")
    return value


def repository_identity(repo_root: Optional[os.PathLike[str] | str] = None) -> dict:
    """Return the canonical absolute root and current HEAD SHA.

    ``repo_root`` defaults to this package's checkout.  Both values are
    resolved by Git rather than inferred from the process cwd, preventing a
    second checkout from silently becoming the run source.
    """
    requested = (Path(repo_root).expanduser().resolve()
                 if repo_root is not None
                 else Path(__file__).resolve().parents[2])
    root = Path(_git(requested, "rev-parse", "--show-toplevel")).resolve()
    sha = _git(root, "rev-parse", "HEAD")
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        raise RepositoryIdentityError(
            f"git HEAD is not a lowercase 40-character SHA: {sha!r}")
    return {"repo_root": str(root), "commit_sha": sha}


def _validate_identity(identity: Mapping[str, str]) -> dict:
    if not isinstance(identity, Mapping):
        raise RepositoryIdentityError("repository identity must be a mapping")
    root = str(identity.get("repo_root", "")).strip()
    sha = str(identity.get("commit_sha", "")).strip()
    if not root or not Path(root).is_absolute():
        raise RepositoryIdentityError("repository repo_root must be absolute")
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        raise RepositoryIdentityError(
            "repository commit_sha must be a lowercase 40-character SHA")
    return {"repo_root": root, "commit_sha": sha}


def write_run_ledger(
    path: os.PathLike[str] | str,
    *,
    run_id: str,
    identity: Mapping[str, str],
    status: str = "planned",
    extra: Optional[Mapping[str, object]] = None,
) -> Path:
    """Atomically write a run ledger containing repository identity.

    The file is intentionally a single JSON document: later run stages can
    append evidence fields while the immutable ``repository`` object remains
    the source-attribution anchor.
    """
    if not str(run_id).strip():
        raise ValueError("run_id must be nonempty")
    if not str(status).strip():
        raise ValueError("status must be nonempty")
    payload = {
        "schema_version": 1,
        "run_id": str(run_id),
        "status": str(status),
        "repository": _validate_identity(identity),
    }
    if extra:
        payload.update(dict(extra))
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(target.parent), prefix=f".{target.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, target)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return target


__all__ = [
    "RepositoryIdentityError",
    "repository_identity",
    "write_run_ledger",
]
