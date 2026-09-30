#!/usr/bin/env python3
"""Authorized, reversible, one-attempt H3 checkpoint offload runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping, Sequence


AUTH_SCHEMA = "wangp-dspy.h3-offload-authorization/v1"
RUN_SCHEMA = "wangp-dspy.h3-offload-run/v1"
BUNDLE_RELATIVE = Path("datasets/runs/maestro-parity/h3-offload/host-run")
AUTHORIZATION_RELATIVE = Path("datasets/runs/maestro-parity/h3-offload/operator-authorization.json")
_AUTHORIZED_TEMPLATE = json.loads((Path(__file__).resolve().parents[1] / AUTHORIZATION_RELATIVE).read_text(encoding="utf-8"))
HOST = str(_AUTHORIZED_TEMPLATE["host"])
WGP_ROOT = str(_AUTHORIZED_TEMPLATE["source_filesystem"])
OFFLOAD_ROOT = str(_AUTHORIZED_TEMPLATE["offload_root"])
BULK_MOUNT = str(_AUTHORIZED_TEMPLATE["bulk_mount"])
SOURCE_FILESYSTEM = WGP_ROOT
COMBINED_BYTES = 44_288_216_793
MARGIN_BYTES = 1_073_741_824
DOCTOR_FLOOR_BYTES = 53_687_091_200
VERBATIM = "Approved authorized"
APPROVED_AT = "2026-09-30T19:57:10Z"
REQUIRED_SCOPE = (
    "reversible offload of exactly the two superseded H3 checkpoints on host 3090, "
    "with live size/SHA verification, a reversible recovery path, and no deletion"
)
EXECUTION_BOUNDARY = {
    "deletion": False, "copy": False, "hard_link": False, "symlink": False,
    "rewrite": False, "privileged_command": False, "download": False,
    "gpu_work": False, "provider_spend": False, "queue_admission": False,
}
DOWNSTREAM_AUTHORITY = {
    "h3_retry": False, "ltx_download": False, "inference": False,
    "generation_claim": False, "hardware_verdict": False,
    "capability_promotion": False,
}
EXPECTED_CANDIDATES: tuple[dict[str, object], ...] = tuple(dict(item) for item in _AUTHORIZED_TEMPLATE["candidates"])


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
        {"schema_version", "status", "host", "authorization", "candidates", "offload_root", "bulk_mount", "source_filesystem", "combined_recovery_bytes", "execution", "downstream_authority"},
        "H3_AUTHORIZATION_TAMPERED", "authorization",
    )
    if record.get("schema_version") != AUTH_SCHEMA or record.get("status") != "authorized":
        raise _reject("H3_AUTHORIZATION_TAMPERED", "schema or status is not the exact authorized pair", f"Use {AUTH_SCHEMA} with status=authorized.")
    if record.get("host") != HOST:
        raise _reject("H3_AUTHORIZATION_HOST_MISMATCH", f"authorized host is {record.get('host')!r}", f"Only host {HOST!r} is authorized.")
    if record.get("offload_root") != OFFLOAD_ROOT or record.get("bulk_mount") != BULK_MOUNT or record.get("source_filesystem") != SOURCE_FILESYSTEM:
        raise _reject("H3_AUTHORIZATION_PATH_MISMATCH", "offload root, bulk mount, or source filesystem differs", "Use only the exact authorized paths.")
    if type(record.get("combined_recovery_bytes")) is not int or record.get("combined_recovery_bytes") != COMBINED_BYTES:
        raise _reject("H3_AUTHORIZATION_TOTAL_MISMATCH", f"combined recovery bytes is {record.get('combined_recovery_bytes')!r}", f"Use {COMBINED_BYTES} exactly.")
    authorization = record.get("authorization")
    if not isinstance(authorization, dict):
        raise _reject("H3_AUTHORIZATION_PARTIAL", "authorization object is absent", "Record the verbatim approval and scope.")
    _require_keys(authorization, {"required_scope", "record"}, "H3_AUTHORIZATION_TAMPERED", "authorization")
    if authorization.get("required_scope") != REQUIRED_SCOPE:
        raise _reject("H3_AUTHORIZATION_SCOPE_MISMATCH", "required scope differs", "Record the exact approved storage scope.")
    approval = authorization.get("record")
    if not isinstance(approval, dict):
        raise _reject("H3_AUTHORIZATION_PARTIAL", "operator approval record is absent", "Record the operator, UTC time, and verbatim reply.")
    _require_keys(approval, {"operator", "recorded_utc", "verbatim"}, "H3_AUTHORIZATION_TAMPERED", "operator approval")
    if approval != {"operator": "operator", "recorded_utc": APPROVED_AT, "verbatim": VERBATIM}:
        raise _reject("H3_AUTHORIZATION_VERBATIM_MISMATCH", "operator approval record differs", 'Record exactly "Approved authorized" at 2026-09-30T19:57:10Z.')
    if record.get("execution") != EXECUTION_BOUNDARY or record.get("downstream_authority") != DOWNSTREAM_AUTHORITY:
        raise _reject("H3_AUTHORIZATION_BOUNDARY_MISMATCH", "execution or downstream authority differs", "All prohibited actions must remain false.")
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
    for name in ("run_probe", "push_file", "run_argv"):
        if not callable(getattr(host, name, None)):
            raise _reject("H3_HOST_SEAM_INVALID", f"host seam lacks {name}", "Use host.render_host.SshHost or its exact seam contract.")


_PROBE_CODE = r'''import hashlib,json,os,stat,sys
p=json.loads(sys.argv[2])
def f(path):
 try:s=os.lstat(path)
 except OSError:return {"exists":False}
 return {"exists":True,"type":"directory" if stat.S_ISDIR(s.st_mode) else "regular_file" if stat.S_ISREG(s.st_mode) else "other","symlink":stat.S_ISLNK(s.st_mode),"device":s.st_dev,"size_bytes":s.st_size,"writable":os.access(path,os.W_OK)}
def h(path):
 d=hashlib.sha256()
 with open(path,"rb") as x:
  for b in iter(lambda:x.read(4194304),b""):d.update(b)
 return d.hexdigest()
def space(path):
 v=os.statvfs(path);return v.f_bavail*v.f_frsize
root=p["offload_root"];nearest=root
while not os.path.lexists(nearest):nearest=os.path.dirname(nearest)
components=[];candidate=root
while candidate.startswith(p["bulk_mount"]+"/"):
 components.append(candidate);candidate=os.path.dirname(candidate)
component_facts=[f(item) for item in reversed(components)]
contained=(root.startswith(p["bulk_mount"]+"/") and f(nearest)["device"]==f(p["bulk_mount"])["device"] and all(item["exists"] and item["type"]=="directory" and not item["symlink"] and item["device"]==f(p["bulk_mount"])["device"] for item in component_facts if item["exists"]))
out={"host":os.uname().nodename,"user":__import__("pwd").getpwuid(os.getuid()).pw_name,"candidates":{},"destinations":{},"root":f(root),"root_nearest_parent":f(nearest),"root_contained":contained,"bulk":{"device":f(p["bulk_mount"])["device"],"free_bytes":space(p["bulk_mount"])},"source_filesystem_free_bytes":space(p["source_filesystem"]),"script":f(p["script_path"])}
for c in p["candidates"]:
 x=f(c["source"]);x["sha256"]=h(c["source"]) if x["type"]=="regular_file" and not x["symlink"] else None;out["candidates"][c["id"]]=x;out["destinations"][c["id"]]=f(c["destination"])
print(json.dumps(out,sort_keys=True,separators=(",",":")))'''

_SCRIPT_ID_CODE = r'''import hashlib,json,os,stat,sys
p=sys.argv[2];s=os.lstat(p)
print(json.dumps({"type":"regular_file" if stat.S_ISREG(s.st_mode) else "other","symlink":stat.S_ISLNK(s.st_mode),"size_bytes":s.st_size,"sha256":hashlib.sha256(open(p,"rb").read()).hexdigest()},sort_keys=True,separators=(",",":")))'''


def _offload_script(candidates: Sequence[Mapping[str, object]]) -> str:
    literal = json.dumps(list(candidates), sort_keys=True, separators=(",", ":"))
    return f"""#!/bin/sh
