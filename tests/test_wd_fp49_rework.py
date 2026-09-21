"""Regression coverage for the eleven WD-fp49 PR-review findings."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

import wangp.config
from host.render_host import LocalHost, SshHost
from host.wangp_adapter import WanGPAdapter, build_wgp_lock_argv
from predict.profile_selector import ProfileDecision
from predict.prompt_director import RenderBrief
from qc.audio_critic.av_sync_gate import RemoteSyncNetAVSyncJudge
from wangp.config import HostConfigError, load_host_config


ROOT = Path(__file__).resolve().parents[1]


def _write_host_config(
    path: Path,
    *,
    target: str | None = None,
    wgp_root: str | None = None,
    pull_root: str | None = None,
    wgp_python: str | None = None,
) -> None:
    rows = ["[host]"]
    values = {
        "target": target,
        "wgp_root": wgp_root,
        "pull_root": pull_root,
        "wgp_python": wgp_python,
    }
    for field, value in values.items():
        if value is not None:
            rows.append(f'{field} = "{value}"')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def _source_repository(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "pyproject.toml").write_text(
        '[project]\nname = "configuration-test"\n', encoding="utf-8"
    )
    (path / "wangp.toml").write_text("[host]\n", encoding="utf-8")
    return path


def _isolated_environment(config: Path) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key in {"PATH", "HOME", "TMPDIR", "SYSTEMROOT"}
    }
    environment["WANGP_CONFIG"] = str(config)
    for key in (
        "WANGP_SSH_TARGET",
        "WANGP_WGP_ROOT",
        "WANGP_PULL_ROOT",
        "WANGP_WGP_PYTHON",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
    ):
        environment.pop(key, None)
    return environment


def test_run_qc_real_entry_point_reports_configuration_not_name_error() -> None:
    environment = _isolated_environment(ROOT / "does-not-exist-config.toml")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/run_qc.py"),
            str(ROOT / "does-not-exist.mp4"),
            str(ROOT / "does-not-exist-record.json"),
            "surreal",
        ],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 2
    assert "configuration error:" in result.stderr
    assert "missing host.target, host.wgp_root" in result.stderr
    assert "NameError" not in result.stderr


def test_documented_default_user_config_is_loaded(monkeypatch, tmp_path) -> None:
    home = tmp_path / "home"
    root = _source_repository(tmp_path / "repository")
    documented = home / ".config/wangp/config.toml"
    _write_host_config(documented, target="documented-user-host")
    monkeypatch.setattr(
        wangp.config.Path,
        "home",
        classmethod(lambda cls: home),
    )

    environment = _isolated_environment(tmp_path / "absent-config.toml")
    environment.pop("WANGP_CONFIG", None)
    config = load_host_config(repository_root=root, environ=environment)

    assert config.user_config == documented
    assert config.target is not None
    assert config.target.value == "documented-user-host"
    assert config.target.source == "user_config"


def test_file_only_target_reaches_gpu_sequencing_environment(tmp_path) -> None:
    from wangp.gpu_sequencing import gpu_sequence_environment

    root = _source_repository(tmp_path / "repository")
    config = tmp_path / "config.toml"
    _write_host_config(
        config,
        target="file-only-alias",
        wgp_root="/remote/Wan2GP",
        pull_root=str(tmp_path / "pull"),
    )
    environment = _isolated_environment(config)

    sequence_environment = gpu_sequence_environment(environment)

    assert sequence_environment["WANGP_SSH_TARGET"] == "file-only-alias"
    assert root is not None


def _gpu_seq_calls(path: Path) -> list[ast.Call]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        arguments = [
            constant.value
            for argument in node.args
            for constant in ast.walk(argument)
            if isinstance(constant, ast.Constant)
            and isinstance(constant.value, str)
        ]
        if any(value.endswith("gpu_seq.sh") for value in arguments):
            function = node.func
            name = (
                function.id
                if isinstance(function, ast.Name)
                else function.attr
                if isinstance(function, ast.Attribute)
                else ""
            )
            if name in {"run", "sh", "subprocess"}:
                calls.append(node)
    return calls


def test_all_gpu_seq_callers_pass_resolved_environment() -> None:
    callers = (
        ROOT / "scripts/run_batch.py",
        ROOT / "scripts/ab_render_qc.py",
    )
    checked = 0
    for path in callers:
        calls = _gpu_seq_calls(path)
        assert calls, f"no gpu_seq.sh calls found in {path}"
        for call in calls:
            environment = next(
                (keyword for keyword in call.keywords if keyword.arg == "env"),
                None,
            )
            assert environment is not None
            assert isinstance(environment.value, ast.Call)
            function = environment.value.func
            name = (
                function.id
                if isinstance(function, ast.Name)
                else function.attr
                if isinstance(function, ast.Attribute)
                else ""
            )
            assert name == "gpu_sequence_environment"
            checked += 1
    assert checked >= 4


def test_marathon_remote_target_fails_before_local_filesystem(monkeypatch, tmp_path) -> None:
    config = tmp_path / "remote-config.toml"
    _write_host_config(
        config,
        target="remote-render-host",
        wgp_root="/remote/Wan2GP",
        pull_root=str(tmp_path / "pull"),
        wgp_python="/remote/python",
    )
    environment = _isolated_environment(config)
    monkeypatch.chdir(tmp_path)

    result = subprocess.run(
        ["bash", str(ROOT / "scripts/marathon/driver.sh")],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=2,
        check=False,
    )

    assert result.returncode == 2
    assert "localhost-only" in result.stderr
    assert not Path("/home/straughter/marathon").exists()


def test_marathon_driver_uses_helper_scripts_and_configured_interpreter() -> None:
    source = (ROOT / "scripts/marathon/driver.sh").read_text(encoding="utf-8")
    assert "$(cd " not in source
    assert "ls -t " not in source
    assert "ls " not in source
    assert "./venv/bin/python" not in source
    assert "latest-output" in source
    assert "resolve-config" in source


def test_adapter_missing_paths_raise_actionable_configuration_error(
    monkeypatch, tmp_path
) -> None:
    root = _source_repository(tmp_path / "repository")
    environment = _isolated_environment(tmp_path / "absent-config.toml")
    monkeypatch.chdir(root)
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    for key in (
        "WANGP_SSH_TARGET",
        "WANGP_WGP_ROOT",
        "WANGP_PULL_ROOT",
        "WANGP_WGP_PYTHON",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
    ):
        monkeypatch.delenv(key, raising=False)

    adapter = WanGPAdapter(output_dir=str(tmp_path / "output"))
    brief = RenderBrief(
        subject="a detective walks",
        motion="forward",
        camera="dolly",
        style="16mm",
    )
    decision = ProfileDecision(
        model="h3",
        resolution="768p",
        shot_length_frames=107,
        seed_policy="fixed_per_story",
        wangp_profile="profile3",
    )

    with pytest.raises(HostConfigError) as caught:
        adapter.render([brief], decision)

    message = str(caught.value)
    assert "host.wgp_root" in message
    assert "host.wgp_python" in message
    assert "WANGP_WGP_PYTHON" in message


def test_run_jobs_no_config_names_every_renderer_key(
    monkeypatch, tmp_path
) -> None:
    root = _source_repository(tmp_path / "repository")
    environment = _isolated_environment(tmp_path / "absent-config.toml")
    monkeypatch.chdir(root)
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    for key in (
        "WANGP_SSH_TARGET",
        "WANGP_WGP_ROOT",
        "WANGP_PULL_ROOT",
        "WANGP_WGP_PYTHON",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
    ):
        monkeypatch.delenv(key, raising=False)

    from scripts.run_jobs import _default_host

    with pytest.raises(HostConfigError) as caught:
        _default_host()

    assert "missing host.target, host.wgp_root, host.wgp_python" in str(
        caught.value
    )


def test_explicit_target_or_root_does_not_mix_with_local_detection(tmp_path) -> None:
    base = tmp_path
    root = _source_repository(base / "repository")
    checkout = base / "Wan2GP"
    checkout.mkdir()
    (checkout / "wgp.py").write_text("", encoding="utf-8")

    target_only = root / "target-only.toml"
    _write_host_config(
        target_only,
        target="remote-render-host",
        pull_root=str(base / "pull"),
    )
    config = load_host_config(
        repository_root=root,
        environ=_isolated_environment(target_only),
    )
    assert config.target is not None
    assert config.target.value == "remote-render-host"
    assert config.wgp_root is None

    root_only = root / "root-only.toml"
    _write_host_config(
        root_only,
        wgp_root="/remote/Wan2GP",
        pull_root=str(base / "pull"),
    )
    config = load_host_config(
        repository_root=root,
        environ=_isolated_environment(root_only),
    )
    assert config.wgp_root is not None
    assert config.wgp_root.value == "/remote/Wan2GP"
    assert config.target is None


def test_installed_template_pull_root_uses_user_data_not_site_packages(
    monkeypatch, tmp_path
) -> None:
    home = tmp_path / "home"
    site_packages = tmp_path / "site-packages"
    site_packages.mkdir()
    (site_packages / "wangp.toml").write_text("[host]\n", encoding="utf-8")
    monkeypatch.setattr(
        wangp.config.Path,
        "home",
        classmethod(lambda cls: home),
    )
    environment = _isolated_environment(tmp_path / "absent-config.toml")
    environment["XDG_DATA_HOME"] = str(tmp_path / "data")

    config = load_host_config(
        repository_root=site_packages, environ=environment
    )

    expected = tmp_path / "data/wangp/runs/pull"
    assert config.pull_root is not None
    assert Path(config.pull_root.value) == expected
    assert not Path(config.pull_root.value).is_relative_to(site_packages)


@pytest.mark.parametrize(
    ("field", "environment_key"),
    [
        ("wgp_root", "WANGP_WGP_ROOT"),
        ("pull_root", "WANGP_PULL_ROOT"),
        ("wgp_python", "WANGP_WGP_PYTHON"),
    ],
)
def test_relative_paths_are_rejected_from_file_and_environment(
    tmp_path, field, environment_key
) -> None:
    root = _source_repository(tmp_path / "repository")
    file_config = root / "relative-file.toml"
    _write_host_config(
        file_config,
        **{field: "relative/path"},
    )
    with pytest.raises(
        HostConfigError, match=r"field host\." + field + r".*absolute path"
    ):
        load_host_config(
            repository_root=root,
            environ=_isolated_environment(file_config),
        )

    environment = _isolated_environment(tmp_path / "absent-config.toml")
    environment[environment_key] = "relative/path"
    with pytest.raises(
        HostConfigError, match=r"field host\." + field + r".*absolute path"
    ):
        load_host_config(
            repository_root=root,
            environ=environment,
        )


def test_syncnet_judge_needs_only_interpreter_not_complete_render_host(
    monkeypatch, tmp_path
) -> None:
    environment = _isolated_environment(tmp_path / "absent-config.toml")
    environment["WANGP_WGP_PYTHON"] = sys.executable
    for key, value in environment.items():
        monkeypatch.setenv(key, value)

    supplied_host = SshHost(
        target="supplied-fake-host",
        wgp_root="/supplied/Wan2GP",
        pull_root=str(tmp_path / "pull"),
    )
    judge = RemoteSyncNetAVSyncJudge(
        host=supplied_host,
        model_path="/models/syncnet.model",
        host_repo=str(ROOT),
    )

    assert judge.host_python == sys.executable


def test_configured_interpreter_is_used_instead_of_root_venv(
    monkeypatch, tmp_path
) -> None:
    checkout = tmp_path / "Wan2GP"
    checkout.mkdir()
    (checkout / "wgp.py").write_text("", encoding="utf-8")
    config = tmp_path / "config.toml"
    _write_host_config(config, wgp_python=sys.executable)
    environment = _isolated_environment(config)
    for key, value in environment.items():
        monkeypatch.setenv(key, value)

    adapter = WanGPAdapter(
        host=LocalHost(),
        output_dir=str(tmp_path / "output"),
        wgp_outputs_dir=str(checkout / "outputs"),
    )
    argv = build_wgp_lock_argv(
        "/run/settings.json",
        "/run/render.log",
        wangp_dir=str(checkout),
        wgp_python=sys.executable,
    )

    assert adapter.venv_python == sys.executable
    assert sys.executable in argv[0]
    assert f"{checkout}/venv/bin/python" not in argv[0]
