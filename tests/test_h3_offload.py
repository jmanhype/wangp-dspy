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
from host.render_host import SshHost


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION = ROOT / "datasets/runs/maestro-parity/h3-offload/operator-authorization.json"
SCRIPT = ROOT / "scripts/run_h3_offload.py"


class _FakeProcess:
    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode

    def communicate(self):
        return b"", b""


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
        ("H3_AUTHORIZATION_PATH_MISMATCH", lambda value: value.update(local_destination_root="/other/root")),
        ("H3_AUTHORIZATION_TOTAL_MISMATCH", lambda value: value.update(combined_recovery_bytes=1)),
        ("H3_AUTHORIZATION_VERBATIM_MISMATCH", lambda value: value["authorization"]["record"].update(verbatim="no")),
        ("H3_AUTHORIZATION_CANDIDATES_MISMATCH", lambda value: value["candidates"][0].update(size_bytes=1)),
        ("H3_AUTHORIZATION_BOUNDARY_MISMATCH", lambda value: value["execution"].update(deletion=True)),
        ("H3_AUTHORIZATION_PROTECTED_FILE_MISMATCH", lambda value: value["protected_existing_files"][0].update(size_bytes=1)),
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

    def fetch_file_partial(self, remote: str, local: str) -> str:
        raise AssertionError("preflight must not transfer")

    def unlink_verified_file(self, remote: str, *, expected_size_bytes: int, expected_sha256: str) -> str:
        raise AssertionError("preflight must not free a source")


def _facts(**changes: Any) -> dict[str, Any]:
    source = {"exists": True, "type": "regular_file", "symlink": False, "device": 11, "size_bytes": 22_144_108_396, "writable": True, "sha256": "a" * 64}
    second = dict(source, size_bytes=22_144_108_397, sha256="b" * 64)
    parent = {"exists": True, "type": "directory", "symlink": False, "device": 22, "size_bytes": 96, "writable": True}
    value: dict[str, Any] = {
        "host": "authorized-host", "user": "straughter",
        "candidates": {"superseded-h3-checkpoint-1": source, "superseded-h3-checkpoint-2": second},
        "source_filesystem_free_bytes": runner.COMBINED_BYTES,
    }
    for key, item in changes.items():
        value[key] = item
    return value


def _destination(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, record: dict[str, Any]) -> Path:
    root = tmp_path / "model-offload"
    root.mkdir(parents=True)
    protected = root / "MiniMax-H3-FL2VA_int8_convrot.safetensors"
    protected.write_bytes(b"abc")
    record["protected_existing_files"][0]["size_bytes"] = protected.stat().st_size
    record["local_destination_root"] = root.as_posix()
    monkeypatch.setattr(runner, "PROTECTED_FILES", tuple(dict(item) for item in record["protected_existing_files"]))
    monkeypatch.setattr(runner, "DESTINATION_ROOT", root)
    return root


def test_preflight_verifies_remote_sources_local_capacity_and_protected_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _record()
    root = _destination(tmp_path, monkeypatch, record)
    for item in record["candidates"]:
        item["size_bytes"] = 100
    record["combined_recovery_bytes"] = 200
    record["local_capacity_margin_bytes"] = 1
    monkeypatch.setattr(runner, "EXPECTED_CANDIDATES", tuple(dict(item) for item in record["candidates"]))
    monkeypatch.setattr(runner, "COMBINED_BYTES", 200)
    monkeypatch.setattr(runner, "MARGIN_BYTES", 1)
    facts = _facts()
    for value in facts["candidates"].values():
        value["size_bytes"] = 100
    result = runner.preflight(ROOT, record, StaticProbeHost(facts))
    assert result["status"] == "passed" and result["mutation"] is False
    assert result["local_destination"]["root"].startswith(root.as_posix())
    assert result["local_destination"]["protected_existing_files"][0]["size_bytes"] == 3
    assert result["candidates"]["superseded-h3-checkpoint-1"]["sha256"] == "a" * 64

    wrong_host = StaticProbeHost(facts, target="other")
    with pytest.raises(runner.H3OffloadError) as raised:
        runner.preflight(ROOT, record, wrong_host)
    assert raised.value.code == "H3_HOST_IDENTITY_MISMATCH"

    base = facts
    remote_cases = {
        "H3_SOURCE_TYPE_INVALID": _facts(candidates={
            "superseded-h3-checkpoint-1": {"exists": False},
            "superseded-h3-checkpoint-2": base["candidates"]["superseded-h3-checkpoint-2"],
        }),
        "H3_SOURCE_SIZE_MISMATCH": _facts(candidates={
            "superseded-h3-checkpoint-1": dict(base["candidates"]["superseded-h3-checkpoint-1"], size_bytes=1),
            "superseded-h3-checkpoint-2": base["candidates"]["superseded-h3-checkpoint-2"],
        }),
        "H3_SOURCE_HASH_INVALID": _facts(candidates={
            "superseded-h3-checkpoint-1": dict(base["candidates"]["superseded-h3-checkpoint-1"], sha256=None),
            "superseded-h3-checkpoint-2": base["candidates"]["superseded-h3-checkpoint-2"],
        }),
    }
    for code, case_facts in remote_cases.items():
        with pytest.raises(runner.H3OffloadError) as raised:
            runner.preflight(ROOT, record, StaticProbeHost(case_facts))
        assert raised.value.code == code

    (root / runner.EXPECTED_CANDIDATES[0]["destination"].rsplit("/", 1)[-1]).write_bytes(b"collision")
    with pytest.raises(runner.H3OffloadError) as raised:
        runner.preflight(ROOT, record, StaticProbeHost(facts))
    assert raised.value.code == "H3_DESTINATION_COLLISION"


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