set -eu
exec python3 - <<'PY'
import hashlib, json, os, stat, subprocess, time
CANDIDATES = json.loads(r'''{literal}''')
ROOT = {OFFLOAD_ROOT!r}
BULK = {BULK_MOUNT!r}
SOURCE_FS = {SOURCE_FILESYSTEM!r}
FLOOR = {DOCTOR_FLOOR_BYTES}
def facts(path):
    try: item = os.lstat(path)
    except OSError: return {{"exists": False}}
    return {{"exists": True, "type": "directory" if stat.S_ISDIR(item.st_mode) else "regular_file" if stat.S_ISREG(item.st_mode) else "other", "symlink": stat.S_ISLNK(item.st_mode), "device": item.st_dev, "size_bytes": item.st_size}}
def digest(path):
    value = hashlib.sha256()
    with open(path, "rb") as source:
        for block in iter(lambda: source.read(4194304), b""): value.update(block)
    return value.hexdigest()
def free(path):
    value = os.statvfs(path)
    return value.f_bavail * value.f_frsize
def nearest_existing(path):
    while not os.path.lexists(path): path = os.path.dirname(path)
    return path
def check_prestate():
    bulk = facts(BULK)
    nearest = nearest_existing(ROOT)
    if not bulk["exists"] or bulk["type"] != "directory" or bulk["symlink"]: raise OSError("bulk mount invalid")
    if not ROOT.startswith(BULK + "/") or facts(nearest)["device"] != bulk["device"]: raise OSError("offload root is not contained by bulk mount")
    if free(BULK) < sum(int(item["size_bytes"]) for item in CANDIDATES) + {MARGIN_BYTES}: raise OSError("insufficient bulk free space")
    for item in CANDIDATES:
        source = facts(item["source"])
        if not source["exists"] or source["type"] != "regular_file" or source["symlink"] or source["size_bytes"] != int(item["size_bytes"]):
            raise OSError("source identity mismatch: " + item["id"])
        if facts(item["destination"])["exists"]: raise OSError("destination collision: " + item["id"])
        item["pre_sha256"] = digest(item["source"])
    return {{"bulk_free_before": free(BULK), "source_free_before": free(SOURCE_FS)}}
