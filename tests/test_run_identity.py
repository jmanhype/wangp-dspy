"""Finding 0: every film run records its repository identity."""
from __future__ import annotations

import json

import pytest


def test_repository_identity_resolves_repo_root_and_head():
    from services.director.run_ledger import repository_identity

    identity = repository_identity()
    assert identity["repo_root"] == "/Users/Shared/HermesWorkspace/wangp-dspy"
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
