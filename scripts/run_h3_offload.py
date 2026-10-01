#!/usr/bin/env python3
"""Authorized, reversible, one-attempt H3 checkpoint offload runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence


AUTH_SCHEMA = "wangp-dspy.h3-offload-authorization/v2"
RUN_SCHEMA = "wangp-dspy.h3-offload-run/v1"
BUNDLE_RELATIVE = Path("datasets/runs/maestro-parity/h3-offload/host-run")
AUTHORIZATION_RELATIVE = Path("datasets/runs/maestro-parity/h3-offload/operator-authorization.json")
_AUTHORIZED_TEMPLATE = json.loads((Path(__file__).resolve().parents[1] / AUTHORIZATION_RELATIVE).read_text(encoding="utf-8"))
HOST = str(_AUTHORIZED_TEMPLATE["host"])
WGP_ROOT = str(_AUTHORIZED_TEMPLATE["source_filesystem"])
DESTINATION_ROOT = Path(str(_AUTHORIZED_TEMPLATE["local_destination_root"]))
SOURCE_FILESYSTEM = WGP_ROOT
COMBINED_BYTES = 44_288_216_793
MARGIN_BYTES = int(_AUTHORIZED_TEMPLATE["local_capacity_margin_bytes"])
DOCTOR_FLOOR_BYTES = 53_687_091_200
VERBATIM = "Approved authorized"
APPROVED_AT = "2026-09-30T19:57:10Z"
DESTINATION_VERBATIM = "You decide."
DESTINATION_DECIDED_AT = "2026-10-01T19:00:26Z"
REQUIRED_SCOPE = (
    "reversible offload of exactly the two superseded H3 checkpoints on host 3090, "
    "with live size/SHA verification, a reversible recovery path, and no deletion"
)
EXECUTION_BOUNDARY = {
    "sequential_transfer": True, "resumable_part_transfer": True,
    "atomic_promotion": True, "verify_both_copies_before_free": True,
    "free_verified_remote_source": True, "deletion": False,
    "hard_link": False, "symlink": False, "rewrite": False,
    "privileged_command": False, "download": False, "gpu_work": False,
    "provider_spend": False, "queue_admission": False,
}
DOWNSTREAM_AUTHORITY = {
    "h3_retry": False, "ltx_download": False, "inference": False,
    "generation_claim": False, "hardware_verdict": False,
    "capability_promotion": False,
}
EXPECTED_CANDIDATES: tuple[dict[str, object], ...] = tuple(dict(item) for item in _AUTHORIZED_TEMPLATE["candidates"])
PROTECTED_FILES: tuple[dict[str, object], ...] = tuple(dict(item) for item in _AUTHORIZED_TEMPLATE["protected_existing_files"])


class H3OffloadError(ValueError):
    """Typed fail-closed H3 offload boundary."""

    def __init__(self, code: str, observed: str, remediation: str, *, critical: bool = False) -> None:
        super().__init__(observed)
        self.code = code
        self.observed = observed
        self.remediation = remediation
        self.critical = critical


def _reject(code: str, observed: str, remediation: str, *, critical: bool = False) -> H3OffloadError:
    return H3OffloadError(code, observed, remediation, critical=critical)


# Runtime validation in _host_object enforces this exact seam; the authorized
# CLI constructs the real host.render_host.SshHost rather than a local fake.
SshHostLike = Any


def _require_keys(value: Mapping[str, object], expected: set[str], code: str, label: str) -> None:
    observed = set(value)
    if observed != expected:
        raise _reject(
            code,
            f"{label} keys differ (missing={sorted(expected - observed)}, extra={sorted(observed - expected)})",
            "Supply the exact authorization document without adding or removing fields.",
        )


def _candidate_map(record: Mapping[str, object]) -> dict[str, dict[str, object]]:
    candidates = record.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != len(EXPECTED_CANDIDATES):
        raise _reject("H3_AUTHORIZATION_CANDIDATES_INVALID", "authorization must contain exactly two candidates", "Bind only the two named superseded checkpoints.")
    result: dict[str, dict[str, object]] = {}
    for item in candidates:
        if not isinstance(item, dict):
            raise _reject("H3_AUTHORIZATION_CANDIDATES_INVALID", "candidate is not an object", "Use the exact candidate object schema.")
        _require_keys(item, {"id", "source", "destination", "size_bytes"}, "H3_AUTHORIZATION_CANDIDATES_INVALID", "candidate")
        if not isinstance(item.get("id"), str) or item["id"] in result:
            raise _reject("H3_AUTHORIZATION_CANDIDATES_INVALID", "candidate ids must be unique strings", "Use the two exact candidate ids.")
        result[item["id"]] = dict(item)
    expected = {str(item["id"]): dict(item) for item in EXPECTED_CANDIDATES}
    if result != expected or sum(int(item["size_bytes"]) for item in result.values()) != COMBINED_BYTES:
        raise _reject("H3_AUTHORIZATION_CANDIDATES_MISMATCH", "candidate identities, paths, or sizes differ from authorization", "Bind the exact two source/destination/size triples.")
    return result


def verify_authorization(record: Mapping[str, object]) -> dict[str, dict[str, object]]:
    """Validate the exact operator authorization before any host contact."""
    if not record:
        raise _reject("H3_AUTHORIZATION_ABSENT", "authorization record is absent", "Record the exact operator approval.")
    _require_keys(
        record,
        {"schema_version", "status", "host", "authorization", "candidates", "local_destination_root", "source_filesystem", "combined_recovery_bytes", "local_capacity_margin_bytes", "protected_existing_files", "execution", "downstream_authority"},
        "H3_AUTHORIZATION_TAMPERED", "authorization",
    )
    if record.get("schema_version") != AUTH_SCHEMA or record.get("status") != "authorized":
        raise _reject("H3_AUTHORIZATION_TAMPERED", "schema or status is not the exact authorized pair", f"Use {AUTH_SCHEMA} with status=authorized.")
    if record.get("host") != HOST:
        raise _reject("H3_AUTHORIZATION_HOST_MISMATCH", f"authorized host is {record.get('host')!r}", f"Only host {HOST!r} is authorized.")
    if record.get("local_destination_root") != DESTINATION_ROOT.as_posix() or record.get("source_filesystem") != SOURCE_FILESYSTEM:
        raise _reject("H3_AUTHORIZATION_PATH_MISMATCH", "local destination root or source filesystem differs", "Use only the exact authorized paths.")
    if type(record.get("combined_recovery_bytes")) is not int or record.get("combined_recovery_bytes") != COMBINED_BYTES:
        raise _reject("H3_AUTHORIZATION_TOTAL_MISMATCH", f"combined recovery bytes is {record.get('combined_recovery_bytes')!r}", f"Use {COMBINED_BYTES} exactly.")
    if type(record.get("local_capacity_margin_bytes")) is not int or record.get("local_capacity_margin_bytes") != MARGIN_BYTES:
        raise _reject("H3_AUTHORIZATION_CAPACITY_MARGIN_MISMATCH", f"local capacity margin is {record.get('local_capacity_margin_bytes')!r}", f"Use {MARGIN_BYTES} exactly.")
    authorization = record.get("authorization")
    if not isinstance(authorization, dict):
        raise _reject("H3_AUTHORIZATION_PARTIAL", "authorization object is absent", "Record the verbatim approval and scope.")
    _require_keys(authorization, {"required_scope", "record", "destination_decision"}, "H3_AUTHORIZATION_TAMPERED", "authorization")
    if authorization.get("required_scope") != REQUIRED_SCOPE:
        raise _reject("H3_AUTHORIZATION_SCOPE_MISMATCH", "required scope differs", "Record the exact approved storage scope.")
    approval = authorization.get("record")
    if not isinstance(approval, dict):
        raise _reject("H3_AUTHORIZATION_PARTIAL", "operator approval record is absent", "Record the operator, UTC time, and verbatim reply.")
    _require_keys(approval, {"operator", "recorded_utc", "verbatim"}, "H3_AUTHORIZATION_TAMPERED", "operator approval")
    if approval != {"operator": "operator", "recorded_utc": APPROVED_AT, "verbatim": VERBATIM}:
        raise _reject("H3_AUTHORIZATION_VERBATIM_MISMATCH", "operator approval record differs", 'Record exactly "Approved authorized" at 2026-09-30T19:57:10Z.')
    decision = authorization.get("destination_decision")
    if decision != {
        "operator": "operator", "recorded_utc": DESTINATION_DECIDED_AT,
        "verbatim": DESTINATION_VERBATIM,
        "decision": "Use the already-proven ordinary-user local destination for both exact superseded H3 candidates; transfer sequentially with resumable parts, verify both copies before freeing either source, and preserve restoration mappings.",
    }:
        raise _reject("H3_AUTHORIZATION_DESTINATION_DECISION_MISMATCH", "destination decision differs", "Record the corrected 2026-10-01T19:00:26Z operator decision exactly.")
    if record.get("execution") != EXECUTION_BOUNDARY or record.get("downstream_authority") != DOWNSTREAM_AUTHORITY:
        raise _reject("H3_AUTHORIZATION_BOUNDARY_MISMATCH", "execution or downstream authority differs", "All prohibited actions must remain false.")
    if record.get("protected_existing_files") != list(PROTECTED_FILES):
        raise _reject("H3_AUTHORIZATION_PROTECTED_FILE_MISMATCH", "protected existing-file identity differs", "Bind the exact accepted WD-osfm checkpoint and do not alter it.")
    return _candidate_map(record)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _host_object(host: SshHostLike) -> None:
    if getattr(host, "target", None) != HOST:
        raise _reject("H3_HOST_IDENTITY_MISMATCH", f"host seam target is {getattr(host, 'target', None)!r}", f"Use the real SshHost target {HOST!r}.")
    for name in ("run_probe", "fetch_file_partial", "unlink_verified_file"):
        if not callable(getattr(host, name, None)):
            raise _reject("H3_HOST_SEAM_INVALID", f"host seam lacks {name}", "Use host.render_host.SshHost or its exact seam contract.")


def _probe_json(host: SshHostLike, code: str, payload: Mapping[str, object], *, timeout: int) -> dict[str, Any]:
    rc, stdout, stderr = host.run_probe(
        ["python3", "-c", code, "wd-cuzw-h3-offload", json.dumps(payload, sort_keys=True, separators=(",", ":"))],
        timeout=timeout,
    )
    if rc != 0:
        raise _reject("H3_PREFLIGHT_OUTPUT_INVALID", f"remote probe exited {rc}: {stderr.strip()[:500]}", "Stop before mutation; inspect the typed boundary.")
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise _reject("H3_PREFLIGHT_OUTPUT_INVALID", f"remote probe returned invalid JSON: {exc}", "Stop before mutation; do not substitute facts.") from exc
    if not isinstance(value, dict):
        raise _reject("H3_PREFLIGHT_OUTPUT_INVALID", "remote probe JSON root is not an object", "Stop before mutation.")
    return value


_REMOTE_PREFLIGHT_CODE = r'''import hashlib,json,os,stat,sys
p=json.loads(sys.argv[2])
def f(path):
 try:s=os.lstat(path)
 except OSError:return {"exists":False}
 return {"exists":True,"type":"directory" if stat.S_ISDIR(s.st_mode) else "regular_file" if stat.S_ISREG(s.st_mode) else "other","symlink":stat.S_ISLNK(s.st_mode),"size_bytes":s.st_size}
def h(path):
 value=hashlib.sha256()
 with open(path,"rb") as source:
  for block in iter(lambda:source.read(4194304),b""):value.update(block)
 return value.hexdigest()
out={"host":os.uname().nodename,"user":__import__("pwd").getpwuid(os.getuid()).pw_name,"source_filesystem_free_bytes":os.statvfs(p["source_filesystem"]).f_bavail*os.statvfs(p["source_filesystem"]).f_frsize,"candidates":{}}
for item in p["candidates"]:
 value=f(item["source"]);value["sha256"]=h(item["source"]) if value["type"]=="regular_file" and not value["symlink"] else None;out["candidates"][item["id"]]=value
print(json.dumps(out,sort_keys=True,separators=(",",":")))'''

_REMOTE_POSTFREE_CODE = r'''import json,os,sys
p=json.loads(sys.argv[2]);value=os.statvfs(p["source_filesystem"])
out={"source_filesystem_free_bytes":value.f_bavail*value.f_frsize,"candidates":{}}
for item in p["candidates"]:out["candidates"][item["id"]]={"source_exists":os.path.lexists(item["source"]),"source_is_symlink":os.path.islink(item["source"])}
print(json.dumps(out,sort_keys=True,separators=(",",":")))'''


def _candidate_file(destination_root: Path, expected: Mapping[str, object]) -> Path:
    destination = Path(str(expected["destination"]))
    if PurePosixPath(destination).name in {"", ".", ".."}:
        raise _reject("H3_AUTHORIZATION_CANDIDATES_INVALID", f"destination has no safe filename: {destination}", "Use the exact local destination names.")
    return destination_root / destination.name


def _local_destination_preflight(destination_root: Path, record: Mapping[str, object]) -> dict[str, object]:
    candidates = verify_authorization(record)
    root = destination_root.expanduser()
    try:
        root_stat = root.lstat()
    except OSError as exc:
        raise _reject("H3_DESTINATION_ROOT_INVALID", f"local destination root is absent: {root}: {exc}", "Stop; no alternate root or creation is authorized.") from exc
    if not root.is_dir() or root.is_symlink() or not os.access(root, os.W_OK):
        raise _reject("H3_DESTINATION_ROOT_INVALID", f"local destination root is not an ordinary writable directory: {root}", "Stop; no alternate root, symlink, or permissions repair.")
    allowed = {Path(str(item["path"])).name for item in PROTECTED_FILES}
    observed = {item.name for item in root.iterdir()}
    if observed - allowed:
        raise _reject("H3_DESTINATION_COLLISION", f"unexpected local destination entries: {sorted(observed - allowed)}", "Stop; do not alter or clean unrelated files.")
    protected: list[dict[str, object]] = []
    for expected in PROTECTED_FILES:
        path = root / Path(str(expected["path"])).name
        try:
            stat = path.lstat()
        except OSError as exc:
            raise _reject("H3_PROTECTED_FILE_INVALID", f"protected existing file is absent: {path}: {exc}", "Stop; WD-osfm evidence must remain intact.") from exc
        if not path.is_file() or path.is_symlink() or stat.st_size != expected["size_bytes"]:
            raise _reject("H3_PROTECTED_FILE_INVALID", f"protected existing file identity differs: {path}", "Stop; do not alter WD-osfm evidence.")
        protected.append({"path": path.as_posix(), "size_bytes": stat.st_size, "inode": stat.st_ino, "mtime_ns": stat.st_mtime_ns})
    for expected in candidates.values():
        final = _candidate_file(root, expected)
        part = final.with_name(final.name + ".part")
        if final.exists() or final.is_symlink() or part.exists() or part.is_symlink():
            raise _reject("H3_DESTINATION_COLLISION", f"candidate final or resumable part already exists: {final}", "Stop; no overwrite or cleanup is authorized.")
    statvfs = os.statvfs(root)
    free = statvfs.f_bavail * statvfs.f_frsize
    required = COMBINED_BYTES + MARGIN_BYTES
    if free < required:
        raise _reject("H3_LOCAL_CAPACITY_INSUFFICIENT", f"local free bytes={free}, required={required}", "Stop before transfer.")
    return {
        "root": root.resolve().as_posix(),
        "writable": True,
        "free_bytes": free,
        "required_free_bytes": required,
        "protected_existing_files": protected,
    }


def _validate_remote_preflight(record: Mapping[str, object], facts: dict[str, Any]) -> None:
    candidates = verify_authorization(record)
    required = {"host", "user", "source_filesystem_free_bytes", "candidates"}
    if set(facts) != required:
        raise _reject("H3_PREFLIGHT_OUTPUT_INVALID", f"remote probe fields differ: {sorted(facts)}", "Stop before transfer.")
    if not isinstance(facts.get("host"), str) or not facts["host"].strip() or not isinstance(facts.get("user"), str) or not facts["user"].strip():
        raise _reject("H3_HOST_IDENTITY_INVALID", "remote hostname or user is absent", "Stop before transfer.")
    if type(facts.get("source_filesystem_free_bytes")) is not int:
        raise _reject("H3_PREFLIGHT_OUTPUT_INVALID", "remote source filesystem free bytes is absent", "Stop before transfer.")
    for candidate_id, expected in candidates.items():
        source = facts["candidates"].get(candidate_id)
        if not isinstance(source, dict) or source.get("exists") is not True or source.get("type") != "regular_file" or source.get("symlink") is not False:
            raise _reject("H3_SOURCE_TYPE_INVALID", f"remote source is absent, symlinked, or not regular: {candidate_id}={source!r}", "Stop before transfer.")
        if source.get("size_bytes") != expected["size_bytes"]:
            raise _reject("H3_SOURCE_SIZE_MISMATCH", f"remote source size mismatch for {candidate_id}: {source.get('size_bytes')!r}", "Stop before transfer.")
        if not isinstance(source.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", source["sha256"]):
            raise _reject("H3_SOURCE_HASH_INVALID", f"live remote SHA-256 is absent or malformed for {candidate_id}", "Stop before transfer.")


def preflight(root: Path, record: Mapping[str, object], host: SshHostLike) -> dict[str, object]:
    """Verify exact remote sources and the ordinary-user local destination."""
    del root
    candidates = verify_authorization(record)
    _host_object(host)
    remote = _probe_json(host, _REMOTE_PREFLIGHT_CODE, {
        "candidates": list(candidates.values()),
        "source_filesystem": SOURCE_FILESYSTEM,
    }, timeout=3600)
    _validate_remote_preflight(record, remote)
    local = _local_destination_preflight(DESTINATION_ROOT, record)
    return {
        "schema_version": "wangp-dspy.h3-offload-preflight/v2",
        "status": "passed",
        "mutation": False,
        "host_alias": HOST,
        "host": remote["host"],
        "user": remote["user"],
        "source_filesystem": SOURCE_FILESYSTEM,
        "source_filesystem_free_bytes": remote["source_filesystem_free_bytes"],
        "local_destination": local,
        "candidates": remote["candidates"],
    }


def _write_text_once(path: Path, text: str) -> None:
    if path.exists():
        raise _reject("H3_EVIDENCE_ALREADY_PRESENT", f"immutable evidence already exists: {path}", "Never retry or overwrite the one attempt.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json_once(path: Path, value: Mapping[str, object]) -> None:
    _write_text_once(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def _repository_identity(root: Path) -> dict[str, object]:
    clean = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], text=True, capture_output=True, check=False)
    if clean.returncode or clean.stdout.strip():
        raise _reject("H3_REPOSITORY_DIRTY", f"repository is dirty or git failed: {clean.stdout.strip()!r}", "Commit the implementation before the sole host attempt.")
    values: dict[str, object] = {}
    revisions: tuple[tuple[str, Sequence[str]], ...] = (
        ("commit", ("HEAD",)),
        ("tree", ("HEAD^{tree}",)),
        ("branch", ("--abbrev-ref", "HEAD")),
    )
    for key, arguments in revisions:
        result = subprocess.run(["git", "-C", str(root), "rev-parse", *arguments], text=True, capture_output=True, check=False)
        if result.returncode:
            raise _reject("H3_REPOSITORY_IDENTITY_INVALID", f"cannot resolve {' '.join(arguments)}: {result.stderr.strip()}", "Run from the prepared story worktree.")
        values[key] = result.stdout.strip()
    return values


def _regular_hash_fact(path: Path) -> dict[str, object]:
    try:
        stat = path.lstat()
    except OSError as exc:
        return {"exists": False}
    if not path.is_file() or path.is_symlink():
        return {"exists": True, "type": "other", "symlink": path.is_symlink(), "size_bytes": stat.st_size}
    return {"exists": True, "type": "regular_file", "symlink": False, "size_bytes": stat.st_size, "sha256": _sha256(path)}


def _require_local_identity(path: Path, expected: Mapping[str, object], code: str) -> dict[str, object]:
    fact = _regular_hash_fact(path)
    if fact.get("type") != "regular_file" or fact.get("symlink") is not False:
        raise _reject(code, f"path is absent, symlinked, or not regular: {path}={fact!r}", "Stop and preserve state; do not retry or substitute.")
    if fact.get("size_bytes") != expected["size_bytes"]:
        raise _reject(code, f"size mismatch for {path}: {fact.get('size_bytes')!r}", "Stop and preserve state; do not retry or substitute.")
    if not isinstance(fact.get("sha256"), str):
        raise _reject(code, f"hash is absent for {path}", "Stop and preserve state; do not retry or substitute.")
    return fact


def _restoration_state(destination_root: Path, record: Mapping[str, object], state: Mapping[str, object]) -> list[dict[str, object]]:
    candidates = verify_authorization(record)
    mapping: list[dict[str, object]] = []
    freed = {item["id"]: item for item in state.get("frees", []) if isinstance(item, dict)}
    for candidate_id, expected in candidates.items():
        final = _candidate_file(destination_root, expected)
        local = _regular_hash_fact(final)
        mapping.append({
            "id": candidate_id,
            "from_local_copy": final.as_posix(),
            "to_remote_source": expected["source"],
            "size_bytes": expected["size_bytes"],
            "local_copy_present": local.get("exists") is True and local.get("type") == "regular_file",
            "local_sha256": local.get("sha256"),
            "remote_source_freed": candidate_id in freed,
            "restore_method": "separately authorized rsync push through SshHost.push_file",
        })
    return mapping


def _transfer_and_free(
    destination_root: Path,
    record: Mapping[str, object],
    host: SshHostLike,
    bundle: Path,
    state: dict[str, object],
    remote_candidates: Mapping[str, object],
) -> dict[str, object]:
    candidates = verify_authorization(record)
    local_before = _local_destination_preflight(destination_root, record)
    transfers: list[dict[str, object]] = []
    state["transfers"] = transfers
    for candidate_id, expected in candidates.items():
        final = _candidate_file(destination_root, expected)
        part = final.with_name(final.name + ".part")
        started = time.time_ns()
        remote_hash = str(remote_candidates[candidate_id]["sha256"])
        host.fetch_file_partial(str(expected["source"]), str(part))
        part_fact = _require_local_identity(part, expected, "H3_PART_TRANSFER_MISMATCH")
        if part_fact["sha256"] != remote_hash:
            raise _reject("H3_PART_TRANSFER_MISMATCH", f"resumable part hash differs for {candidate_id}", "Stop and preserve the part; do not retry.")
        if final.exists() or final.is_symlink():
            raise _reject("H3_DESTINATION_COLLISION", f"final appeared before promotion: {final}", "Stop and preserve state; do not overwrite it.")
        os.replace(part, final)
        final_fact = _require_local_identity(final, expected, "H3_FINAL_COPY_MISMATCH")
        if final_fact["sha256"] != remote_hash:
            raise _reject("H3_FINAL_COPY_MISMATCH", f"promoted copy hash differs for {candidate_id}", "Stop and preserve the copy; do not retry.")
        transfer = {
            "id": candidate_id,
            "source": expected["source"],
            "destination": final.as_posix(),
            "part_path": part.as_posix(),
            "size_bytes": expected["size_bytes"],
            "remote_preflight_sha256": remote_hash,
            "part_sha256": part_fact["sha256"],
            "final_sha256": final_fact["sha256"],
            "part_absent_after_promotion": not part.exists() and not part.is_symlink(),
            "started_ns": started,
            "finished_ns": time.time_ns(),
        }
        transfers.append(transfer)
        _write_json_once(bundle / f"transfer-{candidate_id}.json", transfer)
    final_verification = []
    for candidate_id, expected in candidates.items():
        fact = _require_local_identity(_candidate_file(destination_root, expected), expected, "H3_FINAL_COPY_MISMATCH")
        if fact["sha256"] != remote_candidates[candidate_id]["sha256"]:
            raise _reject("H3_FINAL_COPY_MISMATCH", f"second final verification differs for {candidate_id}", "Stop and preserve both copies; do not free either source.")
        final_verification.append({"id": candidate_id, "size_bytes": fact["size_bytes"], "sha256": fact["sha256"]})
    verification = {
        "status": "both_copies_verified",
        "verified_count": len(final_verification),
        "required_count": len(candidates),
        "copies": final_verification,
    }
    _write_json_once(bundle / "final-verification.json", verification)
    frees: list[dict[str, object]] = []
    state["frees"] = frees
    for candidate_id, expected in candidates.items():
        started = time.time_ns()
        host.unlink_verified_file(
            str(expected["source"]),
            expected_size_bytes=int(expected["size_bytes"]),  # type: ignore[arg-type]
            expected_sha256=str(next(item for item in final_verification if item["id"] == candidate_id)["sha256"]),
        )
        post = _probe_json(host, _REMOTE_POSTFREE_CODE, {
            "candidates": [expected],
            "source_filesystem": SOURCE_FILESYSTEM,
        }, timeout=120)
        source_state = post.get("candidates", {}).get(candidate_id)
        if not isinstance(source_state, dict) or source_state.get("source_exists") is not False or source_state.get("source_is_symlink") is not False:
            raise _reject("H3_REMOTE_SOURCE_FREE_INVALID", f"source still exists after governed free: {source_state!r}", "Stop and preserve state; do not retry.")
        free_record = {
            "id": candidate_id,
            "source": expected["source"],
            "method": "SshHost.unlink_verified_file",
            "size_bytes": expected["size_bytes"],
            "sha256": next(item for item in final_verification if item["id"] == candidate_id)["sha256"],
            "source_absent": True,
            "remote_free_bytes": post["source_filesystem_free_bytes"],
            "started_ns": started,
            "finished_ns": time.time_ns(),
        }
        frees.append(free_record)
        _write_json_once(bundle / f"free-{candidate_id}.json", free_record)
    remote_after = _probe_json(host, _REMOTE_POSTFREE_CODE, {
        "candidates": list(candidates.values()),
        "source_filesystem": SOURCE_FILESYSTEM,
    }, timeout=120)
    protected_after: list[dict[str, object]] = []
    for expected in PROTECTED_FILES:
        path = destination_root / Path(str(expected["path"])).name
        stat = path.lstat()
        if not path.is_file() or path.is_symlink() or stat.st_size != expected["size_bytes"]:
            raise _reject("H3_PROTECTED_FILE_INVALID", f"protected existing file changed during the run: {path}", "Stop and record the boundary; do not alter WD-osfm evidence.")
        protected_after.append({"path": path.as_posix(), "size_bytes": stat.st_size, "inode": stat.st_ino, "mtime_ns": stat.st_mtime_ns})
    if protected_after != local_before["protected_existing_files"]:
        raise _reject("H3_PROTECTED_FILE_INVALID", "protected WD-osfm file identity changed during the run", "Stop and record the boundary; do not alter WD-osfm evidence.")
    statvfs = os.statvfs(destination_root)
    return {
        "status": "offloaded_and_remote_sources_freed",
        "local_destination_root": destination_root.resolve().as_posix(),
        "local_free_before_bytes": local_before["free_bytes"],
        "local_free_after_bytes": statvfs.f_bavail * statvfs.f_frsize,
        "remote_free_after_bytes": remote_after["source_filesystem_free_bytes"],
        "transfers": transfers,
        "final_verification": verification,
        "remote_source_frees": frees,
        "protected_existing_files_after": protected_after,
    }


def _has_current_evidence(bundle: Path) -> bool:
    if not bundle.exists():
        return False
    boundary = bundle / "boundary-attempts"
    for child in bundle.iterdir():
        if child.name != "boundary-attempts":
            return True
    if not boundary.exists():
        return False
    expected = {
        frozenset({"attempt.json", "failure.json", "evidence.sha256"}),
        frozenset({"attempt.json", "preflight.json", "failure.json", "evidence.sha256"}),
    }
    for attempt in boundary.iterdir():
        if not attempt.is_dir() or not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z", attempt.name):
            return True
        children = list(attempt.iterdir())
        if any(child.is_dir() for child in children) or {child.name for child in children} not in expected:
            return True
    return False


def _parse_execution_stdout(stdout: str) -> dict[str, Any]:
    lines = [line for line in stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise _reject("H3_EXECUTION_OUTPUT_INVALID", f"script emitted {len(lines)} output lines", "Stop after recording the boundary.")
    try:
        value = json.loads(lines[0])
    except json.JSONDecodeError as exc:
        raise _reject("H3_EXECUTION_OUTPUT_INVALID", f"script JSON is invalid: {exc}", "Stop after recording the boundary.") from exc
    if not isinstance(value, dict):
        raise _reject("H3_EXECUTION_OUTPUT_INVALID", "script JSON root is not an object", "Stop after recording the boundary.")
    return value


def _manifest(bundle: Path) -> dict[str, object]:
    files = sorted(path for path in bundle.rglob("*") if path.is_file() and path.name != "evidence.sha256")
    return {
        "schema_version": "wangp-dspy.h3-offload-evidence/v1",
        "files": [
            {"path": path.relative_to(bundle).as_posix(), "byte_size": path.stat().st_size, "sha256": _sha256(path)}
            for path in files
        ],
    }


def execute(root: Path, record: Mapping[str, object], host: SshHostLike) -> dict[str, object]:
    """Run one preflight, sequential verified-copy transfer, and governed free."""
    repository = root.expanduser().resolve()
    identity = _repository_identity(repository)
    bundle = repository / BUNDLE_RELATIVE
    if _has_current_evidence(bundle):
        raise _reject("H3_RUN_ALREADY_PRESENT", f"host-run evidence already exists: {bundle}", "Do not retry or overwrite a prior attempt.")
    bundle.mkdir(parents=True, exist_ok=True)
    attempt_started = time.time_ns()
    _write_json_once(bundle / "attempt.json", {
        "schema_version": RUN_SCHEMA, "status": "started",
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repository": identity, "clean_tree_before_attempt": True,
        "mutation_attempt_budget": 1,
    })
    state: dict[str, object] = {"transfers": [], "frees": []}
    try:
        before = preflight(repository, record, host)
        state["remote_candidates"] = before["candidates"]
        _write_json_once(bundle / "preflight.json", before)
        result = _transfer_and_free(DESTINATION_ROOT, record, host, bundle, state, before["candidates"])
        restoration = _restoration_state(DESTINATION_ROOT, record, state)
        summary = {
            "schema_version": RUN_SCHEMA,
            "status": "passed",
            "authorization_verbatim": VERBATIM,
            "authorization_recorded_utc": APPROVED_AT,
            "destination_decision_verbatim": DESTINATION_VERBATIM,
            "destination_decision_recorded_utc": DESTINATION_DECIDED_AT,
            "repository": identity,
            "clean_tree_before_attempt": True,
            "host_alias": HOST,
            "host": before["host"],
            "user": before["user"],
            "preflight": before,
            "result": result,
            "recovery_mapping": restoration,
            "mutation_attempt_count": 1,
            "doctor_floor_bytes": DOCTOR_FLOOR_BYTES,
            "doctor_floor_met_after_remote_free": int(result["remote_free_after_bytes"]) >= DOCTOR_FLOOR_BYTES,
            "storage_result_only": True,
            "generation_result": False,
            "hardware_verdict": False,
            "capability_promotion": False,
            "downstream_authority": DOWNSTREAM_AUTHORITY,
            "attempt_started_ns": attempt_started,
            "attempt_finished_ns": time.time_ns(),
        }
        _write_json_once(bundle / "run-summary.json", summary)
        _write_json_once(bundle / "evidence.sha256", _manifest(bundle))
        return summary
    except BaseException as exc:
        error = exc if isinstance(exc, H3OffloadError) else _reject("H3_EXECUTION_CRITICAL", f"{type(exc).__name__}: {exc}", "Stop and preserve state; no retry.", critical=True)
        _write_json_once(bundle / "failure.json", {
            "schema_version": RUN_SCHEMA,
            "status": "failed",
            "diagnostic": {"code": error.code, "observed": error.observed, "remediation": error.remediation, "critical": error.critical},
            "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "preserved_state": state,
            "restoration_mapping": _restoration_state(DESTINATION_ROOT, record, state),
        })
        _write_json_once(bundle / "evidence.sha256", _manifest(bundle))
        raise error from None


def _load_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _reject("H3_AUTHORIZATION_INVALID", f"cannot read JSON {path}: {exc}", "Supply the exact committed authorization file.") from exc
    if not isinstance(value, dict):
        raise _reject("H3_AUTHORIZATION_INVALID", "authorization root is not an object", "Supply the documented object.")
    return value


def _emit(value: Mapping[str, object]) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--execute", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        if arguments.authorization is None:
            raise _reject("H3_AUTHORIZATION_ABSENT", "authorization path was not supplied", "Supply the committed operator authorization record.")
        authorization = arguments.root / arguments.authorization if not arguments.authorization.is_absolute() else arguments.authorization
        record = _load_json(authorization)
        verify_authorization(record)
        if not arguments.execute:
            _emit({"schema_version": "wangp-dspy.h3-offload-command-contract/v1", "status": "represented", "host": HOST, "execute": False, "mutation": False})
            return 0
        from host.render_host import SshHost

        pull_root = tempfile.mkdtemp(prefix="wd-cuzw-h3-offload-pull-")
        host = SshHost(target=HOST, wgp_root=WGP_ROOT, pull_root=pull_root)
        _emit(execute(arguments.root, record, host))
        return 0
    except H3OffloadError as exc:
        _emit({"schema_version": "wangp-dspy.h3-offload-boundary/v1", "status": "failed", "diagnostic": {"code": exc.code, "observed": exc.observed, "remediation": exc.remediation, "critical": exc.critical}})
        return 3


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
