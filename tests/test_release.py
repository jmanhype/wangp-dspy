"""Real-process release-readiness integration tests."""

from __future__ import annotations

import hashlib, json, os, stat, subprocess, sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921"
WGP = Path(sys.executable).with_name("wgp")
SCHEMA = "wangp-dspy.render-recipe/v3"


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                          text=True, check=True)


def _clone(tmp_path: Path) -> Path:
    clone = tmp_path / "checkout"
    subprocess.run(
        ["git", "clone", "--shared", "--quiet", "--config",
         "user.email=release-test@example.invalid", "--config",
         "user.name=Release Test", str(ROOT), str(clone)],
        capture_output=True, text=True, check=True)
    assert _git(clone, "status", "--short").stdout == ""
    return clone

def _network_guard(guard_root: Path) -> tuple[Path, Path]:
    (guard_root / "bin").mkdir(parents=True)
    bin_dir = guard_root / "bin"
    ssh_log = guard_root / "ssh.log"
    (guard_root / "sitecustomize.py").write_text(
        "import sys\n"
        "def audit(event, args):\n"
        "    if event in {'socket.connect', 'socket.getaddrinfo', 'urllib.Request'}:\n"
        "        raise RuntimeError(f'unexpected network call: {event}')\n"
        "sys.addaudithook(audit)\n", encoding="utf-8")
    fake_ssh = bin_dir / "ssh"
    fake_ssh.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" > {ssh_log}\nexit 255\n",
                        encoding="utf-8")
    fake_ssh.chmod(fake_ssh.stat().st_mode | stat.S_IEXEC)
    return guard_root, ssh_log

def _run(root: Path, guard_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    guard, ssh_log = _network_guard(guard_root)
    environment = {**os.environ, "PYTHONPATH": f"{guard}:{root}",
                   "PATH": f"{guard / 'bin'}:{os.environ['PATH']}"}
    for host_variable in ("WANGP_SSH_TARGET", "WANGP_WGP_ROOT",
                          "WANGP_PULL_ROOT", "WANGP_3090"):
        environment.pop(host_variable, None)
    result = subprocess.run([str(WGP), *args], cwd=root, capture_output=True,
                            text=True, env=environment)
    assert not ssh_log.exists(), ssh_log.read_text(encoding="utf-8")
    assert "Traceback (most recent call last)" not in result.stdout + result.stderr
    return result

def _release_inputs(root: Path) -> list[Path]:
    evidence = RUN if root == ROOT else root / RUN.relative_to(ROOT)
    return [root / "VERSION", root / "pyproject.toml", root / "CHANGELOG.md",
            root / "wangp/__init__.py", root / "wangp/release.py",
            root / "wangp/recipe.py", root / "wangp/cli.py",
            *sorted(evidence.rglob("*"))]

def _snapshot(root: Path, extra: Path | None = None) -> dict[str, object]:
    status = _git(root, "status", "--porcelain=v1", "--untracked-files=normal").stdout
    files: dict[str, str] = {}
    for path in [* _release_inputs(root), *([extra] if extra else [])]:
        if path.is_file():
            files[str(path.relative_to(root))] = hashlib.sha256(
                path.read_bytes()).hexdigest()
    return {"status": status, "files": files}

def _run_verified(root: Path, guard_root: Path, extra: Path | None,
                  *args: str) -> subprocess.CompletedProcess[str]:
    before = _snapshot(root, extra)
    result = _run(root, guard_root, *args)
    assert _snapshot(root, extra) == before
    return result

def _commit(clone: Path, path: Path, message: str) -> None:
    _git(clone, "add", str(path.relative_to(clone)))
    _git(clone, "commit", "-m", message)


def _release_payload(result: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(result.stdout)["release"]

def test_clean_checkout_and_real_repository_are_release_ready(tmp_path: Path) -> None:
    clone = _clone(tmp_path)
    guard = tmp_path / "success-human"
    human = _run_verified(clone, guard, None, "release", "verify")
    assert human.returncode == 0, human.stdout + human.stderr
    assert all(phrase in human.stdout for phrase in (
        "version=0.1.0", "check=version status=pass",
        "check=changelog status=pass", "check=recipe_schema status=pass",
        "check=tree status=pass", "tag-ready=v0.1.0", "tag_created=false",
        "no tag was created", "release=ready"))

    guard = tmp_path / "success-json"
    json_run = _run_verified(clone, guard, None, "release", "verify", "--json")
    assert json_run.returncode == 0, json_run.stdout + json_run.stderr
    payload = _release_payload(json_run)
    assert (payload["version"], payload["ready"], payload["tag"],
            payload["tag_created"]) == ("0.1.0", True, "v0.1.0", False)
    names = " ".join(check["name"] for check in payload["checks"])
    assert names == "version changelog recipe_schema tree"
    assert all(check["status"] == "pass" for check in payload["checks"])
    assert payload["checks"][2]["observed"] == SCHEMA

    assert _git(ROOT, "status", "--short").stdout == ""
    guard = tmp_path / "success-real"
    real = _run_verified(ROOT, guard, None, "release", "verify", "--json")
    assert real.returncode == 0, real.stdout + real.stderr
    assert _release_payload(real)["tag"] == "v0.1.0"


def test_release_failure_matrix_is_typed_and_read_only(tmp_path: Path) -> None:
    clone = _clone(tmp_path)
    baseline = _git(clone, "rev-parse", "HEAD").stdout.strip()
    cases = [
        ("version", "VERSION", ("0.1.0\n", "0.2.0\n"), 0, "0.1.0", {
            "VERSION": "0.2.0", "pyproject.toml": "0.1.0",
            "wangp.__version__": "0.1.0"}),
        ("changelog", "CHANGELOG.md", ("## [0.1.0] - 2026-09-21",
                                       "## [0.0.9] - 2026-09-21"), 1, "0.1.0", None),
        ("recipe_schema", "wangp/recipe.py", (
            'RECIPE_SCHEMA = "wangp-dspy.render-recipe/v3"',
            'RECIPE_SCHEMA = "wangp-dspy.render-recipe/v4"'), 2, SCHEMA,
            "wangp-dspy.render-recipe/v4"),
    ]
    for name, relative, change, index, expected, observed in cases:
        _git(clone, "reset", "--hard", baseline)
        target = clone / relative
        old, new = change
        target.write_text(target.read_text(encoding="utf-8").replace(
            old, new), encoding="utf-8")
        _commit(clone, target, f"release-test: {name}")
        guard = tmp_path / name
        result = _run_verified(clone, guard, None, "release", "verify", "--json")
        assert result.returncode == 2, result.stdout + result.stderr
        payload = _release_payload(result)
        check = payload["checks"][index]
        assert (payload["ready"], payload["tag_created"],
                check["name"], check["status"], check["expected"],
                check["observed"]) == (False, False, name, "failed",
                                      expected, observed)

    _git(clone, "reset", "--hard", baseline)
    untracked = clone / "untracked-release-probe.txt"
    untracked.write_text("dirty release test\n", encoding="utf-8")
    guard = tmp_path / "dirty"
    result = _run_verified(clone, guard, untracked, "release", "verify")
    assert result.returncode == 2, result.stdout + result.stderr
    assert all(phrase in result.stdout for phrase in (
        "check=tree status=failed", "'changed_path_count': 1",
        "'untracked_path_count': 1", "release=not_ready"))
