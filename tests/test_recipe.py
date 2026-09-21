"""Real-process tests for ``wgp recipe write|verify`` against committed evidence.

Verification is only useful if it re-reads the world. These tests therefore
tamper with real bytes -- media, provenance, and recipe copies -- rather than
only with the manifest under comparison.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921"
SCHEMA = "wangp-dspy.render-recipe/v2"


def wgp(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Invoke the real installed entry point, not an in-process import."""
    return subprocess.run(
        ["uv", "run", "--frozen", "--extra", "dev", "wgp", *args],
        cwd=ROOT, capture_output=True, text=True,
        env={**os.environ, **(env or {})},
    )


def _copy_run(tmp_path: Path, name: str = "run") -> Path:
    bundle = tmp_path / name
    shutil.copytree(RUN, bundle)
    return bundle


def _provenance(bundle: Path) -> dict:
    return json.loads((bundle / "final-provenance.json").read_text(encoding="utf-8"))


def _write_provenance(bundle: Path, payload: dict) -> None:
    (bundle / "final-provenance.json").write_text(
        json.dumps(payload, sort_keys=True), encoding="utf-8")


def _write_recipe(tmp_path: Path, run: Path = RUN, name: str = "recipe.json") -> Path:
    target = tmp_path / name
    result = wgp("recipe", "write", "--run", str(run), "--out", str(target))
    assert result.returncode == 0, result.stderr
    return target


def _verify(recipe: Path, run: Path = RUN, env: dict[str, str] | None = None):
    return wgp("recipe", "verify", "--recipe", str(recipe), "--run", str(run), env=env)


def _mutate(recipe: dict, field: str, value: object) -> None:
    parts = field.split(".")
    node = recipe["pinned"]
    for part in parts[:-1]:
        node = node[part]
    node[parts[-1]] = value


def test_recipe_write_pins_real_provenance_values(tmp_path: Path) -> None:
    recipe = json.loads(_write_recipe(tmp_path).read_text(encoding="utf-8"))
    provenance = _provenance(RUN)
    pinned = recipe["pinned"]
    assert recipe["schema_version"] == SCHEMA
    assert pinned["run_id"] == provenance["run_id"]
    assert pinned["plan"]["canonical_sha256"] == provenance["operator_approval"]["canonical_plan_sha256"]
    assert pinned["plan"]["raw_plan_sha256"] == provenance["inputs"]["plan_sha256"]
    assert pinned["brief"]["raw_sha256"] == provenance["inputs"]["brief_sha256"]
    assert pinned["assembled_media"]["recorded_sha256"] == provenance["final_media"]["sha256"]
    if "file" in pinned["assembled_media"]:
        # Artifact present in this checkout: it is pinned by live hash.
        assert pinned["assembled_media"]["file"]["sha256"] == provenance["final_media"]["sha256"]
    else:
        # Artifact absent (for example a CI checkout without render media): it is
        # recorded as explicitly unavailable rather than pinned as a null.
        labels = {entry["label"] for entry in pinned["unavailable_artifacts"]}
        assert "assembled_media" in labels
    assert pinned["retry_policy"] == provenance["retry_policy"]
    assert pinned["recorded_settings_hashes"] == provenance["settings_hashes"]
    assert pinned["repository_version"] == (ROOT / "VERSION").read_text().strip()
    assert len(pinned["cut_gate_thresholds"]) == len(provenance["cuts"])
    assert pinned["cut_gate_thresholds"][3]["whisper_post_pass_bar"] == (
        provenance["cuts"][3]["whisper"]["post"]["pass_bar"])
    assert any("lossy" in entry for entry in recipe["not_promised"])


def test_clean_recipe_verifies_with_no_drift(tmp_path: Path) -> None:
    result = _verify(_write_recipe(tmp_path))
    assert result.returncode == 0, result.stderr
    assert "drift=0" in result.stdout and "verified=true" in result.stdout


def test_modified_media_is_detected(tmp_path: Path) -> None:
    """The reviewer's headline case: appended bytes must not verify clean."""
    recipe = _write_recipe(tmp_path)
    bundle = _copy_run(tmp_path)
    media = bundle / "assembled.mp4"
    media.write_bytes(media.read_bytes() + b"\x00")
    result = _verify(recipe, bundle)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "pinned.assembled_media.file.sha256 status=changed" in result.stdout


@pytest.mark.parametrize(
    "field,value",
    [
        ("plan.canonical_sha256", "0" * 64),
        ("repository_version", "0.0.0-test"),
        ("retry_policy.DEFAULT_MAX_ATTEMPTS", 99),
        ("run_id", "a-different-run"),
    ],
)
def test_recipe_detects_drift_per_field_class(
    tmp_path: Path, field: str, value: object
) -> None:
    target = _write_recipe(tmp_path)
    recipe = json.loads(target.read_text(encoding="utf-8"))
    _mutate(recipe, field, value)
    mutated = tmp_path / "mutated.json"
    mutated.write_text(json.dumps(recipe, sort_keys=True), encoding="utf-8")
    result = _verify(mutated)
    assert result.returncode == 2, result.stdout + result.stderr
    assert f"drift field=pinned.{field} status=changed" in result.stdout