def test_local_preflight_rejects_capacity_protected_and_unexpected_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _record()
    root = _destination(tmp_path, monkeypatch, record)
    monkeypatch.setattr(runner, "MARGIN_BYTES", 10**15)
    record["local_capacity_margin_bytes"] = runner.MARGIN_BYTES
    with pytest.raises(runner.H3OffloadError) as raised:
        runner._local_destination_preflight(root, record)
    assert raised.value.code == "H3_LOCAL_CAPACITY_INSUFFICIENT"

    monkeypatch.setattr(runner, "MARGIN_BYTES", 1)
    record["local_capacity_margin_bytes"] = 1
    protected = root / "MiniMax-H3-FL2VA_int8_convrot.safetensors"
    protected.write_bytes(b"abcd")
    with pytest.raises(runner.H3OffloadError) as raised:
        runner._local_destination_preflight(root, record)
    assert raised.value.code == "H3_PROTECTED_FILE_INVALID"


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

    four_file = tmp_path / "four-file-run/boundary-attempts/20261001T201056Z"
    four_file.mkdir(parents=True)
    for name in ("attempt.json", "preflight.json", "failure.json", "evidence.sha256"):
        (four_file / name).write_text(name + "\n", encoding="utf-8")
    assert runner._has_current_evidence(four_file.parent.parent) is False


class TransferHost:
    target = "3090"

    def __init__(self, sources: dict[str, Path], *, corrupt_second: bool = False, fail_first_free: bool = False) -> None:
        self.sources = sources
        self.corrupt_second = corrupt_second
        self.fail_first_free = fail_first_free
        self.fetch_order: list[str] = []
        self.free_order: list[str] = []

    def _hash(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def run_probe(self, argv: list[str], timeout: int = 30) -> tuple[int, str, str]:
        payload = json.loads(argv[4])
        if argv[2] == runner._REMOTE_POSTFREE_CODE:
            candidates = {
                item["id"]: {"source_exists": self.sources[item["source"]].exists(), "source_is_symlink": self.sources[item["source"]].is_symlink()}
                for item in payload["candidates"]
            }
            return 0, json.dumps({"source_filesystem_free_bytes": 100, "candidates": candidates}), ""
        candidates = {}
        for item in payload["candidates"]:
            path = self.sources[item["source"]]
            candidates[item["id"]] = {
                "exists": path.exists(), "type": "regular_file" if path.is_file() else "other",
                "symlink": path.is_symlink(), "size_bytes": path.stat().st_size,
                "sha256": self._hash(path),
            }
        return 0, json.dumps({
            "host": "authorized-host", "user": "straughter",
            "source_filesystem_free_bytes": 100, "candidates": candidates,
        }), ""

    def fetch_file_partial(self, remote: str, local: str) -> str:
        self.fetch_order.append(remote)
        data = self.sources[remote].read_bytes()
        if self.corrupt_second and remote.endswith("Ref2VA-pruned_int8_convrot.safetensors"):
            data += b"mismatch"
        Path(local).write_bytes(data)
        return local

    def unlink_verified_file(self, remote: str, *, expected_size_bytes: int, expected_sha256: str) -> str:
        if self.fail_first_free:
            raise RuntimeError("governed free failed")
        path = self.sources[remote]
        assert path.stat().st_size == expected_size_bytes
        assert self._hash(path) == expected_sha256
        path.unlink()
        self.free_order.append(remote)
        return remote


def _small_transfer_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, Any], Path, dict[str, Path], TransferHost]:
    record = _record()
    source_dir = tmp_path / "remote"
    source_dir.mkdir()
    sources: dict[str, Path] = {}
    for item in record["candidates"]:
        path = source_dir / Path(str(item["destination"])).name
        path.write_bytes(item["id"].encode())
        item["size_bytes"] = path.stat().st_size
        item["source"] = item["source"]
        sources[item["source"]] = path
    record["combined_recovery_bytes"] = sum(item["size_bytes"] for item in record["candidates"])
    record["local_capacity_margin_bytes"] = 1
    monkeypatch.setattr(runner, "EXPECTED_CANDIDATES", tuple(dict(item) for item in record["candidates"]))
    monkeypatch.setattr(runner, "COMBINED_BYTES", record["combined_recovery_bytes"])
    monkeypatch.setattr(runner, "MARGIN_BYTES", 1)
    root = _destination(tmp_path / "local", monkeypatch, record)
    host = TransferHost(sources)
    return record, root, sources, host


