"""Static and real-seam integration coverage for active host wiring."""

from __future__ import annotations

import ast
from pathlib import Path
from tempfile import TemporaryDirectory

from wangp.config import load_host_config, render_host


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_ROOTS = ("host", "services", "scripts", "predict", "qc")
FORBIDDEN_LITERALS = (b'"3090"', b"/home/straughter/Wan2GP")


def _active_files() -> list[Path]:
    files: list[Path] = []
    for directory in ACTIVE_ROOTS:
        for path in (ROOT / directory).rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".sh"}:
                continue
            if "datasets" in path.parts or "test" in path.name:
                continue
            files.append(path)
    return sorted(files)


def test_active_runtime_has_no_operator_host_defaults() -> None:
    matches: list[str] = []
    for path in _active_files():
        content = path.read_bytes()
        if any(literal in content for literal in FORBIDDEN_LITERALS):
            matches.append(str(path.relative_to(ROOT)))
    assert matches == []


def test_run_jobs_default_host_is_configuration_backed() -> None:
    source = (ROOT / "scripts/run_jobs.py").read_text(encoding="utf-8")
    tree = ast.parse(source, filename="scripts/run_jobs.py")
    function = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_default_host"
    )
    names = {
        node.id
        for node in ast.walk(function)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    assert {"load_host_config", "render_host"} <= names
    constants = {
        node.value
        for node in ast.walk(function)
        if isinstance(node, ast.Constant)
    }
    assert "3090" not in constants
    assert "/home/straughter/Wan2GP" not in constants


def test_complete_environment_values_reach_render_host_unchanged() -> None:
    with TemporaryDirectory(prefix="wangp-host-seam-") as temporary:
        root = Path(temporary) / "repository"
        pull = Path(temporary) / "pull"
        root.mkdir()
        config = load_host_config(
            repository_root=root,
            environ={
                "WANGP_SSH_TARGET": "configured-alias",
                "WANGP_WGP_ROOT": "/configured/wgp-root",
                "WANGP_PULL_ROOT": str(pull),
                "WANGP_CONFIG": str(root / "absent-user.toml"),
            },
        )
        host = render_host(config)
        assert host.target == "configured-alias"
        assert host.wgp_root == "/configured/wgp-root"
        assert host.pull_root == str(pull)
