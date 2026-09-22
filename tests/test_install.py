"""Real-process coverage for the source installer."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.sh"
DEFAULT_REPOSITORY = "https://github.com/jmanhype/wangp-dspy.git"
DEFAULT_GIT_REQUIREMENT = "git+https://github.com/jmanhype/wangp-dspy.git@main"
UV_DOWNLOAD = "curl -LsSf https://astral.sh/uv/install.sh -o uv-installer.sh"


def run(
    command: list[str], *, cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, cwd=cwd, env=env, check=False, text=True, capture_output=True
    )


def test_help_and_dry_run_print_commands() -> None:
    with TemporaryDirectory(prefix="wangp-install-dry-") as temporary:
        outside = Path(temporary) / "outside"
        tool_bin = Path(temporary) / "bin"
        outside.mkdir()
        tool_bin.mkdir()
        env = os.environ.copy()
        env["UV_TOOL_DIR"] = str(Path(temporary) / "tools")
        env["UV_TOOL_BIN_DIR"] = str(tool_bin)

        syntax = run(["sh", "-n", str(INSTALLER)], cwd=outside, env=env)
        assert syntax.returncode == 0, syntax.stderr

        help_result = run(["sh", str(INSTALLER), "--help"], cwd=outside, env=env)
        assert help_result.returncode == 0, help_result.stderr
        assert "--dry-run" in help_result.stdout
        assert "--source <path-or-url>" in help_result.stdout
        assert DEFAULT_REPOSITORY in help_result.stdout
        assert "sh install.sh" in help_result.stdout
        assert "| sh" not in help_result.stdout

        default_dry_run = run(
            ["sh", str(INSTALLER), "--dry-run"], cwd=outside, env=env
        )
        assert default_dry_run.returncode == 0, default_dry_run.stderr
        assert (
            f"uv tool install --upgrade --from {DEFAULT_GIT_REQUIREMENT} wangp-dspy"
            in default_dry_run.stdout
        )
        assert DEFAULT_GIT_REQUIREMENT.startswith("git+https://")
        assert DEFAULT_GIT_REQUIREMENT.endswith("@main")

        dry_run = run(
            ["sh", str(INSTALLER), "--dry-run", "--source", str(ROOT)],
            cwd=outside,
            env=env,
        )
        assert dry_run.returncode == 0, dry_run.stderr
        assert (
            f"uv tool install --upgrade --from {ROOT} wangp-dspy" in dry_run.stdout
        )
        assert f"{tool_bin / 'wgp'} doctor" in dry_run.stdout
        assert not any(tool_bin.iterdir())


def test_real_install_doctor_and_checkout_boundary() -> None:
    with TemporaryDirectory(prefix="wangp-install-real-") as temporary:
        root = Path(temporary)
        outside = root / "outside"
        tool_dir = root / "tools"
        tool_bin = root / "bin"
        config = root / "empty-config.toml"
        outside.mkdir()
        tool_dir.mkdir()
        tool_bin.mkdir()
        config.touch()
        env = os.environ.copy()
        env.update(
            UV_TOOL_DIR=str(tool_dir),
            UV_TOOL_BIN_DIR=str(tool_bin),
            WANGP_CONFIG=str(config),
        )
        for variable in (
            "WANGP_SSH_TARGET",
            "WANGP_WGP_ROOT",
            "WANGP_PULL_ROOT",
            "WANGP_WGP_PYTHON",
            "WANGP_3090",
        ):
            env.pop(variable, None)

        installed = run(
            ["sh", str(INSTALLER), "--source", str(ROOT)], cwd=outside, env=env
        )
        install_output = installed.stdout + installed.stderr
        assert installed.returncode == 0, install_output
        assert "Installed 1 executable: wgp" in install_output
        assert installed.stdout.endswith("ready=yes\n")

        wgp = tool_bin / "wgp"
        assert wgp.is_file() and os.access(wgp, os.X_OK)
        doctor = run([str(wgp), "doctor"], cwd=outside, env=env)
        assert doctor.returncode == 0, doctor.stdout + doctor.stderr
        assert doctor.stdout.endswith("ready=yes\n")

        boundary = run([str(wgp), "release", "verify"], cwd=outside, env=env)
        boundary_output = boundary.stdout + boundary.stderr
        print(f"repository-scoped release output: {boundary_output}", flush=True)
        assert boundary.returncode == 2, boundary_output
        assert "cannot read release version sources" in boundary_output
        assert "release=ready" not in boundary_output

        plan = run(
            [
                str(wgp),
                "plan",
                "--brief",
                str(
                    ROOT
                    / "datasets/content_briefs/lf004-operator-dogfood-56f/brief.json"
                ),
                "--plates",
                str(
                    ROOT / "datasets/content_briefs/lf004-operator-dogfood/plates"
                ),
                "--out",
                str(root / "plan.json"),
                "--run-dir",
                str(root / "plan-run"),
            ],
            cwd=outside,
            env=env,
        )
        plan_output = plan.stdout + plan.stderr
        print(f"installed plan boundary output: {plan_output}", flush=True)
        assert plan.returncode == 4, plan_output
        assert "unexpected internal error: RepositoryIdentityError" in plan_output
        assert "not a git repository" in plan_output
        assert not (root / "plan.json").exists()


def test_uv_reported_bin_and_checkout_use_local_repository() -> None:
    with TemporaryDirectory(prefix="wangp-install-checkout-") as temporary:
        root = Path(temporary)
        outside = root / "outside"
        tool_dir = root / "tools"
        xdg_bin = root / "xdg-bin"
        checkout = root / "wangp-dspy"
        config = root / "empty-config.toml"
        outside.mkdir()
        tool_dir.mkdir()
        xdg_bin.mkdir()
        config.touch()
        env = os.environ.copy()
        env.update(
            UV_TOOL_DIR=str(tool_dir),
            XDG_BIN_HOME=str(xdg_bin),
            WANGP_CONFIG=str(config),
        )
        env.pop("UV_TOOL_BIN_DIR", None)
        for variable in (
            "WANGP_SSH_TARGET",
            "WANGP_WGP_ROOT",
            "WANGP_PULL_ROOT",
            "WANGP_WGP_PYTHON",
            "WANGP_3090",
        ):
            env.pop(variable, None)

        reported_bin = run(
            ["uv", "tool", "dir", "--bin"], cwd=outside, env=env
        )
        assert reported_bin.returncode == 0, reported_bin.stderr
        assert reported_bin.stdout.strip() == str(xdg_bin)

        result = run(
            [
                "sh",
                str(INSTALLER),
                "--source",
                str(ROOT),
                "--checkout",
                str(checkout),
            ],
            cwd=outside,
            env=env,
        )
        output = result.stdout + result.stderr
        assert result.returncode == 0, output
        assert result.stdout.endswith("quickstart/run\"\n")
        assert (xdg_bin / "wgp").is_file()
        assert (checkout / ".git").is_dir()
        assert (checkout / "VERSION").read_text(encoding="utf-8").strip() == "0.1.0"
        assert f'cd "{checkout}"' in output
        assert "uv sync --extra dev" in output
        assert "scripts/run_content_brief.py" in output


def test_missing_uv_fails_closed() -> None:
    with TemporaryDirectory(prefix="wangp-install-nouv-") as temporary:
        root = Path(temporary)
        empty_path = root / "empty-path"
        tool_dir = root / "tools"
        tool_bin = root / "bin"
        empty_path.mkdir()
        tool_dir.mkdir()
        tool_bin.mkdir()
        env = os.environ.copy()
        env.update(
            PATH=str(empty_path),
            UV_TOOL_DIR=str(tool_dir),
            UV_TOOL_BIN_DIR=str(tool_bin),
        )

        result = run(
            ["/bin/sh", str(INSTALLER), "--source", str(ROOT)],
            cwd=root,
            env=env,
        )
        output = result.stdout + result.stderr
        assert result.returncode != 0, output
        assert "MISSING_PREREQUISITE: uv is required" in output
        assert UV_DOWNLOAD in output
        assert "sh uv-installer.sh" in output
        assert not any(tool_dir.iterdir())
        assert not any(tool_bin.iterdir())
