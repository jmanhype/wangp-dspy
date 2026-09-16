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
import hashlib
import stat
from pathlib import Path
from typing import Mapping, Optional


class RepositoryIdentityError(RuntimeError):
    """The run cannot be attributed to a concrete repository revision."""


def _git(repo_root: Path, *args: str, allow_empty: bool = False) -> str:
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
    if not value and not allow_empty:
        raise RepositoryIdentityError(
            f"git {' '.join(args)} returned no value for {repo_root}")
    return value


def _untracked_content_sha256(root: Path) -> str:
    """Hash untracked paths, types, modes, and bytes deterministically."""
    proc = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--others",
         "--exclude-standard", "-z"],
        capture_output=True, check=False)
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", "replace").strip()[:240]
        raise RepositoryIdentityError(
            f"git ls-files --others failed for {root}: {detail}")
    digest = hashlib.sha256()
    for raw_path in proc.stdout.split(b"\0"):
        if not raw_path:
            continue
        digest.update(len(raw_path).to_bytes(8, "big"))
        digest.update(raw_path)
        path = root / os.fsdecode(raw_path)
        try:
            mode = path.lstat().st_mode
        except OSError as exc:
            raise RepositoryIdentityError(
                f"unable to stat untracked path {path}: {exc}") from exc
        digest.update(f"mode={mode:o}".encode("ascii"))
        if stat.S_ISLNK(mode):
            try:
                target = os.readlink(path)
            except OSError as exc:
                raise RepositoryIdentityError(
                    f"unable to read untracked symlink {path}: {exc}") from exc
            encoded_target = os.fsencode(target)
            digest.update(len(encoded_target).to_bytes(8, "big"))
            digest.update(encoded_target)
        elif stat.S_ISREG(mode):
            try:
                flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                descriptor = os.open(path, flags)
            except OSError as exc:
                raise RepositoryIdentityError(
                    f"unable to hash untracked file {path}: {exc}") from exc
            try:
                before = os.fstat(descriptor)
                if not stat.S_ISREG(before.st_mode):
                    raise RepositoryIdentityError(
                        f"untracked path changed type while hashing: {path}")
                content_hash = hashlib.sha256()
                remaining = before.st_size
                while remaining:
                    chunk = os.read(
                        descriptor, min(1024 * 1024, remaining))
                    if not chunk:
                        raise RepositoryIdentityError(
                            "untracked file shrank while hashing: "
                            f"{path}")
                    content_hash.update(chunk)
                    remaining -= len(chunk)
                after = os.fstat(descriptor)
                stable = (
                    before.st_dev, before.st_ino, before.st_mode,
                    before.st_size, before.st_mtime_ns,
                ) == (
                    after.st_dev, after.st_ino, after.st_mode,
                    after.st_size, after.st_mtime_ns,
                )
                if not stable:
                    raise RepositoryIdentityError(
                        f"untracked file changed while hashing: {path}")
                payload = content_hash.digest()
                digest.update(f"size={before.st_size}:".encode("ascii"))
                digest.update(len(payload).to_bytes(8, "big"))
                digest.update(payload)
            finally:
                os.close(descriptor)
        elif stat.S_ISDIR(mode):
            raise RepositoryIdentityError(
                f"untracked embedded repository or opaque directory changes "
                f"are not safely hashable: {path}")
    return digest.hexdigest()


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
    status = _git(root, "status", "--porcelain=v1",
                  "--untracked-files=normal", allow_empty=True)
    tracked_diff = _git(root, "diff", "HEAD", "--full-index",
                        "--no-ext-diff", allow_empty=True)
    status_lines = [line for line in status.splitlines() if line.strip()]
    untracked_count = sum(line.startswith("?? ") for line in status_lines)
    status_sha = hashlib.sha256(status.encode("utf-8", "replace")).hexdigest()
    diff_sha = hashlib.sha256(
        tracked_diff.encode("utf-8", "replace")).hexdigest()
    return {
        "repo_root": str(root),
        "commit_sha": sha,
        "clean_tree": not bool(status_lines),
        "dirty_tree": bool(status_lines),
        "status_sha256": status_sha,
        "tracked_diff_sha256": diff_sha,
        "untracked_content_sha256": _untracked_content_sha256(root),
        "changed_path_count": len(status_lines),
        "untracked_path_count": untracked_count,
    }


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
    identity = dict(identity)
    identity["repo_root"] = root
    identity["commit_sha"] = sha
    optional_ints = ("changed_path_count", "untracked_path_count")
    optional_hashes = (
        "status_sha256", "tracked_diff_sha256", "untracked_content_sha256")
    for key in optional_ints:
        if key not in identity:
            continue
        value = identity.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise RepositoryIdentityError(
                f"repository {key} must be a non-negative integer")
        identity[key] = value
    for key in optional_hashes:
        if key not in identity:
            continue
        value = str(identity.get(key, "")).strip()
        if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise RepositoryIdentityError(
                f"repository {key} must be a lowercase SHA-256")
        identity[key] = value
    for key in ("clean_tree", "dirty_tree"):
        if key in identity:
            value = identity.get(key)
            if not isinstance(value, bool):
                raise RepositoryIdentityError(
                    f"repository {key} must be boolean")
            identity[key] = value
    return identity


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