def test_sequential_transfer_promotes_parts_and_frees_only_after_both_verified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record, root, sources, host = _small_transfer_fixture(tmp_path, monkeypatch)
    bundle = tmp_path / "host-run"
    bundle.mkdir()
    state: dict[str, object] = {"transfers": [], "frees": []}
    remote = json.loads(host.run_probe([
        "python3", "-c", runner._REMOTE_PREFLIGHT_CODE, "wd-cuzw-h3-offload",
        json.dumps({"candidates": record["candidates"], "source_filesystem": runner.SOURCE_FILESYSTEM}),
    ])[1])["candidates"]
    result = runner._transfer_and_free(root, record, host, bundle, state, remote)
    assert result["status"] == "offloaded_and_remote_sources_freed"
    protected_path = root / "MiniMax-H3-FL2VA_int8_convrot.safetensors"
    assert protected_path.read_bytes() == b"abc"
    assert host.fetch_order == [str(item["source"]) for item in record["candidates"]]
    assert host.free_order == host.fetch_order
    assert all(not path.exists() for path in sources.values())
    assert all(not (root / (Path(str(item["destination"])).name + ".part")).exists() for item in record["candidates"])
    assert all((root / Path(str(item["destination"])).name).is_file() for item in record["candidates"])
    restoration = runner._restoration_state(root, record, state)
    assert all(item["local_copy_present"] and item["remote_source_freed"] for item in restoration)


def test_transfer_mismatch_preserves_local_and_remote_state_without_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record, root, sources, _ = _small_transfer_fixture(tmp_path, monkeypatch)
    host = TransferHost({key: value for key, value in _.sources.items()}, corrupt_second=True)
    bundle = tmp_path / "host-run"
    bundle.mkdir()
    state: dict[str, object] = {"transfers": [], "frees": []}
    remote = {
        record["candidates"][0]["id"]: {"sha256": hashlib.sha256(sources[record["candidates"][0]["source"]].read_bytes()).hexdigest()},
        record["candidates"][1]["id"]: {"sha256": "a" * 64},
    }
    with pytest.raises(runner.H3OffloadError) as raised:
        runner._transfer_and_free(root, record, host, bundle, state, remote)
    assert raised.value.code == "H3_PART_TRANSFER_MISMATCH"
    assert host.free_order == []
    assert all(path.exists() for path in sources.values())
    assert (root / (Path(str(record["candidates"][0]["destination"])).name)).is_file()
    assert (root / (Path(str(record["candidates"][1]["destination"])).name + ".part")).is_file()


def test_governed_free_failure_preserves_both_verified_copies_and_stops(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record, root, sources, _ = _small_transfer_fixture(tmp_path, monkeypatch)
    host = TransferHost({key: value for key, value in _.sources.items()}, fail_first_free=True)
    bundle = tmp_path / "host-run"
    bundle.mkdir()
    state: dict[str, object] = {"transfers": [], "frees": []}
    remote = {}
    for item in record["candidates"]:
        remote[item["id"]] = {"sha256": hashlib.sha256(sources[item["source"]].read_bytes()).hexdigest()}
    with pytest.raises(RuntimeError) as raised:
        runner._transfer_and_free(root, record, host, bundle, state, remote)
    assert str(raised.value) == "governed free failed"
    assert all(path.exists() for path in sources.values())
    assert all((root / Path(str(item["destination"])).name).is_file() for item in record["candidates"])


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


def test_ssh_host_partial_fetch_uses_openrsync_269_compatible_argv(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def sp(argv, **_kwargs):
        calls.append(list(argv))
        return _FakeProcess()

    host = SshHost(target="3090", wgp_root="/remote/wgp", pull_root=str(tmp_path / "pull"), sp=sp)
    local = tmp_path / "destination/model.part"
    assert host.fetch_file_partial("/remote/source.safetensors", str(local)) == str(local)
    assert calls == [[
        "rsync", "-a", "--partial", "--inplace", "--append",
        "3090:/remote/source.safetensors", str(local),
    ]]
    assert "--append-verify" not in calls[0]
    assert local.parent == (tmp_path / "destination")


def test_ssh_host_verified_free_uses_structured_host_seam(tmp_path: Path) -> None:
    commands: list[tuple[list[str], str, int]] = []

    class RecordingHost(SshHost):
        def run_argv(self, cmd, *, cwd, timeout):
            commands.append((list(cmd), cwd, timeout))
            return subprocess.CompletedProcess(cmd, 0, "", "")

    host = RecordingHost(target="3090", wgp_root="/remote/wgp", pull_root=str(tmp_path / "pull"))
    result = host.unlink_verified_file(
        "/remote/source.safetensors",
        expected_size_bytes=123,
        expected_sha256="a" * 64,
    )
    assert result == "/remote/source.safetensors"
    assert len(commands) == 1
    command, cwd, timeout = commands[0]
    assert command[:2] == ["python3", "-c"]
    assert command[3:5] == ["wd-cuzw-verified-unlink", "/remote/source.safetensors"]
    assert command[5] == "123"
    assert "a" * 64 in command
    assert cwd == "/" and timeout == 3600
