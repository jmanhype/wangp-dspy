import json
import sqlite3

import pytest

from tests.lf003_fixtures import (
    MANIFEST_PATH, ROOT, FixtureVerificationError, stage_lf003_jobs_db,
    verify_lf003_fixtures,
)


def test_lf003_manifest_fails_closed_on_missing_fixture(tmp_path):
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    payload["artifacts"][0]["path"] = "datasets/missing-lf003-fixture.bin"
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(FixtureVerificationError, match="missing"):
        verify_lf003_fixtures(manifest_path=manifest)


def test_lf003_manifest_fails_closed_on_hash_mismatch(tmp_path):
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    payload["artifacts"][0]["sha256"] = "0" * 64
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(FixtureVerificationError, match="SHA-256 mismatch"):
        verify_lf003_fixtures(manifest_path=manifest)


def test_lf003_jobs_db_fixture_rebases_embedded_paths(tmp_path):
    fixtures = verify_lf003_fixtures()
    staged = stage_lf003_jobs_db(
        tmp_path / "staged-lf003.jobs.db", fixtures=fixtures)
    with sqlite3.connect(staged["jobs_db"]) as db:
        clips = db.execute(
            "SELECT clips FROM jobs WHERE job_id=?", (staged["job_id"],)
        ).fetchone()[0]
    assert fixtures.jobs_db_source_root + "/assets/" not in clips
    assert fixtures.jobs_db_source_root + "/datasets/" not in clips
    assert str(ROOT) in clips