def move_no_clobber(source, destination):
    return subprocess.run(["mv", "-n", source, destination], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
def verify_moved(item):
    if os.path.lexists(item["source"]) or facts(item["destination"])["type"] != "regular_file": raise OSError("move outcome mismatch: " + item["id"])
    observed_size = os.lstat(item["destination"]).st_size
    observed_hash = digest(item["destination"])
    if observed_size != int(item["size_bytes"]) or observed_hash != item["pre_sha256"]: raise OSError("moved bytes mismatch: " + item["id"])
    return {{"id": item["id"], "source": item["source"], "destination": item["destination"], "size_bytes": int(item["size_bytes"]), "pre_sha256": item["pre_sha256"], "post_size_bytes": observed_size, "post_sha256": observed_hash, "source_absent": True, "destination_present": True}}
def rollback(moved):
    outcomes = []
    for item in reversed(moved):
        outcome = dict(item)
        try:
            if os.path.lexists(item["source"]) or not os.path.lexists(item["destination"]): raise OSError("rollback path collision")
            result = move_no_clobber(item["destination"], item["source"])
            if result.returncode or os.path.lexists(item["destination"]) or not os.path.lexists(item["source"]): raise OSError("reverse move failed")
            if os.lstat(item["source"]).st_size != item["size_bytes"] or digest(item["source"]) != item["pre_sha256"]: raise OSError("rollback identity mismatch")
            outcome.update({{"rolled_back": True, "destination_absent": True, "verified": True}})
        except BaseException as exc:
            outcome.update({{"rolled_back": False, "verified": False, "error": str(exc)}})
        outcomes.append(outcome)
    return outcomes
moved = []
root_created = False
try:
    before = check_prestate()
    root_created = not os.path.lexists(ROOT)
    os.makedirs(ROOT, exist_ok=True)
    root_fact = facts(ROOT)
    if root_fact["type"] != "directory" or root_fact["symlink"] or root_fact["device"] != facts(BULK)["device"]:
        raise OSError("created offload root is invalid")
    for candidate in CANDIDATES:
        move_started = time.time_ns()
        result = move_no_clobber(candidate["source"], candidate["destination"])
        if result.returncode: raise OSError("authorized move failed: " + candidate["id"])
        record = verify_moved(candidate)
        record["move_started_ns"] = move_started
        record["move_finished_ns"] = time.time_ns()
        record["move_stderr"] = result.stderr
        moved.append(record)
        # POST_MOVE_BOUNDARY
    output = {{"status": "offloaded", "moved": moved, "root_created": root_created, "rollback": {{"state": "not_required", "outcomes": []}}, "free_bytes": {{"bulk_before": before["bulk_free_before"], "bulk_after": free(BULK), "source_filesystem_before": before["source_free_before"], "source_filesystem_after": free(SOURCE_FS)}}, "doctor_floor_bytes": FLOOR, "doctor_floor_met": free(SOURCE_FS) >= FLOOR, "storage_result_only": True}}
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
except BaseException as exc:
    outcomes = rollback(moved)
    rollback_failed = any(not item.get("verified") for item in outcomes)
    output = {{"status": "rollback_failed" if rollback_failed else "rolled_back", "failure": str(exc), "failure_type": type(exc).__name__, "moved_before_failure": moved, "root_created": root_created, "rollback": {{"state": "failed" if rollback_failed else "completed", "outcomes": outcomes}}, "free_bytes": {{"bulk_before": free(BULK), "bulk_after": free(BULK), "source_filesystem_before": free(SOURCE_FS), "source_filesystem_after": free(SOURCE_FS)}}, "doctor_floor_bytes": FLOOR, "doctor_floor_met": free(SOURCE_FS) >= FLOOR, "storage_result_only": True}}
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    raise SystemExit(2)
PY
"""


def _script_identity(script: str) -> dict[str, object]:
    data = script.encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    return {
        "relative_path": BUNDLE_RELATIVE.joinpath("offload-script.sh").as_posix(),
        "remote_path": f"/tmp/wd-cuzw-h3-offload-{digest}.sh",
        "sha256": digest,
        "byte_size": len(data),
    }


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


def _mount_fact(host: SshHostLike) -> dict[str, str]:
    rc, stdout, stderr = host.run_probe(["findmnt", "-n", "-o", "TARGET,SOURCE,FSTYPE", "--", BULK_MOUNT], timeout=60)
    lines = [line for line in stdout.splitlines() if line.strip()]
    if rc != 0 or len(lines) != 1:
        raise _reject("H3_ROOT_CONTAINMENT_INVALID", f"bulk mount probe was absent or ambiguous ({len(lines)} rows): {stderr.strip()[:200]}", "Stop before root creation or mutation.")
    fields = lines[0].split()
    if len(fields) != 3 or fields[0] != BULK_MOUNT or not fields[1] or not fields[2]:
        raise _reject("H3_ROOT_CONTAINMENT_INVALID", f"bulk mount identity differs: {lines[0]!r}", "Use the exact mounted /mnt/bulk-hdd filesystem only.")
    return {"target": fields[0], "source": fields[1], "filesystem_type": fields[2]}


def _validate_preflight(record: Mapping[str, object], facts: dict[str, Any], identity: Mapping[str, object]) -> None:
    candidates = verify_authorization(record)
    required = {"host", "user", "candidates", "destinations", "root", "root_nearest_parent", "root_contained", "bulk", "source_filesystem_free_bytes", "script"}
    if set(facts) != required:
        raise _reject("H3_PREFLIGHT_OUTPUT_INVALID", f"probe fields differ: {sorted(facts)}", "Stop before mutation; require the exact fact set.")
    if not isinstance(facts.get("host"), str) or not facts["host"].strip() or not isinstance(facts.get("user"), str) or not facts["user"].strip():
        raise _reject("H3_HOST_IDENTITY_INVALID", "remote hostname or user is absent", "Stop before mutation.")
    root = facts["root"]
    parent = facts["root_nearest_parent"]
    if facts.get("root_contained") is not True or root.get("type") not in {None, "directory"} or parent.get("type") != "directory" or parent.get("writable") is not True:
        raise _reject("H3_ROOT_CONTAINMENT_INVALID", f"root/parent containment or ordinary write permission failed: root={root!r}, parent={parent!r}", "Stop; no alternate root, sudo, or permissions repair.")
    if root.get("exists") and (root.get("type") != "directory" or root.get("symlink") or root.get("writable") is not True):
        raise _reject("H3_ROOT_CONTAINMENT_INVALID", f"existing root is not an ordinary writable directory: {root!r}", "Stop; no alternate root or repair.")
    bulk_free = facts["bulk"].get("free_bytes")
    if type(bulk_free) is not int or bulk_free < COMBINED_BYTES + MARGIN_BYTES:
        raise _reject("H3_FREE_SPACE_INSUFFICIENT", f"bulk free bytes={bulk_free!r}, required={COMBINED_BYTES + MARGIN_BYTES}", "Stop before root creation or move.")
    script_fact = facts["script"]
    if script_fact.get("exists") is not False:
        raise _reject("H3_SCRIPT_IDENTITY_INVALID", f"remote staged script path is already occupied: {script_fact!r}", "Use the deterministic script path and never overwrite it.")
    for candidate_id, expected in candidates.items():
        source = facts["candidates"].get(candidate_id)
        destination = facts["destinations"].get(candidate_id)
        if not isinstance(source, dict) or source.get("exists") is not True or source.get("type") != "regular_file" or source.get("symlink") is not False:
            raise _reject("H3_SOURCE_TYPE_INVALID", f"source is absent, symlinked, or not regular: {candidate_id}={source!r}", "Stop before mutation.")
        if source.get("size_bytes") != expected["size_bytes"]:
            raise _reject("H3_SOURCE_SIZE_MISMATCH", f"source size mismatch for {candidate_id}: {source.get('size_bytes')!r}", "Stop before mutation; do not substitute a file.")
        if not isinstance(source.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", source["sha256"]):
            raise _reject("H3_SOURCE_HASH_INVALID", f"live SHA-256 is absent or malformed for {candidate_id}", "Stop before mutation.")
        if not isinstance(destination, dict) or destination.get("exists") is not False:
            raise _reject("H3_DESTINATION_COLLISION", f"destination is occupied for {candidate_id}: {destination!r}", "Stop before mutation; no overwrite or cleanup is authorized.")
    expected_identity = _script_identity(_offload_script(list(record["candidates"])))  # type: ignore[arg-type]
    if identity != expected_identity:
        raise _reject("H3_SCRIPT_IDENTITY_INVALID", "generated script identity changed", "Stop before staging the script.")


def preflight(root: Path, record: Mapping[str, object], host: SshHostLike) -> dict[str, object]:
    """Collect all live host facts through read-only SshHost probes."""
    del root
    candidates = verify_authorization(record)
    _host_object(host)
    script = _offload_script(list(record["candidates"]))  # type: ignore[arg-type]
    identity = _script_identity(script)
    payload = {
        "candidates": list(candidates.values()),
        "offload_root": OFFLOAD_ROOT,
        "bulk_mount": BULK_MOUNT,
        "source_filesystem": SOURCE_FILESYSTEM,
        "script_path": identity["remote_path"],
    }
    facts = _probe_json(host, _PROBE_CODE, payload, timeout=3600)
    mount = _mount_fact(host)
    _validate_preflight(record, facts, identity)
    return {
        "schema_version": "wangp-dspy.h3-offload-preflight/v1",
        "status": "passed", "mutation": False, "host_alias": HOST,
        "host": facts["host"], "user": facts["user"], "mount": mount,
        "root": facts["root"], "root_nearest_parent": facts["root_nearest_parent"],
        "source_filesystem_free_bytes": facts["source_filesystem_free_bytes"],
        "bulk_free_bytes": facts["bulk"]["free_bytes"],
        "required_bulk_free_bytes": COMBINED_BYTES + MARGIN_BYTES,
        "candidates": {
            candidate_id: {
                "size_bytes": facts["candidates"][candidate_id]["size_bytes"],
                "sha256": facts["candidates"][candidate_id]["sha256"],
                "type": facts["candidates"][candidate_id]["type"],
                "symlink": facts["candidates"][candidate_id]["symlink"],
            }
            for candidate_id in candidates
        },
        "script": identity,
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
    for key, revision in (("commit", "HEAD"), ("tree", "HEAD^{tree}"), ("branch", "--abbrev-ref HEAD")):
        result = subprocess.run(["git", "-C", str(root), "rev-parse", revision], text=True, capture_output=True, check=False)
        if result.returncode:
            raise _reject("H3_REPOSITORY_IDENTITY_INVALID", f"cannot resolve {revision}: {result.stderr.strip()}", "Run from the prepared story worktree.")
        values[key] = result.stdout.strip()
    return values


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


def _validate_success(record: Mapping[str, object], result: Mapping[str, Any]) -> None:
    candidates = verify_authorization(record)
    if result.get("status") != "offloaded":
        critical = result.get("status") == "rollback_failed"
        raise _reject(
            "H3_OFFLOAD_ROLLBACK_FAILED" if critical else "H3_OFFLOAD_ROLLED_BACK",
            f"single attempt ended {result.get('status')!r}: {result.get('failure')!r}",
            "Preserve rollback evidence and stop; never retry this batch.",
            critical=critical,
        )
    moved = result.get("moved")
    if not isinstance(moved, list) or len(moved) != len(candidates):
        raise _reject("H3_MOVE_OUTCOME_INVALID", "script did not record exactly two moved candidates", "Stop after automatic rollback evidence.")
    records = {item.get("id"): item for item in moved if isinstance(item, dict)}
    if set(records) != set(candidates):
        raise _reject("H3_MOVE_OUTCOME_INVALID", f"moved ids differ: {sorted(records)}", "Stop after automatic rollback evidence.")
    for candidate_id, expected in candidates.items():
        item = records[candidate_id]
        if item.get("source_absent") is not True or item.get("destination_present") is not True:
            raise _reject("H3_MOVE_OUTCOME_INVALID", f"source/destination presence mismatch for {candidate_id}", "Stop after automatic rollback evidence.")
        if item.get("size_bytes") != expected["size_bytes"] or item.get("post_size_bytes") != expected["size_bytes"]:
            raise _reject("H3_MOVED_SIZE_MISMATCH", f"post-move size mismatch for {candidate_id}", "Automatic rollback must be verified before stopping.")
        if item.get("pre_sha256") != item.get("post_sha256") or not isinstance(item.get("post_sha256"), str):
            raise _reject("H3_MOVED_HASH_MISMATCH", f"post-move hash mismatch for {candidate_id}", "Automatic rollback must be verified before stopping.")
    free = result.get("free_bytes")
    if not isinstance(free, dict) or type(free.get("source_filesystem_after")) is not int or type(free.get("bulk_after")) is not int:
        raise _reject("H3_POSTOFFLIGHT_INVALID", "post-offload free-byte facts are absent", "Stop after automatic rollback evidence.")
    if result.get("doctor_floor_bytes") != DOCTOR_FLOOR_BYTES or type(result.get("doctor_floor_met")) is not bool:
        raise _reject("H3_POSTOFFLIGHT_INVALID", "doctor-floor fact is absent or ambiguous", "Stop after automatic rollback evidence.")


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
    """Run preflight, stage one script, and perform exactly one offload attempt."""
    repository = root.expanduser().resolve()
    identity = _repository_identity(repository)
    bundle = repository / BUNDLE_RELATIVE
    if bundle.exists() and any(bundle.iterdir()):
        raise _reject("H3_RUN_ALREADY_PRESENT", f"host-run evidence already exists: {bundle}", "Do not retry or overwrite a prior attempt.")
    bundle.mkdir(parents=True, exist_ok=True)
    attempt_started = time.time_ns()
    _write_json_once(bundle / "attempt.json", {
        "schema_version": RUN_SCHEMA, "status": "started",
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repository": identity, "clean_tree_before_attempt": True,
        "mutation_attempt_budget": 1,
    })
    try:
        before = preflight(repository, record, host)
        script = _offload_script(list(record["candidates"]))  # type: ignore[arg-type]
        script_identity = before["script"]
        _write_text_once(bundle / "offload-script.sh", script)
        _write_json_once(bundle / "preflight.json", before)
        local_script = bundle / "offload-script.sh"
        if _sha256(local_script) != script_identity["sha256"] or local_script.stat().st_size != script_identity["byte_size"]:
            raise _reject("H3_SCRIPT_IDENTITY_INVALID", "local staged script bytes differ from preflight identity", "Stop before mutation.")
        staged_path = host.push_file(str(local_script), str(script_identity["remote_path"]))
        stage_probe = _probe_json(host, _SCRIPT_ID_CODE, {"script_path": staged_path}, timeout=120)
        expected_stage = {"type": "regular_file", "symlink": False, "size_bytes": script_identity["byte_size"], "sha256": script_identity["sha256"]}
        if stage_probe != expected_stage:
            raise _reject("H3_SCRIPT_IDENTITY_INVALID", f"remote staged script differs: {stage_probe!r}", "Stop before offload mutation.")
        stage = {
            "method": "SshHost.push_file", "local_path": str(local_script.relative_to(repository)),
            "remote_path": staged_path, "sha256": script_identity["sha256"],
            "byte_size": script_identity["byte_size"],
        }
        _write_json_once(bundle / "stage.json", stage)
        execution_started = time.time_ns()
        execution = host.run_argv(["/bin/sh", staged_path], cwd="/", timeout=7200)
        execution_finished = time.time_ns()
        raw = {
            "method": "SshHost.run_argv", "argv": ["/bin/sh", staged_path], "cwd": "/",
            "timeout": 7200, "returncode": execution.returncode, "stdout": execution.stdout,
            "stderr": execution.stderr, "started_ns": execution_started,
            "finished_ns": execution_finished,
        }
        _write_json_once(bundle / "execution.json", raw)
        result = _parse_execution_stdout(execution.stdout)
        _write_json_once(bundle / "offload-result.json", result)
        if execution.returncode != 0 and result.get("status") == "offloaded":
            raise _reject("H3_EXECUTION_OUTPUT_INVALID", f"script reported success but exited {execution.returncode}", "Stop after recording the boundary.")
        _validate_success(record, result)
        recovery = [
            {"id": item["id"], "from": item["destination"], "to": item["source"], "size_bytes": item["size_bytes"], "sha256": item["post_sha256"], "method": "mv -n"}
            for item in result["moved"]
        ]
        summary = {
            "schema_version": RUN_SCHEMA, "status": "passed",
            "authorization_verbatim": VERBATIM, "authorization_recorded_utc": APPROVED_AT,
            "repository": identity, "clean_tree_before_attempt": True,
            "host_alias": HOST, "host": before["host"], "user": before["user"],
            "mount": before["mount"],
            "preflight": {"bulk_free_bytes": before["bulk_free_bytes"], "source_filesystem_free_bytes": before["source_filesystem_free_bytes"], "candidates": before["candidates"]},
            "staged_script": stage, "mutation_attempt_count": 1, "result": result,
            "recovery_mapping": recovery, "storage_result_only": True,
            "generation_result": False, "hardware_verdict": False,
            "capability_promotion": False, "downstream_authority": DOWNSTREAM_AUTHORITY,
            "attempt_started_ns": attempt_started, "attempt_finished_ns": time.time_ns(),
        }
        _write_json_once(bundle / "run-summary.json", summary)
        _write_json_once(bundle / "evidence.sha256", _manifest(bundle))
        return summary
    except BaseException as exc:
        error = exc if isinstance(exc, H3OffloadError) else _reject("H3_EXECUTION_CRITICAL", f"{type(exc).__name__}: {exc}", "Stop after recording evidence; no retry.", critical=True)
        _write_json_once(bundle / "failure.json", {
            "schema_version": RUN_SCHEMA, "status": "failed",
            "diagnostic": {"code": error.code, "observed": error.observed, "remediation": error.remediation, "critical": error.critical},
            "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
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
