"""Execute and constrain the repository's documented quickstart."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
HYGIENE_FILES = (
    "README.md",
    "LICENSE",
    "VERSION",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "THIRD_PARTY_NOTICES.md",
)


def _section(title: str) -> str:
    lines = README.read_text(encoding="utf-8").splitlines()
    selected: list[str] = []
    active = False
    for line in lines:
        if line.startswith("## "):
            active = line[3:].strip() == title
            if not active and selected:
                break
            continue
        if active:
            selected.append(line)
    assert selected, f"README section not found: {title}"
    return "\n".join(selected)


def _quickstart_commands() -> list[str]:
    quickstart = _section("Tested no-GPU quickstart")
    blocks = re.findall(r"```bash\n(.*?)```", quickstart, flags=re.DOTALL)
    commands = [
        line.strip()
        for block in blocks
        for line in block.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert len(commands) == 2, commands
    assert commands[0] == "uv sync --extra dev"
    assert commands[1].startswith(
        "uv run --frozen --extra dev python scripts/run_content_brief.py "
        "--brief datasets/content_briefs/lf004-operator-dogfood-56f/brief.json "
    )
    return commands


def _run(command: str, *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        shell=True,
        executable="/bin/bash",
        check=True,
        text=True,
        capture_output=True,
    )


def _fail_with_content_brief_error(
    *args: str,
    cwd: Path,
    env: dict[str, str],
    expected: str,
) -> None:
    result = subprocess.run(
        [
            "uv",
            "run",
            "--frozen",
            "--extra",
            "dev",
            "python",
            "scripts/run_content_brief.py",
            *args,
        ],
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )
    combined = result.stdout + result.stderr
    assert result.returncode != 0, combined
    assert "ContentBriefError" in combined, combined
    assert expected in combined, combined


def test_repository_hygiene_and_readme_contract() -> None:
    readme = README.read_text(encoding="utf-8")
    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    for name in HYGIENE_FILES:
        path = ROOT / name
        assert path.is_file(), name
        assert path.stat().st_size > 0, name

    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "0.1.0"
    assert project["project"]["version"] == "0.1.0"
    assert project["project"]["requires-python"] == ">=3.11"
    # Licensing is an owner decision. The repository ships a deliberate source-available
    # notice that grants no rights, so this test fails if the licence is changed silently in
    # either direction: a missing reserved-rights notice, or an OSS grant nobody authorised.
    assert "All rights reserved" in license_text
    assert "NO LICENCE GRANTED" in license_text
    assert "Apache License" not in license_text and "MIT License" not in license_text
    # The third-party notice must disclose the test-only Maestro excerpt corpus rather than
    # claiming nothing third-party is checked in.
    assert "maestro_reference" in notices
    assert "test-only reference corpus" in notices

    for phrase in (
        "typed content brief",
        "deterministic",
        "Whisper",
        "SyncNet",
        "WANGP_SSH_TARGET",
        "3090",
        "/home/straughter/Wan2GP",
        "WD-fp49",
        "final-provenance.json",
        "RepositoryIdentityError",
        "wangp-dspy.content-plan/v1",
        "clip_count",
        "planned_duration_s",
        "dry_run",
        "gpu_work",
        "queue_submitted",
    ):
        assert phrase in readme, phrase

    for phrase in (
        "WanGP Non-Commercial Evaluation 1.1",
        "MiniMax H3",
        "SyncNet v2",
        "MIT-licensed SyncNet",
        "Whisper",
        "Qwen2-Audio",
        "Qwen-VL",
        "does not licence, relicence, or waive conditions",
    ):
        assert phrase in notices, phrase

    _quickstart_commands()


def test_readme_internal_links_resolve() -> None:
    targets = re.findall(r"\[[^\]]+\]\(([^)#\s]+)(?:#[^)]*)?\)", README.read_text(encoding="utf-8"))
    local = [target for target in targets if not re.match(r"^[a-z][a-z0-9+.-]*:", target)]
    assert local
    for target in local:
        assert (ROOT / target).exists(), target


def test_readme_quickstart_runs_in_clean_worktree() -> None:
    commands = _quickstart_commands()
    with TemporaryDirectory(prefix="wangp-readme-quickstart-") as temporary:
        temporary_path = Path(temporary)
        worktree = temporary_path / "repo"
        output_root = temporary_path / "quickstart-output"
        output_root.mkdir()
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree), "HEAD"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        env = {
            "PATH": os.environ["PATH"],
            "HOME": os.environ["HOME"],
            "TMPDIR": str(output_root),
        }
        try:
            assert subprocess.run(
                ["git", "status", "--short"],
                cwd=worktree,
                check=True,
                text=True,
                capture_output=True,
            ).stdout == ""
            _run(commands[0], cwd=worktree, env=env)
            plan_run = _run(commands[1], cwd=worktree, env=env)

            output_dir = output_root / "wangp-quickstart"
            plan_path = output_dir / "plan.json"
            run_dir = output_dir / "run"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            ledger = json.loads((run_dir / "run_ledger.json").read_text(encoding="utf-8"))
            head_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=worktree,
                check=True,
                text=True,
                capture_output=True,
            ).stdout.strip()

            assert "clips=4" in plan_run.stdout
            assert plan["schema_version"] == "wangp-dspy.content-plan/v1"
            assert plan["summary"] == {
                "clip_count": 4,
                "speakers": ["Tess", "Rho", "Tess", "Rho"],
                "planned_duration_s": 9.332,
                "dry_run": True,
                "gpu_work": False,
                "queue_submitted": False,
            }
            assert len(plan["clips"]) == 4
            assert re.fullmatch(r"[0-9a-f]{40}", plan["repository"]["commit_sha"])
            assert plan["repository"]["commit_sha"] == head_sha
            assert plan["repository"]["clean_tree"] is True
            assert plan["repository"]["dirty_tree"] is False
            assert plan["repository"]["changed_path_count"] == 0
            assert plan["repository"]["untracked_path_count"] == 0
            assert (run_dir / "script.txt").is_file()
            assert ledger["status"] == "planned"
            assert ledger["dry_run"] is True
            assert ledger["clip_count"] == 4
            assert ledger["repository"]["clean_tree"] is True

            invalid = output_root / "invalid-brief.json"
            brief = json.loads(
                (worktree / "datasets/content_briefs/lf004-operator-dogfood-56f/brief.json")
                .read_text(encoding="utf-8")
            )
            brief["title"] = ""
            invalid.write_text(json.dumps(brief), encoding="utf-8")
            invalid_output = output_root / "invalid"
            missing_output = output_root / "missing-plate"
            _fail_with_content_brief_error(
                "--brief",
                str(invalid),
                "--plates",
                "datasets/content_briefs/lf004-operator-dogfood/plates",
                "--output",
                str(invalid_output / "plan.json"),
                "--run-dir",
                str(invalid_output / "run"),
                cwd=worktree,
                env=env,
                expected="title must be a non-empty string",
            )
            assert not invalid_output.exists()
            assert not missing_output.exists()
            missing_plates = output_root / "missing-plates"
            missing_plates.mkdir()
            (missing_plates / "anchor.png").write_bytes(
                (
                    worktree
                    / "datasets/content_briefs/lf004-operator-dogfood/plates/anchor.png"
                ).read_bytes()
            )
            assert not missing_output.exists()
            _fail_with_content_brief_error(
                "--brief",
                "datasets/content_briefs/lf004-operator-dogfood-56f/brief.json",
                "--plates",
                str(missing_plates),
                "--output",
                str(missing_output / "plan.json"),
                "--run-dir",
                str(missing_output / "run"),
                cwd=worktree,
                env=env,
                expected="missing plate for 'Tess'",
            )
            assert not missing_output.exists()
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree)],
                cwd=ROOT,
                check=False,
                capture_output=True,
            )
            subprocess.run(
                ["git", "worktree", "prune"],
                cwd=ROOT,
                check=False,
                capture_output=True,
            )
