"""Finding 0: every film run records its repository identity."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


def _git(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def test_repository_identity_resolves_repo_root_and_head():
    from services.director import run_ledger
    from services.director.run_ledger import repository_identity

    checkout_root = Path(run_ledger.__file__).resolve().parents[2]
    expected_root = Path(
        _git(checkout_root, "rev-parse", "--show-toplevel")
    ).resolve()
    expected_head = _git(expected_root, "rev-parse", "HEAD")

    identity = repository_identity()
    assert identity["repo_root"] == str(expected_root)
    assert identity["commit_sha"] == expected_head
    assert len(identity["commit_sha"]) == 40
    assert all(c in "0123456789abcdef" for c in identity["commit_sha"])


def test_repository_identity_default_ignores_cwd(monkeypatch, tmp_path):
    from services.director.run_ledger import repository_identity

    expected_identity = repository_identity()
    monkeypatch.chdir(tmp_path)

    assert repository_identity() == expected_identity


def test_repository_identity_resolves_explicit_other_checkout(tmp_path):
    from services.director.run_ledger import repository_identity

    source_root = Path(
        _git(Path(__file__).resolve().parents[1], "rev-parse", "--show-toplevel")
    ).resolve()
    source_head = _git(source_root, "rev-parse", "HEAD")
    clone_root = (tmp_path / "other-checkout").resolve()
    subprocess.run(
        [
            "git",
            "clone",
            "--no-hardlinks",
            "--quiet",
            str(source_root),
            str(clone_root),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    identity = repository_identity(clone_root)

    assert identity["repo_root"] == str(clone_root)
    assert identity["commit_sha"] == source_head
    assert len(identity["commit_sha"]) == 40
    assert all(c in "0123456789abcdef" for c in identity["commit_sha"])


def test_write_run_ledger_records_identity_atomically(tmp_path):
    from services.director.run_ledger import write_run_ledger

    path = write_run_ledger(
        tmp_path / "run_ledger.json",
        run_id="run-test",
        identity={"repo_root": "/repo", "commit_sha": "a" * 40},
        status="planned",
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "run-test"
    assert payload["status"] == "planned"
    assert payload["repository"] == {
        "repo_root": "/repo", "commit_sha": "a" * 40}
    assert not list(tmp_path.glob("*.tmp"))


def test_repository_identity_fails_closed_outside_git(tmp_path):
    from services.director.run_ledger import RepositoryIdentityError, repository_identity

    with pytest.raises(RepositoryIdentityError):
        repository_identity(tmp_path)
