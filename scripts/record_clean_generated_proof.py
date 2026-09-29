#!/usr/bin/env python3
"""Run the one operator-authorized clean-machine H3 standard-create proof."""
from __future__ import annotations

import argparse, dataclasses, datetime as dt, hashlib, json, os, re, shlex, shutil, sqlite3, subprocess, sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from services.jobs.preflight import run_preflight
from services.jobs.queue import JobQueue
from scripts.run_jobs import drain_once

BASE = "6ac1023b522726705d3ea560216f211003a1d4bd"
ROOT = Path(__file__).resolve().parents[1]
ACCEPTED = ROOT / "datasets/runs/maestro-parity/WD-isg9/model-assets.json"
ACCEPTED_AUTHORIZATION = ROOT / "datasets/runs/maestro-parity/clean-generated/operator-authorization.json"
PROMPT = ("A concise cinematic test shot: a small brass compass spins slowly on a paper map while cool window light "
          "shifts across the table. Soft cloth and paper sounds, one clear click, no speech.")


class ProofError(RuntimeError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail); self.code, self.detail = code, detail


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load(path: Path) -> Any:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProofError("CLEAN_GENERATED_INPUT_INVALID", f"cannot read {path}: {exc}") from exc


def json_safe(value: Any) -> Any:
    if isinstance(value, Path): return str(value)
    if isinstance(value, dict): return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)): return [json_safe(item) for item in value]
    return value


