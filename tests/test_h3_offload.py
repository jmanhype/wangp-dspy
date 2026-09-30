"""Focused local WD-cuzw authorization, preflight, move, and evidence tests."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import pytest

import scripts.run_h3_offload as runner


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION = ROOT / "datasets/runs/maestro-parity/h3-offload/operator-authorization.json"
SCRIPT = ROOT / "scripts/run_h3_offload.py"


def _record() -> dict[str, Any]:
    return json.loads(AUTHORIZATION.read_text(encoding="utf-8"))


def _typed(record: dict[str, Any], mutate: Callable[[dict[str, Any]], None]) -> runner.H3OffloadError:
    value = copy.deepcopy(record)
    mutate(value)
    with pytest.raises(runner.H3OffloadError) as raised:
        runner.verify_authorization(value)
    return raised.value


def test_authorization_binds_exact_two_candidates_and_total() -> None:
    record = _record()
    assert runner.verify_authorization(record) == {
        item["id"]: item for item in runner.EXPECTED_CANDIDATES
    }
    assert sum(item["size_bytes"] for item in record["candidates"]) == runner.COMBINED_BYTES
    assert record["authorization"]["record"]["verbatim"] == "Approved authorized"
    assert record["downstream_authority"]["h3_retry"] is False
    assert record["downstream_authority"]["ltx_download"] is False


def test_authorization_rejects_tampering_third_path_and_wrong_host() -> None:
    record = _record()
    cases = (
        ("H3_AUTHORIZATION_HOST_MISMATCH", lambda value: value.update(host="other")),
        ("H3_AUTHORIZATION_PATH_MISMATCH", lambda value: value.update(offload_root="/other/root")),
        ("H3_AUTHORIZATION_TOTAL_MISMATCH", lambda value: value.update(combined_recovery_bytes=1)),
        ("H3_AUTHORIZATION_VERBATIM_MISMATCH", lambda value: value["authorization"]["record"].update(verbatim="no")),
        ("H3_AUTHORIZATION_CANDIDATES_MISMATCH", lambda value: value["candidates"][0].update(size_bytes=1)),
        ("H3_AUTHORIZATION_BOUNDARY_MISMATCH", lambda value: value["execution"].update(deletion=True)),
    )
    for code, mutate in cases:
        assert _typed(record, mutate).code == code

    third = copy.deepcopy(record)
    third["candidates"].append(dict(third["candidates"][0], id="third", source="/unauthorized"))
    with pytest.raises(runner.H3OffloadError) as raised:
        runner.verify_authorization(third)
    assert raised.value.code in {"H3_AUTHORIZATION_CANDIDATES_INVALID", "H3_AUTHORIZATION_CANDIDATES_MISMATCH"}


class StaticProbeHost:
    def __init__(self, facts: dict[str, Any], *, target: str = "3090", mount: str = "/mnt/bulk-hdd systemd-1 autofs\n/mnt/bulk-hdd /dev/sda4 ext4\n") -> None:
        self.target = target
        self.facts = facts
        self.mount = mount
        self.calls = 0

    def run_probe(self, argv: list[str], timeout: int = 30) -> tuple[int, str, str]:
        self.calls += 1
        if argv[0] == "findmnt":
            return 0, self.mount, ""
        return 0, json.dumps(self.facts, sort_keys=True), ""

    def push_file(self, local: str, remote: str) -> str:
        raise AssertionError("preflight must not stage or mutate")

    def run_argv(self, cmd: list[str], *, cwd: str, timeout: int) -> Any:
        raise AssertionError("preflight must not execute a mutation script")


def _facts(**changes: Any) -> dict[str, Any]:
    source = {"exists": True, "type": "regular_file", "symlink": False, "device": 11, "size_bytes": 22_144_108_396, "writable": True, "sha256": "a" * 64}
    second = dict(source, size_bytes=22_144_108_397, sha256="b" * 64)
    parent = {"exists": True, "type": "directory", "symlink": False, "device": 22, "size_bytes": 96, "writable": True}
    value: dict[str, Any] = {
        "host": "authorized-host", "user": "straughter",
        "candidates": {"superseded-h3-checkpoint-1": source, "superseded-h3-checkpoint-2": second},
        "destinations": {
            "superseded-h3-checkpoint-1": {"exists": False},
            "superseded-h3-checkpoint-2": {"exists": False},
        },
        "root": {"exists": False}, "root_nearest_parent": parent,
        "root_contained": True, "root_free_bytes": runner.COMBINED_BYTES + runner.MARGIN_BYTES,
        "resolved_bulk": "/mnt/bulk-hdd", "resolved_root_parent": "/mnt/bulk-hdd",
        "bulk": {"device": 22, "free_bytes": runner.COMBINED_BYTES + runner.MARGIN_BYTES},
        "source_filesystem_free_bytes": 100,
        "script": {"exists": False},
    }
    for key, item in changes.items():
        value[key] = item
    return value


def test_preflight_passes_read_only_facts_and_rejects_each_fail_closed_boundary() -> None:
    record = _record()
    host = StaticProbeHost(_facts())
    result = runner.preflight(ROOT, record, host)
    assert result["status"] == "passed" and result["mutation"] is False
    assert result["required_bulk_free_bytes"] == 45_361_958_617
    assert result["candidates"]["superseded-h3-checkpoint-1"]["sha256"] == "a" * 64
    assert host.push_file.__name__ == "push_file"

    wrong_host = StaticProbeHost(_facts(), target="other")
    with pytest.raises(runner.H3OffloadError) as raised:
        runner.preflight(ROOT, record, wrong_host)
    assert raised.value.code == "H3_HOST_IDENTITY_MISMATCH"

    cases = {
        "H3_SOURCE_TYPE_INVALID": _facts(candidates={"superseded-h3-checkpoint-1": {"exists": False}, "superseded-h3-checkpoint-2": _facts()["candidates"]["superseded-h3-checkpoint-2"]}),
        "H3_SOURCE_TYPE_INVALID": _facts(candidates={"superseded-h3-checkpoint-1": dict(_facts()["candidates"]["superseded-h3-checkpoint-1"], symlink=True), "superseded-h3-checkpoint-2": _facts()["candidates"]["superseded-h3-checkpoint-2"]}),
        "H3_SOURCE_SIZE_MISMATCH": _facts(candidates={"superseded-h3-checkpoint-1": dict(_facts()["candidates"]["superseded-h3-checkpoint-1"], size_bytes=1), "superseded-h3-checkpoint-2": _facts()["candidates"]["superseded-h3-checkpoint-2"]}),
        "H3_DESTINATION_COLLISION": _facts(destinations={"superseded-h3-checkpoint-1": {"exists": True}, "superseded-h3-checkpoint-2": {"exists": False}}),
        "H3_FREE_SPACE_INSUFFICIENT": _facts(bulk={"device": 22, "free_bytes": 1}),
        "H3_ROOT_CONTAINMENT_INVALID": _facts(root_contained=False),
        "H3_SCRIPT_IDENTITY_INVALID": _facts(script={"exists": True}),
    }
    for code, facts in cases.items():
        with pytest.raises(runner.H3OffloadError) as raised:
            runner.preflight(ROOT, record, StaticProbeHost(facts))
        assert raised.value.code == code

    absent = _facts(candidates={
        "superseded-h3-checkpoint-1": {"exists": False},
        "superseded-h3-checkpoint-2": _facts()["candidates"]["superseded-h3-checkpoint-2"],
    })
    with pytest.raises(runner.H3OffloadError) as raised:
        runner.preflight(ROOT, record, StaticProbeHost(absent))
    assert raised.value.code == "H3_SOURCE_TYPE_INVALID"

    ambiguous_mount = StaticProbeHost(_facts(), mount="/mnt/bulk-hdd a b\n/mnt/bulk-hdd c d\n")
    with pytest.raises(runner.H3OffloadError) as raised:
        runner.preflight(ROOT, record, ambiguous_mount)
    assert raised.value.code == "H3_ROOT_CONTAINMENT_INVALID"

    nested_over_root = StaticProbeHost(
        _facts(),
        mount="/mnt/bulk-hdd /dev/sda4 ext4\n/mnt/bulk-hdd/straughter/model-offload /dev/sda4[/model] ext4\n",
    )
    with pytest.raises(runner.H3OffloadError) as raised:
        runner.preflight(ROOT, record, nested_over_root)
    assert raised.value.code == "H3_ROOT_CONTAINMENT_INVALID"


def test_final_adjudicated_autofs_namespace_passes_and_all_other_shapes_fail() -> None:
    record = _record()
    final_shape = "/mnt/bulk-hdd systemd-1 autofs\n/mnt/bulk-hdd /dev/sda4 ext4\n"
    result = runner.preflight(ROOT, record, StaticProbeHost(_facts(), mount=final_shape))
    assert result["mount"]["source"] == "/dev/sda4"
    assert result["mount"]["filesystem_type"] == "ext4"
    assert result["mount"]["namespace"] == [
        {"target": "/mnt/bulk-hdd", "source": "systemd-1", "filesystem_type": "autofs"},
        {"target": "/mnt/bulk-hdd", "source": "/dev/sda4", "filesystem_type": "ext4"},
    ]
    assert result["root_containment"] == {
        "resolved_bulk": "/mnt/bulk-hdd",
        "resolved_root_parent": "/mnt/bulk-hdd",
    }

    rejected_shapes = {
        "duplicate": final_shape + "/mnt/bulk-hdd /dev/sda5 ext4\n",
        "foreign": "/mnt/bulk-hdd systemd-1 autofs\n/mnt/bulk-hdd /dev/other ext4\n",
        "autofs-only": "/mnt/bulk-hdd systemd-1 autofs\n",
        "ambiguous": "/mnt/bulk-hdd /dev/sda4 ext4\n/mnt/bulk-hdd /dev/sda4 xfs\n",
        "foreign-target": "/other systemd-1 autofs\n/mnt/bulk-hdd /dev/sda4 ext4\n",
    }
    for shape in rejected_shapes.values():
        with pytest.raises(runner.H3OffloadError) as raised:
            runner.preflight(ROOT, record, StaticProbeHost(_facts(), mount=shape))
        assert raised.value.code == "H3_ROOT_CONTAINMENT_INVALID"

    escaped_root = _facts(resolved_root_parent="/other/root")
    with pytest.raises(runner.H3OffloadError) as raised:
        runner.preflight(ROOT, record, StaticProbeHost(escaped_root, mount=final_shape))
    assert raised.value.code == "H3_ROOT_CONTAINMENT_INVALID"


def test_repository_identity_uses_real_git_branch_argv(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "authorization.json").write_text("{}\n", encoding="utf-8")
    commands = (
        ["git", "-C", str(repository), "init", "-b", "story/WD-cuzw"],
        ["git", "-C", str(repository), "add", "authorization.json"],
        ["git", "-C", str(repository), "-c", "user.name=WD-cuzw", "-c", "user.email=dev@example.invalid", "commit", "-m", "identity fixture"],
    )
    for command in commands:
        assert subprocess.run(command, text=True, capture_output=True, timeout=30, check=True).returncode == 0
    identity = runner._repository_identity(repository)
    assert identity["branch"] == "story/WD-cuzw"
    assert identity["commit"] == subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"], text=True, capture_output=True, check=True
    ).stdout.strip()


def test_only_the_exact_archived_boundary_is_not_current_evidence(tmp_path: Path) -> None:
    bundle = tmp_path / "host-run"
    archived = bundle / "boundary-attempts/20260930T210821Z"
    archived.mkdir(parents=True)
    for name in ("attempt.json", "failure.json", "evidence.sha256"):
        (archived / name).write_text(name + "\n", encoding="utf-8")
    assert runner._has_current_evidence(bundle) is False

    current = tmp_path / "current-run"
    current.mkdir()
    (current / "run-summary.json").write_text("{}\n", encoding="utf-8")
    assert runner._has_current_evidence(current) is True
    malformed = tmp_path / "malformed-run/boundary-attempts/20260930T210821Z"
    malformed.mkdir(parents=True)
    (malformed / "unexpected").write_text("partial\n", encoding="utf-8")
    assert runner._has_current_evidence(malformed.parent.parent) is True


def _translated_script(path: Path, *, fail_after_first: bool = False, rollback_collision: bool = False) -> tuple[Path, dict[str, Path], dict[str, Path]]:
    home = path / "home/straughter/Wan2GP/ckpts"
    bulk = path / "mnt/bulk-hdd"
    home.mkdir(parents=True)
    bulk.mkdir(parents=True)
    first, second = home / "MiniMax-H3-FL2VA-pruned_int8_convrot.safetensors", home / "MiniMax-H3-Ref2VA-pruned_int8_convrot.safetensors"
    first.write_bytes(b"first-checkpoint-bytes")
    second.write_bytes(b"second-checkpoint-bytes")
    root = bulk / "straughter/model-offload/wangp-3090"
    text = runner._offload_script(list(runner.EXPECTED_CANDIDATES))
    placeholders = {
        runner.EXPECTED_CANDIDATES[0]["source"]: str(first),
        runner.EXPECTED_CANDIDATES[1]["source"]: str(second),
        runner.EXPECTED_CANDIDATES[0]["destination"]: str(root / first.name),
        runner.EXPECTED_CANDIDATES[1]["destination"]: str(root / second.name),
        runner.OFFLOAD_ROOT: str(root),
        runner.BULK_MOUNT: str(bulk),
        runner.SOURCE_FILESYSTEM: str(path / "home/straughter/Wan2GP"),
    }
    tokens = {value: f"__WD_CUZW_{index}__" for index, value in enumerate(placeholders)}
    for old, token in tokens.items():
        text = text.replace(old, token)
    for old, token in tokens.items():
        text = text.replace(token, placeholders[old])
    replacements = {
        "__WD_CUZW_ROOT__": str(root), "__WD_CUZW_BULK__": str(bulk),
        "__WD_CUZW_SOURCE_FS__": str(path / "home/straughter/Wan2GP"),
        str(runner.EXPECTED_CANDIDATES[0]["size_bytes"]): str(first.stat().st_size),
        str(runner.EXPECTED_CANDIDATES[1]["size_bytes"]): str(second.stat().st_size),
        "53687091200": "10", "1073741824": "10",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # macOS gives distinct st_dev values to paths on its synthetic mount layer;
    # local tests retain lexical containment while retaining the Linux device check.
    text = text.replace('facts(nearest)["device"] != bulk["device"]', "False")
    text = text.replace('root_fact["device"] != facts(BULK)["device"]', "False")
    if fail_after_first:
        injection = "open(candidate['source'], 'wb').close(); raise OSError('rollback collision')" if rollback_collision else "raise OSError('injected post-first-move failure')"
        text = text.replace("        # POST_MOVE_BOUNDARY", "        " + injection, 1)
    local = path / "translated-offload.sh"
    local.write_text(text, encoding="utf-8")
    return local, {first.name: first for first in (first, second)}, {first.name: root / first.name for first in (first, second)}


def _run_script(path: Path) -> dict[str, Any]:
    result = subprocess.run(["/bin/sh", str(path)], cwd="/", text=True, capture_output=True, timeout=120, check=False)
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 1
    return json.loads(lines[0])


def test_generated_script_is_syntax_safe_and_moves_exactly_two_files(tmp_path: Path) -> None:
    original = runner._offload_script(list(runner.EXPECTED_CANDIDATES))
    syntax = subprocess.run(["/bin/sh", "-n", "/dev/stdin"], input=original, text=True, capture_output=True, timeout=30, check=False)
    assert syntax.returncode == 0, syntax.stderr
    for forbidden in ("rm ", "ln ", "sudo ", "curl ", "wget ", "nvidia-smi", "truncate "):
        assert forbidden not in original
    assert original.count("result = move_no_clobber(") == 2

    script, sources, destinations = _translated_script(tmp_path)
    result = _run_script(script)
    assert result["status"] == "offloaded" and len(result["moved"]) == 2
    assert result["doctor_floor_met"] is True
    for name, source in sources.items():
        assert not source.exists()
        assert destinations[name].is_file()
        observed = destinations[name].read_bytes()
        record = next(item for item in result["moved"] if item["source"].endswith(name))
        assert record["pre_sha256"] == record["post_sha256"] == hashlib.sha256(observed).hexdigest()
        assert record["post_size_bytes"] == len(observed)


def test_collision_and_partial_failure_rollback_are_fail_closed(tmp_path: Path) -> None:
    script, sources, destinations = _translated_script(tmp_path)
    destinations[next(iter(destinations))].parent.mkdir(parents=True, exist_ok=True)
    first_destination = next(iter(destinations.values()))
    first_destination.write_bytes(b"existing collision")
    before = first_destination.read_bytes()
    result = _run_script(script)
    assert result["status"] == "rolled_back" and result["moved_before_failure"] == []
    assert first_destination.read_bytes() == before
    assert all(source.exists() for source in sources.values())

    rollback_root = tmp_path / "rollback"
    script, sources, destinations = _translated_script(rollback_root, fail_after_first=True)
    result = _run_script(script)
    assert result["status"] == "rolled_back"
    assert result["rollback"]["state"] == "completed" and result["rollback"]["outcomes"][0]["verified"] is True
    assert sources["MiniMax-H3-FL2VA-pruned_int8_convrot.safetensors"].exists()
    assert not destinations["MiniMax-H3-FL2VA-pruned_int8_convrot.safetensors"].exists()
    assert sources["MiniMax-H3-Ref2VA-pruned_int8_convrot.safetensors"].exists()


def test_rollback_failure_is_critical_and_not_retried(tmp_path: Path) -> None:
    script, sources, destinations = _translated_script(tmp_path, fail_after_first=True, rollback_collision=True)
    result = _run_script(script)
    assert result["status"] == "rollback_failed"
    assert result["rollback"]["state"] == "failed"
    assert result["rollback"]["outcomes"][0]["verified"] is False
    assert destinations["MiniMax-H3-FL2VA-pruned_int8_convrot.safetensors"].exists()
    assert sources["MiniMax-H3-Ref2VA-pruned_int8_convrot.safetensors"].exists()


def test_evidence_manifest_is_complete_and_cli_never_contacts_external_binaries(tmp_path: Path) -> None:
    bundle = tmp_path / "host-run"
    bundle.mkdir()
    (bundle / "preflight.json").write_text("{}\n", encoding="utf-8")
    (bundle / "offload-script.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    manifest = runner._manifest(bundle)
    assert [item["path"] for item in manifest["files"]] == ["offload-script.sh", "preflight.json"]
    for item in manifest["files"]:
        path = bundle / item["path"]
        assert item["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()

    forbidden = tmp_path / "forbidden-bin"
    forbidden.mkdir()
    calls = tmp_path / "calls.log"
    calls.write_text("", encoding="utf-8")
    for name in ("ssh", "scp", "rsync", "curl", "wget", "nvidia-smi"):
        command = forbidden / name
        command.write_text(f'#!/bin/sh\nprintf "%s\\n" "{name}" >> {calls}\n', encoding="utf-8")
        command.chmod(0o755)
    environment = os.environ.copy()
    environment["PATH"] = f"{forbidden}:{environment['PATH']}"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(ROOT), "--authorization", str(AUTHORIZATION)],
        cwd=ROOT, env=environment, text=True, capture_output=True, timeout=120, check=False,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["mutation"] is False
    assert calls.read_text(encoding="utf-8") == ""