def test_later_cut_threshold_change_is_detected(tmp_path: Path) -> None:
    """A change confined to the last cut must not be masked by earlier cuts."""
    recipe = _write_recipe(tmp_path)
    bundle = _copy_run(tmp_path)
    payload = _provenance(bundle)
    payload["cuts"][3]["whisper"]["post"]["pass_bar"] = 0.99
    _write_provenance(bundle, payload)
    result = _verify(recipe, bundle)
    assert result.returncode == 2
    assert "pinned.cut_gate_thresholds[3].whisper_post_pass_bar status=changed" in result.stdout


def test_unrecorded_evidence_reports_missing_not_clean(tmp_path: Path) -> None:
    bundle = _copy_run(tmp_path)
    payload = _provenance(bundle)
    payload["final_media"].pop("sha256", None)
    _write_provenance(bundle, payload)
    recipe = _write_recipe(tmp_path, bundle)
    written = json.loads(recipe.read_text(encoding="utf-8"))
    assert written["pinned"]["assembled_media"]["recorded_sha256"] is None
    result = _verify(recipe, bundle)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "pinned.assembled_media.recorded_sha256 status=missing" in result.stdout


def test_verifying_machine_configuration_is_context_only(tmp_path: Path) -> None:
    """Host config of the verifying checkout must never manufacture drift."""
    recipe = _write_recipe(tmp_path)
    written = json.loads(recipe.read_text(encoding="utf-8"))
    assert "configuration" in written["context"]
    assert "configuration" not in written["pinned"]
    result = _verify(recipe, env={
        "WANGP_SSH_TARGET": "some-other-host",
        "WANGP_WGP_ROOT": "/tmp/other-root",
        "WANGP_WGP_PYTHON": "/tmp/other/venv/bin/python",
        "WANGP_PULL_ROOT": str(tmp_path / "other-pull"),
    })
    assert result.returncode == 0, result.stdout + result.stderr
    assert "drift=0" in result.stdout


def test_path_keyed_plan_hash_is_resolved(tmp_path: Path) -> None:
    """Older runs key the plan hash by path instead of a named field."""
    bundle = _copy_run(tmp_path)
    payload = _provenance(bundle)
    digest = payload["inputs"].pop("plan_sha256")
    payload["inputs"]["datasets/content_briefs/lf004-operator-dogfood-56f/plan.json"] = digest
    _write_provenance(bundle, payload)
    recipe = json.loads(_write_recipe(tmp_path, bundle).read_text(encoding="utf-8"))
    assert recipe["pinned"]["plan"]["raw_plan_sha256"] == digest


def test_malformed_run_evidence_is_a_typed_input_error(tmp_path: Path) -> None:
    bundle = _copy_run(tmp_path)
    payload = _provenance(bundle)
    payload["cuts"] = [None]
    _write_provenance(bundle, payload)
    result = wgp("recipe", "write", "--run", str(bundle), "--out", str(tmp_path / "r.json"))
    assert result.returncode == 2, result.stdout + result.stderr
    assert "not an object" in (result.stdout + result.stderr)


def test_write_is_symlink_safe(tmp_path: Path) -> None:
    """A pre-created temp path must not be usable to overwrite another file."""
    victim = tmp_path / "victim.txt"
    victim.write_text("original contents", encoding="utf-8")
    target = tmp_path / "recipe.json"
    predictable = Path(f"{target}.tmp-{os.getpid()}")
    predictable.symlink_to(victim)
    recipe = json.loads(_write_recipe(tmp_path, name="source.json").read_text(encoding="utf-8"))
    result = wgp("recipe", "write", "--run", str(RUN), "--out", str(target))
    assert result.returncode == 0, result.stderr
    assert victim.read_text(encoding="utf-8") == "original contents"
    assert json.loads(target.read_text(encoding="utf-8"))["schema_version"] == SCHEMA
    assert recipe["schema_version"] == SCHEMA


def test_missing_and_tampered_recipes_are_rejected(tmp_path: Path) -> None:
    missing = wgp("recipe", "verify", "--recipe", str(tmp_path / "absent.json"), "--run", str(RUN))
    assert missing.returncode == 2
    assert "missing" in (missing.stdout + missing.stderr)

    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert _verify(broken).returncode == 2

    recipe = json.loads(_write_recipe(tmp_path).read_text(encoding="utf-8"))
    recipe["schema_version"] = "wangp-dspy.render-recipe/v0"
    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps(recipe), encoding="utf-8")
    result = _verify(wrong)
    assert result.returncode == 2
    assert "unsupported recipe schema" in (result.stdout + result.stderr)


def test_recipe_verbs_are_local_and_leave_the_run_untouched(tmp_path: Path) -> None:
    ssh_dir = tmp_path / "bin"
    ssh_dir.mkdir()
    ssh_log = tmp_path / "ssh.log"
    fake = ssh_dir / "ssh"
    fake.write_text(f"#!/bin/sh\necho \"$@\" >> {ssh_log}\nexit 255\n", encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    env = {"PATH": f"{ssh_dir}:{os.environ['PATH']}"}

    before = sorted(path.name for path in RUN.iterdir())
    recipe = _write_recipe(tmp_path)
    assert _verify(recipe, env=env).returncode == 0
    assert not ssh_log.exists()
    assert sorted(path.name for path in RUN.iterdir()) == before
    assert not list(RUN.glob("**/*.tmp*"))