def record(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.with_name(path.name + ".tmp").write_text(json.dumps(json_safe(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.with_name(path.name + ".tmp").replace(path)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""): digest.update(block)
    return digest.hexdigest()


def run(argv: Sequence[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(argv), cwd=None if cwd is None else str(cwd), text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def git(checkout: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    return run(("git", "-C", str(checkout), *argv))


def fail(proof: Path | None, code: str, detail: str, command: Sequence[str]) -> int:
    if proof is not None:
        record(proof / "failure.json", {
            "schema_version": "wangp-dspy.clean-generated-proof-failure/v1",
            "diagnostic": {"code": code, "detail": detail}, "command": list(command),
            "generated_artifact": False, "substitution_attempted": False,
        })
    print(f"GENERATED_PROOF_FAILED code={code}\ndiagnostic={detail}", file=sys.stderr)
    return 4


def inputs(authorization: Any, manifest: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    fixed = {"schema_version": "wangp-dspy.clean-generated-authorization/v1", "status": "approved",
             "text": "Approve", "timestamp": "2026-09-28T13:20:11Z", "base_commit": BASE}
    operation = {"family": "minimax_h3", "preset": "standard", "operation": "create", "render_count": 1}
    boundaries = {"downloads": 0, "provider_spend": False, "training": False, "registry_publication": False, "gui": False,
                  "tag_creation": False, "protected_engine_change": False, "threshold_change": False, "deletions": 0, "second_render": False}
    valid = (isinstance(authorization, dict) and all(authorization.get(k) == v for k, v in fixed.items())
             and authorization.get("allowed_operation") == operation
             and authorization == load(ACCEPTED_AUTHORIZATION)
             and authorization.get("boundaries") == boundaries
             and len(authorization.get("superseded_relocations", [])) == 2)
    if not valid: raise ProofError("CLEAN_GENERATED_INPUT_INVALID", "authorization boundary mismatch")
    if manifest != load(ACCEPTED) or len(manifest.get("assets", [])) != 4:
        raise ProofError("CLEAN_GENERATED_INPUT_INVALID", "model manifest must equal the accepted four-asset H3 manifest")
    return authorization, manifest["assets"]


def repository(checkout: Path) -> tuple[str, str, str]:
    commit, status, ancestry = git(checkout, "rev-parse", "HEAD"), git(checkout, "status", "--porcelain=v1"), git(checkout, "merge-base", "--is-ancestor", BASE, "HEAD")
    if commit.returncode or status.returncode or ancestry.returncode or status.stdout.strip():
        raise ProofError("REPOSITORY_DIRTY", "clean checkout identity or authorized ancestry is invalid")
    identity = hashlib.sha256((commit.stdout + "\0" + status.stdout).encode()).hexdigest()
    return commit.stdout.strip(), status.stdout, identity


def tools() -> dict[str, str]:
    result = {"python": sys.version.replace("\n", " ")}
    for name in ("git", "ffmpeg", "ffprobe"):
        probe = run((name, "--version" if name == "git" else "-version"))
        if probe.returncode: raise ProofError("LOCAL_TOOL_MISSING", f"{name} version probe failed")
        result[name] = probe.stdout.splitlines()[0]
    return result


def render_host(config: Mapping[str, Any]) -> Any:
    from wangp.config import HostConfig, HostSetting, render_host
    root = Path(config["wgp_root"])
    def item(key: str, value: str) -> HostSetting:
        return HostSetting(key=key, value=value, source="clean_generated_authorization", origin=None if key == "host.target" else root)
    return render_host(HostConfig(
        target=item("host.target", config["target"]), wgp_root=item("host.wgp_root", config["wgp_root"]),
        pull_root=item("host.pull_root", config["pull_root"]),
        wgp_python=item("host.wgp_python", config["wgp_python"]), repository_root=ROOT,
        repository_config=ROOT / "wangp.toml",
        user_config=Path(os.environ.get("WANGP_CONFIG", "/nonexistent/wangp/config.toml")),
    ))


def probe(host: Any, argv: Sequence[str], timeout: int = 120) -> tuple[int, str, str]:
    return host.run_probe(list(argv), timeout=timeout)


def push(host: Any, proof: Path, name: str, body: str) -> str:
    local = proof / "remote-scripts" / name
    local.parent.mkdir(parents=True, exist_ok=True); local.write_text(body, encoding="utf-8")
    remote = f"{load(proof / 'inputs/resolved-host.json')['remote_work_root']}/{name}"
    rc, _out, err = probe(host, ("mkdir", "-p", str(Path(remote).parent)))
    if rc: raise ProofError("HOST_STAGE_FAILED", err.strip())
    remote = host.push_file(str(local), remote)
    rc, _out, err = probe(host, ("chmod", "700", remote))
    if rc: raise ProofError("HOST_STAGE_FAILED", err.strip())
    return remote


def free(host: Any, path: str) -> int:
    rc, out, err = probe(host, ("df", "-B1", "--output=avail", path)); match = re.search(r"\d+", out or "")
    if rc or not match: raise ProofError("HOST_PREFLIGHT_FAILED", f"cannot inspect {path}: {err.strip()}")
    return int(match.group())


def relocate(host: Any, proof: Path, auth: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    floor = int(config["min_free_gb"]) * 1000**3; before = free(host, config["wgp_root"])
    moves: list[dict[str, Any]] = []
    if before < floor:
        if probe(host, ("mkdir", "-p", config["offload_root"]))[0]: raise ProofError("STORAGE_PREPARATION_FAILED", "cannot create offload root")
        if free(host, config["offload_root"]) < sum(int(x["size_bytes"]) for x in auth["superseded_relocations"]) + 1024**3:
            raise ProofError("STORAGE_PREPARATION_FAILED", "offload lacks verified-copy headroom")
        for item in auth["superseded_relocations"]:
            source, size = str(item["source"]), int(item["size_bytes"]); destination = f"{config['offload_root']}/{Path(source).name}"
            (proof / "storage").mkdir(parents=True, exist_ok=True)
            body = "\n".join([
                "#!/bin/bash", "set -euo pipefail", f"src={shlex.quote(source)}",
                f"tmp={shlex.quote(destination + '.part')}", f"dest={shlex.quote(destination)}", f"size={size}",
                'test -f "$src" && test ! -e "$tmp" && test ! -e "$dest"',
                'test "$(stat -c %s "$src")" -eq "$size"',
                'before=$(sha256sum "$src" | awk "{print \\$1}")',
                'cp --reflink=never --sparse=always "$src" "$tmp"',
                'test "$(stat -c %s "$tmp")" -eq "$size"',
                'after=$(sha256sum "$tmp" | awk "{print \\$1}") && test "$before" = "$after"',
                'mv "$tmp" "$dest" && unlink "$src"',
                'printf "source=%s\\ndestination=%s\\nsize=%s\\nbefore=%s\\nafter=%s\\nverified_copy_before_unlink=true\\n" "$src" "$dest" "$size" "$before" "$after"',
            ]) + "\n"
            name = f"relocate-{Path(source).name}.sh"; script = push(host, proof, name, body)
            rc, out, err = probe(host, ("bash", script), timeout=1800)
            (proof / "storage" / Path(source).name).write_text(f"exit={rc}\n{out}\n{err}", encoding="utf-8")
            if rc: raise ProofError("STORAGE_PREPARATION_FAILED", f"verified relocation failed: {err.strip()}")
            moves.append({"source": source, "destination": destination, "size_bytes": size, "script": name})
    after = free(host, config["wgp_root"])
    result = {"needed": before < floor, "root_free_before": before, "root_free_after": after,
              "minimum": floor, "relocations": moves, "deletions": 0}
    record(proof / "storage/relocation.json", result)
    if after < floor: raise ProofError("STORAGE_PREPARATION_FAILED", "root still below 50 GB floor")
    return result


def models(host: Any, proof: Path, assets: Sequence[Mapping[str, Any]], config: Mapping[str, Any]) -> list[dict[str, Any]]:
    lines = ["#!/bin/bash", "set -euo pipefail"]
    for asset in assets:
        path = shlex.quote(str(asset["destination"]))
        lines += [f"printf '%s\\t' {path}", f"stat -c '%s\\t%y\\t' {path} | tr '\\n' '\\t'", f"sha256sum {path} | awk '{{print $1}}'"]
    script = push(host, proof, "verify-models.sh", "\n".join(lines) + "\n")
    rc, out, err = probe(host, ("bash", script), timeout=900)
    (proof / "preflight").mkdir(parents=True, exist_ok=True)
    (proof / "preflight/model-hash-size-raw.txt").write_text(f"exit={rc}\n{out}\n{err}", encoding="utf-8")
    rows = [line for line in out.splitlines() if line.strip()]
    if rc or len(rows) != 4: raise ProofError("MODEL_PREFLIGHT_FAILED", err.strip() or "expected four model rows")
    observed = []
    for asset, row in zip(assets, rows, strict=True):
        path, size, mtime, digest = [part.strip() for part in row.split("\t", 3)]
        if path != asset["destination"] or int(size) != asset["size_bytes"] or digest != asset["sha256"]:
            raise ProofError("MODEL_PREFLIGHT_FAILED", f"model identity mismatch: {asset['id']}")
        observed.append({**asset, "observed_size_bytes": int(size), "observed_mtime": mtime, "observed_sha256": digest})
    report = run_preflight(host, models=[{"path": a["destination"], "sha256": a["sha256"]} for a in assets],
                           min_free_gb=float(config["min_free_gb"]), disk_path=config["wgp_root"], qc_url=config["qc_url"])
    payload = {"passed": report.passed, "checks": [vars(x) for x in report.checks], "detail": report.detail}
    record(proof / "preflight/report.json", payload)
    if not report.passed: raise ProofError("HOST_PREFLIGHT_FAILED", report.detail)
    return observed


def offline_wrapper(host: Any, proof: Path, config: Mapping[str, Any]) -> tuple[str, str]:
    body = f"#!/bin/bash\nset -euo pipefail\nexport HF_HUB_OFFLINE=1\nexport TRANSFORMERS_OFFLINE=1\nexec {shlex.quote(config['wgp_python'])} \"$@\"\n"
    remote = push(host, proof, "offline-python.sh", body)
    rc, out, err = probe(host, (remote, "-c", "import sys; print(sys.executable)"))
    if rc or out.strip() != config["wgp_python"]: raise ProofError("OFFLINE_WRAPPER_INVALID", err.strip())
    return remote, sha(proof / "remote-scripts/offline-python.sh")


def queue_state(database: Path, job_id: str) -> dict[str, Any]:
    with sqlite3.connect(database) as db:
        db.row_factory = sqlite3.Row
        return {
            "attempts": [dict(x) for x in db.execute("SELECT * FROM job_attempts WHERE job_id=? ORDER BY attempt_id", (job_id,))],
            "failures": [dict(x) for x in db.execute("SELECT * FROM job_attempt_failures WHERE job_id=? ORDER BY id", (job_id,))],
        }


def render(host: Any, proof: Path) -> tuple[str, dict[str, Any]]:
    clip = {"clip_index": 1, "status": "pending", "log": None, "mp4": None, "qc_verdict": None,
            "kind": "video_generation", "family": "minimax_h3", "preset": "standard", "operation": "create",
            "prompt": PROMPT, "frames": 56, "video_length": 56, "resolution": [480, 832], "steps": 20,
            "model_type": "minimax_h3_fl2va_pruned"}
    database = proof / "queue.db"; queue = JobQueue(database)
    try:
        job_id = queue.submit(plan_ref="WD-bw0h-clean-generated-h3-standard-create", clips=[clip])
        record(proof / "queue/initial.json", {"job_id": job_id, "state": "pending", "clips": [clip], **queue_state(database, job_id)})
        drain_once(queue, host=host); job = queue.get(job_id)
        record(proof / "queue/final.json", {"job_id": job_id, "state": job.state, "clips": job.clips, **queue_state(database, job_id)})
        if job.state != "done" or len(job.clips) != 1 or job.clips[0].get("render_attempted") is not True:
            raise ProofError("GENERATION_FAILED", f"queue did not complete exactly one render: {job.state}")
        return job_id, job.clips[0]
    finally: queue.close()


def ffprobe(path: Path) -> dict[str, Any]:
    result = run(("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)))
    if result.returncode: raise ProofError("MEDIA_GATE_FAILED", result.stderr.strip())
    return json.loads(result.stdout)


def media(proof: Path, path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    probe = ffprobe(path); (proof / "outputs").mkdir(parents=True, exist_ok=True)
    (proof / "outputs/wd_bw0h_h3_standard_create.ffprobe.json").write_text(json.dumps(probe, indent=2) + "\n", encoding="utf-8")
    video = next(x for x in probe["streams"] if x["codec_type"] == "video")
    audio = next(x for x in probe["streams"] if x["codec_type"] == "audio")
    rate = [float(x) for x in video["avg_frame_rate"].split("/")]
    first, contact = proof / "outputs/first-frame.png", proof / "outputs/contact-sheet.jpg"
    for argv in (("-i", str(path), "-frames:v", "1", str(first)),
                 ("-i", str(path), "-vf", "fps=2,scale=320:-1,tile=3x2", "-frames:v", "1", str(contact))):
        result = run(("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *argv))
        if result.returncode: raise ProofError("MEDIA_GATE_FAILED", result.stderr.strip())
    black = run(("ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf", "blackdetect=d=0.1:pix_th=0.05", "-an", "-f", "null", "-"))
    (proof / "outputs/blackdetect.txt").write_text(black.stderr, encoding="utf-8")
    metadata = {"width": video["width"], "height": video["height"], "duration_s": float(probe["format"]["duration"]),
                "fps": rate[0] / rate[1], "audio": {"present": True, "codec": audio["codec_name"],
                "sample_rate_hz": audio["sample_rate"], "channels": audio["channels"]}}
    output = [{"path": "outputs/wd_bw0h_h3_standard_create.mp4", "sha256": sha(path)}]
    media_row = [{"path": output[0]["path"], "kind": "video", "alpha_mode": "none", **metadata}]
    values = [metadata["duration_s"], metadata["fps"], float(path.stat().st_size),
              float(len(re.findall("black_start:", black.stderr))), float(audio["sample_rate"]), float(audio["channels"])]
    names = ["duration_s", "fps", "nonempty_bytes", "black_intervals", "audio_sample_rate_hz", "audio_channels"]
    thresholds = [2.0, 24.0, 500000.0, 0.0, 32000.0, 2.0]
    checks = [values[index] == thresholds[index] if name in {"fps", "audio_sample_rate_hz", "audio_channels", "black_intervals"}
              else values[index] >= thresholds[index] for index, name in enumerate(names)]
    gates = [{"name": f"h3_standard_create_{name}", "inputs": [output[0]["path"], "outputs/blackdetect.txt"],
              "threshold": thresholds[index], "measured": values[index], "verdict": "pass" if ok else "fail"}
             for index, (name, ok) in enumerate(zip(names, checks, strict=True))]
    record(proof / "objective-gates.json", gates)
    record(proof / "review/visual-hashes.json", {"first_frame_sha256": sha(first), "contact_sheet_sha256": sha(contact)})
    return output, media_row, gates


def evidence(proof: Path, command: Sequence[str], commit: str, identity: str, auth: Mapping[str, Any],
             model_rows: Sequence[Mapping[str, Any]], storage: Mapping[str, Any], job_id: str,
             output: Sequence[Mapping[str, Any]], media_rows: Sequence[Mapping[str, Any]], gates: Sequence[Mapping[str, Any]]) -> None:
    reviewer = {"decision": "approved", "reviewer": "mechanical objective-gate reviewer; nd acceptance remains pending",
                "reviewed_at": now(), "reviewed_commit": commit,
                "evidence_links": ["objective-gates.json", "preflight/report.json", "queue/final.json", "review/visual-hashes.json"],
                "summary": "All six objective gates pass on one fresh nonempty artifact; this is not story acceptance."}
    record(proof / "reviewer-verdict.json", reviewer)
    record(proof / "evidence.json", {
        "schema": "wangp-dspy.maestro-parity-evidence/v1",
        "operator_authorization": {k: auth[k] for k in ("status", "text", "scope", "timestamp", "approved_by")},
        "command": list(command), "repository": {"commit": commit, "dirty_state": {"dirty": False, "identity_sha256": identity}},
        "model_provenance": [{**dict(x), "download_approved": True, "download_bytes": 0} for x in model_rows],
        "reference_provenance": [
            {"path": "inputs/model-assets.json", "role": "authorized_four_asset_manifest", "sha256": sha(proof / "inputs/model-assets.json"), "license": "Operator authorization; no redistribution"},
            {"path": "inputs/operator-authorization.json", "role": "operator_authorization_and_host", "sha256": sha(proof / "inputs/operator-authorization.json"), "license": "Operator authorization; no redistribution"},
        ],
        "queue_attempt": {"queue_id": "wangp-JobQueue-WD-bw0h-clean-generated", "job_id": job_id, "retry_id": "attempt-1",
                          "admission_state": "admitted", "exit_status": "succeeded", "database": "queue.db",
                          "preflight": "preflight/report.json", "native_logs": ["host-logs/render.log"],
                          "native_log_sha256": {"host-logs/render.log": sha(proof / "host-logs/render.log")}},
        "output": list(output), "media_metadata": list(media_rows), "objective_gate_results": list(gates),
        "reviewer_verdict": reviewer,
        "runtime_notes": {"clean_workspace": str(proof.parent), "storage_relocation": storage, "model_download_bytes": 0,
                          "provider_spend": False, "training": False, "render_count": 1, "protected_engine_changes": 0,
                          "threshold_changes": 0, "deletions": 0,
                          "offline_environment": {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}},
    })


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); proof: Path | None = None; command: list[str] = []
    parser.add_argument("--proof-dir", required=True, type=Path); parser.add_argument("--checkout", required=True, type=Path)
    parser.add_argument("--installer", required=True, type=Path); parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--model-manifest", required=True, type=Path); args = parser.parse_args(argv)
    try:
        auth, assets = inputs(load(args.authorization), load(args.model_manifest))
        checkout = args.checkout.resolve()
        if any(not path.resolve().is_relative_to(checkout) for path in (args.authorization, args.model_manifest)):
            raise ProofError("CLEAN_GENERATED_INPUT_INVALID", "inputs must live inside the disposable checkout")
        commit, status, identity = repository(args.checkout); toolset = tools(); proof = args.proof_dir
        command = ["sh", str(args.installer), *[x.decode() for x in (proof / "argv.nul").read_bytes().split(b"\0") if x]]
        proof.mkdir(parents=True, exist_ok=True); (proof / "inputs").mkdir(parents=True, exist_ok=True)
        for source, name in ((args.authorization, "operator-authorization.json"), (args.model_manifest, "model-assets.json")):
            shutil.copyfile(source, proof / "inputs" / name)
        config = dict(auth["allowed_host"]); config["pull_root"] = config["pull_root"].replace("{WORKSPACE}", str(proof.parent.resolve()))
        record(proof / "inputs/resolved-host.json", config)
        record(proof / "workspace.json", {"workspace": proof.parent, "checkout": checkout, "commit": commit,
                                           "status": status, "identity_sha256": identity, "tools": toolset, "command": command})
        os.environ.update({"WANGP_SSH_TARGET": config["target"], "WANGP_WGP_ROOT": config["wgp_root"],
                           "WANGP_PULL_ROOT": config["pull_root"], "WANGP_WGP_PYTHON": config["wgp_python"],
                           "WANGP_QC_URL": config["qc_url"]})
        host = render_host(config); storage = relocate(host, proof, auth, config); model_rows = models(host, proof, assets, config)
        wrapper, wrapper_hash = offline_wrapper(host, proof, config); os.environ["WANGP_WGP_PYTHON"] = wrapper
        record(proof / "offline-wrapper.json", {"path": wrapper, "sha256": wrapper_hash,
                                                "environment": {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}})
        job_id, clip = render(host, proof); local = proof / "outputs/wd_bw0h_h3_standard_create.mp4"
        host.fetch_file(host.map_path(clip["mp4"]), str(local)); settings, log = Path(clip["mp4"]).parent / "settings.json", Path(clip["log"])
        (proof / "host-logs").mkdir(parents=True, exist_ok=True)
        host.fetch_file(host.map_path(str(log)), str(proof / "host-logs/render.log"))
        host.fetch_file(host.map_path(str(settings)), str(proof / "host-logs/settings.json"))
        from host.wangp_adapter import build_detached_wgp_argv
        argv_record = build_detached_wgp_argv(host.map_path(str(settings)), host.map_path(str(log)),
                                               wangp_dir=config["wgp_root"], wgp_python=wrapper,
                                               wgp_script=f"{config['wgp_root']}/wgp.py", profile="3")
        (proof / "host-logs/native.argv.txt").write_text(shlex.join(argv_record) + "\n", encoding="utf-8")
        if not local.is_file() or local.stat().st_size == 0: raise ProofError("GENERATION_FAILED", "renderer returned no artifact")
        output, media_rows, gates = media(proof, local)
        if any(x["verdict"] != "pass" for x in gates): raise ProofError("OBJECTIVE_GATE_FAILED", "one or more objective gates failed")
        evidence(proof, command, commit, identity, auth, model_rows, storage, job_id, output, media_rows, gates)
        check = proof / "checker"; check.mkdir(parents=True, exist_ok=True)
        result = run((sys.executable, str(args.checkout / "scripts/verify_maestro_parity.py"), str(proof)))
        (check / "result.txt").write_text(f"exit={result.returncode}\n{result.stdout}\n{result.stderr}", encoding="utf-8")
        if result.returncode: raise ProofError("CANONICAL_CHECKER_FAILED", result.stderr.strip()[:1000])
        print(f"CLEAN_GENERATED workspace={proof.parent} commit={commit} job_id={job_id}")
        print(f"ARTIFACT path={local} bytes={local.stat().st_size} sha256={output[0]['sha256']}")
        print(f"CANONICAL_CHECKER {result.stdout.strip()}")
        return 0
    except ProofError as exc: return fail(proof, exc.code, exc.detail, command)
    except Exception as exc: return fail(proof, "UNEXPECTED_GENERATED_PROOF_FAILURE", f"{type(exc).__name__}: {exc}", command)


if __name__ == "__main__": raise SystemExit(main())
