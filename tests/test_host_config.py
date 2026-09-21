"""Real-file, real-environment tests for render-host configuration."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from wangp.config import (
    HostConfigError,
    load_host_config,
    missing_host_keys,
    render_host,
    require_host_config,
)


ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "datasets/content_briefs/lf004-operator-dogfood-56f/brief.json"
PLATES = ROOT / "datasets/content_briefs/lf004-operator-dogfood/plates"


def _write_config(path: Path, *, target: str | None = None,
                  wgp_root: str | None = None,
                  pull_root: str | None = None) -> None:
    lines = ["[host]"]
    if target is not None:
        lines.append(f'target = "{target}"')
    if wgp_root is not None:
        lines.append(f'wgp_root = "{wgp_root}"')
    if pull_root is not None:
        lines.append(f'pull_root = "{pull_root}"')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_environment_user_and_repository_precedence() -> None:
    with TemporaryDirectory(prefix="wangp-config-") as temporary:
        root = Path(temporary) / "repository"
        user = Path(temporary) / "user" / "config.toml"
        root.mkdir()
        _write_config(
            root / "wangp.toml",
            target="repo-host",
            wgp_root="/repo/wgp",
            pull_root="/repo/pull",
        )
        _write_config(
            user,
            target="user-host",
            wgp_root="/user/wgp",
            pull_root="/user/pull",
        )
        environment = {
            "WANGP_CONFIG": str(user),
            "WANGP_PULL_ROOT": "/environment/pull",
        }
        config = load_host_config(
            repository_root=root, environ=environment
        )
        assert config.target is not None and config.target.value == "user-host"
        assert config.target.source == "user_config"
        assert config.wgp_root is not None
        assert config.wgp_root.value == "/user/wgp"
        assert config.pull_root is not None
        assert config.pull_root.value == "/environment/pull"
        assert config.pull_root.source == "environment"
        assert missing_host_keys(config) == ()


def test_safe_detection_uses_local_wgp_marker_and_never_guesses_remote() -> None:
    with TemporaryDirectory(prefix="wangp-detect-") as temporary:
        base = Path(temporary)
        root = base / "repository"
        checkout = base / "Wan2GP"
        root.mkdir()
        checkout.mkdir()
        (checkout / "wgp.py").write_text("", encoding="utf-8")
        config = load_host_config(
            repository_root=root,
            environ={"WANGP_CONFIG": str(base / "absent.toml")},
        )
        assert config.target is not None
        assert (config.target.value, config.target.source) == (
            "localhost", "detection"
        )
        assert config.wgp_root is not None
        assert config.wgp_root.value == str(checkout.resolve())
        assert config.pull_root is not None
        assert config.pull_root.value == str(
            root.resolve() / "datasets/runs/pull"
        )

    with TemporaryDirectory(prefix="wangp-undetected-") as undetected:
        base = Path(undetected)
        empty_root = base / "repository"
        empty_root.mkdir()
        unconfigured = load_host_config(
            repository_root=empty_root,
            environ={"WANGP_CONFIG": str(base / "absent.toml")},
        )
        assert missing_host_keys(unconfigured) == (
            "host.target", "host.wgp_root"
        )


def test_partial_configuration_names_every_missing_key() -> None:
    with TemporaryDirectory(prefix="wangp-partial-") as temporary:
        root = Path(temporary) / "repository"
        root.mkdir()
        _write_config(root / "wangp.toml", pull_root="/configured/pull")
        config = load_host_config(
            repository_root=root,
            environ={"WANGP_CONFIG": str(root / "absent-user.toml")},
        )
        assert missing_host_keys(config) == ("host.target", "host.wgp_root")
        with pytest.raises(HostConfigError) as caught:
            render_host(config)
        message = str(caught.value)
        assert "missing host.target, host.wgp_root" in message
        assert "WANGP_SSH_TARGET, WANGP_WGP_ROOT" in message


def test_unknown_keys_and_invalid_path_types_have_file_context() -> None:
    with TemporaryDirectory(prefix="wangp-invalid-") as temporary:
        root = Path(temporary) / "repository"
        root.mkdir()
        config_path = root / "wangp.toml"
        config_path.write_text("[host]\ntarget = 7\n", encoding="utf-8")
        with pytest.raises(HostConfigError, match=r"wangp\.toml.*host\.target"):
            load_host_config(
                repository_root=root,
                environ={"WANGP_CONFIG": str(root / "absent-user.toml")},
            )

        config_path.write_text(
            "[other]\nvalue = 1\n\n[host]\ntarget = \"alias\"\n",
            encoding="utf-8",
        )
        with pytest.raises(HostConfigError, match=r"unknown configuration table"):
            load_host_config(
                repository_root=root,
                environ={"WANGP_CONFIG": str(root / "absent-user.toml")},
            )


def test_explicit_localhost_environment_constructs_existing_host_seam() -> None:
    with TemporaryDirectory(prefix="wangp-complete-") as temporary:
        root = Path(temporary) / "repository"
        root.mkdir()
        pull = Path(temporary) / "pull"
        config = load_host_config(
            repository_root=root,
            environ={
                "WANGP_SSH_TARGET": "localhost",
                "WANGP_WGP_ROOT": "/configured/wgp",
                "WANGP_PULL_ROOT": str(pull),
                "WANGP_CONFIG": str(root / "absent-user.toml"),
            },
        )
        host = render_host(config)
        assert host.target == "localhost"
        assert host.wgp_root == "/configured/wgp"
        assert host.pull_root == str(pull)
        assert host.map_path(str(pull / "settings.json")) == (
            "/configured/wgp/settings.json"
        )


def test_no_config_preserves_no_gpu_lane_and_names_exact_keys() -> None:
    with TemporaryDirectory(prefix="wangp-no-host-") as temporary:
        output_root = Path(temporary)
        environment = os.environ.copy()
        environment.update({
            "WANGP_CONFIG": str(output_root / "absent-user-config.toml"),
            "TMPDIR": str(output_root),
        })
        for key in (
            "WANGP_SSH_TARGET", "WANGP_WGP_ROOT", "WANGP_PULL_ROOT"
        ):
            environment.pop(key, None)

        doctor = subprocess.run(
            ["uv", "run", "--frozen", "--extra", "dev", "wgp", "doctor"],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        assert doctor.returncode == 0, doctor.stdout + doctor.stderr
        assert "[SKIP] host_configuration:" in doctor.stdout
        assert "host.target=unconfigured" in doctor.stdout
        assert "host.wgp_root=unconfigured" in doctor.stdout
        assert "ready=yes" in doctor.stdout
        assert "ssh_reachable" not in doctor.stdout

        output = output_root / "plan.json"
        run_dir = output_root / "run"
        plan = subprocess.run(
            [
                "uv", "run", "--frozen", "--extra", "dev", "wgp", "plan",
                "--brief", str(BRIEF),
                "--plates", str(PLATES),
                "--out", str(output),
                "--run-dir", str(run_dir),
            ],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        assert plan.returncode == 0, plan.stdout + plan.stderr
        assert "clips=4" in plan.stdout
        assert "gpu_work=false" in plan.stdout
        assert "queue_submitted=false" in plan.stdout
        payload = json.loads(output.read_text(encoding="utf-8"))
        assert payload["summary"]["clip_count"] == 4

        import scripts.run_jobs as run_jobs

        run_jobs_environment = {
            key: value
            for key, value in environment.items()
            if key in {"PATH", "HOME", "TMPDIR", "WANGP_CONFIG"}
        }
        previous = os.environ.copy()
        try:
            os.environ.clear()
            os.environ.update(run_jobs_environment)
            with pytest.raises(HostConfigError, match="host.target"):
                run_jobs._default_host()
        finally:
            os.environ.clear()
            os.environ.update(previous)
