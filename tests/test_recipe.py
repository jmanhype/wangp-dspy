"""Real-process tests for ``wgp recipe write|verify`` against committed evidence."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921"


def wgp(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Invoke the real installed entry point, not an in-process import."""
    return subprocess.run(
        ["uv", "run", "--frozen", "--extra", "dev", "wgp", *args],
        cwd=ROOT, capture_output=True, text=True,
        env={**os.environ, **(env or {})},
    )


def _write_recipe(tmp_path: Path) -> Path:
    target = tmp_path / "recipe.json"
    result = wgp("recipe", "write", "--run", str(RUN), "--out", str(target))
    assert result.returncode == 0, result.stderr
    assert target.is_file()
    return target


def _mutate(recipe: dict, field: str, value: object) -> None:
    parts = field.split(".")
    node = recipe["pinned"]
    for part in parts[:-1]:
        node = node[part]
    node[parts[-1]] = value


def test_recipe_write_pins_the_logical_inputs(tmp_path: Path) -> None:
    target = _write_recipe(tmp_path)
    recipe = json.loads(target.read_text(encoding="utf-8"))
    assert recipe["schema_version"] == "wangp-dspy.render-recipe/v1"
    pinned = recipe["pinned"]
    provenance = json.loads((RUN / "final-provenance.json").read_text())
    assert pinned["plan"]["canonical_sha256"] == provenance["operator_approval"]["canonical_plan_sha256"]
    assert pinned["brief"]["raw_sha256"] == provenance["operator_approval"]["raw_brief_sha256"]
    assert pinned["media"]["assembled_sha256"] == provenance["final_media"]["sha256"]
    assert pinned["retry_policy"] == provenance["retry_policy"]
    assert pinned["model_and_settings_hashes"] == provenance["settings_hashes"]
    assert pinned["gate_thresholds"]["whisper_post_pass_bar"] is not None
    assert pinned["gate_thresholds"]["syncnet_model_sha256"]
    assert str(ROOT / "VERSION").strip() and pinned["repository_version"] == (
        ROOT / "VERSION").read_text().strip()
    assert len(recipe["not_promised"]) >= 2
    assert any("lossy" in entry for entry in recipe["not_promised"])


def test_recipe_verify_is_clean_for_the_committed_run(tmp_path: Path) -> None:
    target = _write_recipe(tmp_path)
    result = wgp("recipe", "verify", "--recipe", str(target), "--run", str(RUN))
    assert result.returncode == 0, result.stderr
    assert "drift=0" in result.stdout and "verified=true" in result.stdout


@pytest.mark.parametrize(
    "field,value",
    [
        ("plan.canonical_sha256", "0" * 64),
        ("configuration.wgp_root.value", "/nonexistent/root"),
        ("repository_version", "0.0.0-test"),
        ("retry_policy.DEFAULT_MAX_ATTEMPTS", 99),
        ("gate_thresholds.whisper_post_pass_bar", 0.99),
    ],
)
def test_recipe_detects_drift_per_field_class(tmp_path: Path, field: str, value: object) -> None:
    target = _write_recipe(tmp_path)
    recipe = json.loads(target.read_text(encoding="utf-8"))
    _mutate(recipe, field, value)
    mutated = tmp_path / "mutated.json"
    mutated.write_text(json.dumps(recipe, sort_keys=True), encoding="utf-8")
    result = wgp("recipe", "verify", "--recipe", str(mutated), "--run", str(RUN))
    assert result.returncode == 2, result.stdout + result.stderr
    assert f"drift field=pinned.{field} status=changed" in result.stdout
    assert "verified=false" in result.stdout


def test_recipe_detects_model_settings_drift(tmp_path: Path) -> None:
    target = _write_recipe(tmp_path)
    recipe = json.loads(target.read_text(encoding="utf-8"))
    key = sorted(recipe["pinned"]["model_and_settings_hashes"])[0]
    recipe["pinned"]["model_and_settings_hashes"][key] = "0" * 64
    mutated = tmp_path / "settings.json"
    mutated.write_text(json.dumps(recipe, sort_keys=True), encoding="utf-8")
    result = wgp("recipe", "verify", "--recipe", str(mutated), "--run", str(RUN))
    assert result.returncode == 2
    assert f"field=pinned.model_and_settings_hashes.{key} status=changed" in result.stdout


def test_missing_recipe_is_actionable(tmp_path: Path) -> None:
    missing = tmp_path / "absent.json"
    result = wgp("recipe", "verify", "--recipe", str(missing), "--run", str(RUN))
    assert result.returncode == 2
    assert "missing" in (result.stdout + result.stderr)
    assert "wgp recipe write" in (result.stdout + result.stderr)


def test_tampered_recipe_is_rejected(tmp_path: Path) -> None:
    target = _write_recipe(tmp_path)
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert wgp("recipe", "verify", "--recipe", str(broken), "--run", str(RUN)).returncode == 2

    recipe = json.loads(target.read_text(encoding="utf-8"))
    recipe["schema_version"] = "wangp-dspy.render-recipe/v0"
    wrong = tmp_path / "wrong-schema.json"
    wrong.write_text(json.dumps(recipe), encoding="utf-8")
    result = wgp("recipe", "verify", "--recipe", str(wrong), "--run", str(RUN))
    assert result.returncode == 2
    assert "unsupported recipe schema" in (result.stdout + result.stderr)


def test_recipe_write_verify_make_no_host_call_and_leave_the_run_untouched(
    tmp_path: Path,
) -> None:
    """The recipe verbs are local and read-only: no ssh, no new files in the run."""
    ssh_dir = tmp_path / "bin"
    ssh_dir.mkdir()
    ssh_log = tmp_path / "ssh.log"
    fake = ssh_dir / "ssh"
    fake.write_text(f"#!/bin/sh\necho \"$@\" >> {ssh_log}\nexit 255\n", encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)

    before = sorted(path.name for path in RUN.iterdir())
    target = _write_recipe(tmp_path)
    assert wgp(
        "recipe", "verify", "--recipe", str(target), "--run", str(RUN),
        env={"PATH": f"{ssh_dir}:{os.environ['PATH']}"},
    ).returncode == 0
    assert not ssh_log.exists()
    assert sorted(path.name for path in RUN.iterdir()) == before
    assert not list(RUN.glob("*.tmp-*"))
