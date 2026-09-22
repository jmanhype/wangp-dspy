"""Real-process coverage for installed-package repository-root resolution."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "datasets/content_briefs/lf004-operator-dogfood-56f/brief.json"
PLATES = ROOT / "datasets/content_briefs/lf004-operator-dogfood/plates"


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=240,
        check=False,
    )


def _environment(
    temporary: Path, outside: Path, tool_dir: Path, tool_bin: Path
) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "UV_TOOL_DIR": str(tool_dir),
            "UV_TOOL_BIN_DIR": str(tool_bin),
            "UV_OFFLINE": "1",
            "WANGP_CONFIG": str(temporary / "empty-config.toml"),
        }
    )
    environment.pop("WANGP_REPOSITORY_ROOT", None)
    for variable in (
        "WANGP_SSH_TARGET",
        "WANGP_WGP_ROOT",
        "WANGP_PULL_ROOT",
        "WANGP_WGP_PYTHON",
        "WANGP_3090",
    ):
        environment.pop(variable, None)
    del outside
    return environment


def _plan_command(
    wgp: Path, output: Path, run_dir: Path
) -> list[str]:
    return [
        str(wgp),
        "plan",
        "--brief",
        str(BRIEF),
        "--plates",
        str(PLATES),
        "--out",
        str(output),
        "--run-dir",
        str(run_dir),
    ]


def test_installed_plan_boundary_override_and_checkout_parity() -> None:
    with TemporaryDirectory(prefix="wangp-repository-root-") as temporary_name:
        temporary = Path(temporary_name)
        outside = temporary / "outside"
        tool_dir = temporary / "tools"
        tool_bin = temporary / "bin"
        for path in (outside, tool_dir, tool_bin):
            path.mkdir()
        (temporary / "empty-config.toml").touch()
        environment = _environment(temporary, outside, tool_dir, tool_bin)

        installed = _run(
            [
                "uv",
                "tool",
                "install",
                "--offline",
                "--refresh-package",
                "wangp-dspy",
                "--from",
                str(ROOT),
                "wangp-dspy",
            ],
            cwd=outside,
            env=environment,
        )
        install_output = installed.stdout + installed.stderr
        assert installed.returncode == 0, install_output
        wgp = tool_bin / "wgp"
        assert wgp.is_file()

        no_root_output = temporary / "installed-plan.json"
        no_root_run = temporary / "installed-run"
        no_root = _run(
            _plan_command(wgp, no_root_output, no_root_run),
            cwd=outside,
            env=environment,
        )
        boundary = no_root.stdout + no_root.stderr
        assert no_root.returncode == 2, boundary
        assert "diagnostic code=INPUT_INVALID" in boundary
        assert "A Wangp Git checkout is required" in boundary
        assert "Run inside a Wangp Git checkout" in boundary
        assert "WANGP_REPOSITORY_ROOT=<repository>" in boundary
        assert "unexpected internal error" not in boundary
        assert "Traceback" not in boundary
        assert "site-packages" not in boundary
        assert not no_root_output.exists()

        release = _run(
            [str(wgp), "release", "verify"],
            cwd=outside,
            env=environment,
        )
        release_boundary = release.stdout + release.stderr
        assert release.returncode == 2, release_boundary
        assert "diagnostic code=INPUT_INVALID" in release_boundary
        assert "unexpected internal error" not in release_boundary

        shared_output = temporary / "shared-plan.json"
        shared_run = temporary / "shared-run"
        flag_command = _plan_command(wgp, shared_output, shared_run)
        flag_command.insert(2, "--repository-root")
        flag_command.insert(3, str(ROOT))
        overridden = _run(
            flag_command,
            cwd=outside,
            env=environment,
        )
        override_output = overridden.stdout + overridden.stderr
        assert overridden.returncode == 0, override_output
        assert "clips=4" in override_output
        installed_plan = shared_output.read_bytes()
        installed_payload = json.loads(installed_plan)
        assert installed_payload["repository"]["repo_root"] == str(ROOT)

        shutil.rmtree(shared_run)
        in_checkout = _run(
            [
                "uv",
                "run",
                "--frozen",
                "--extra",
                "dev",
                "wgp",
                *_plan_command(wgp, shared_output, shared_run)[1:],
            ],
            cwd=ROOT,
            env=environment,
        )
        checkout_output = in_checkout.stdout + in_checkout.stderr
        assert in_checkout.returncode == 0, checkout_output
        assert shared_output.read_bytes() == installed_plan

        environment_root = environment.copy()
        environment_root["WANGP_REPOSITORY_ROOT"] = str(ROOT)
        env_output = temporary / "environment-plan.json"
        env_run = temporary / "environment-run"
        environment_override = _run(
            _plan_command(wgp, env_output, env_run),
            cwd=outside,
            env=environment_root,
        )
        environment_result = environment_override.stdout + environment_override.stderr
        assert environment_override.returncode == 0, environment_result
        environment_payload = json.loads(env_output.read_text(encoding="utf-8"))
        assert (
            environment_payload["repository"]
            == installed_payload["repository"]
        )


def test_no_checkout_front_doors_remain_available() -> None:
    with TemporaryDirectory(prefix="wangp-no-checkout-") as temporary_name:
        temporary = Path(temporary_name)
        outside = temporary / "outside"
        tool_dir = temporary / "tools"
        tool_bin = temporary / "bin"
        for path in (outside, tool_dir, tool_bin):
            path.mkdir()
        (temporary / "empty-config.toml").touch()
        environment = _environment(temporary, outside, tool_dir, tool_bin)
        install = _run(
            [
                "uv",
                "tool",
                "install",
                "--offline",
                "--refresh-package",
                "wangp-dspy",
                "--from",
                str(ROOT),
                "wangp-dspy",
            ],
            cwd=outside,
            env=environment,
        )
        assert install.returncode == 0, install.stdout + install.stderr
        wgp = tool_bin / "wgp"

        doctor = _run([str(wgp), "doctor"], cwd=outside, env=environment)
        assert doctor.returncode == 0, doctor.stdout + doctor.stderr
        assert doctor.stdout.endswith("ready=yes\n")

        brief = _run(
            [str(wgp), "brief", "validate", str(BRIEF)],
            cwd=outside,
            env=environment,
        )
        assert brief.returncode == 0, brief.stdout + brief.stderr
        assert "valid=true" in brief.stdout

        plan_output = temporary / "content-summary.json"
        content = _run(
            [
                str(wgp),
                "content",
                "--brief",
                str(BRIEF),
                "--plates",
                str(PLATES),
                "--out",
                str(plan_output),
                "--json",
            ],
            cwd=outside,
            env=environment,
        )
        assert content.returncode == 0, content.stdout + content.stderr
        payload = json.loads(content.stdout)
        assert payload["what_will_be_generated"]["clip_count"] == 4
        assert "repository" not in payload
        assert not plan_output.exists()
