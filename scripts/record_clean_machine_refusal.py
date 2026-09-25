#!/usr/bin/env python3
"""Record a no-GPU clean-machine plan and typed generation refusal."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from wangp.diagnostics import FailureDiagnostic, render_diagnostic


SCHEMA = "wangp-dspy.clean-machine-proof/v1"
EXPECTED_SUMMARY = {
    "clip_count": 4,
    "speakers": ["Tess", "Rho", "Tess", "Rho"],
    "planned_duration_s": 9.332,
    "dry_run": True,
    "gpu_work": False,
    "queue_submitted": False,
}
OPERATOR_REQUIREMENTS = (
    "per-batch GPU/render-host authorization",
    "model-download approval",
    "complete authorized host/model manifest with identity, source, hash or immutable version, license, and usage constraint",
)


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _from_mapping(raw: Mapping[str, Any]) -> FailureDiagnostic:
    return FailureDiagnostic(
        code=str(raw["code"]),
        severity=str(raw["severity"]),
        title=str(raw["title"]),
        observed=str(raw["observed"]),
        why=str(raw["why"]),
        remediation=str(raw["remediation"]),
        next_command=raw.get("next_command"),
        evidence_refs=tuple(str(item) for item in raw.get("evidence_refs", ())),
        metadata=dict(raw.get("metadata", {})),
    )


def _host_diagnostic(report: Mapping[str, Any]) -> FailureDiagnostic:
    diagnostics = report.get("diagnostics")
    if (
        isinstance(diagnostics, list)
        and diagnostics
        and isinstance(diagnostics[0], dict)
    ):
        return _from_mapping(diagnostics[0])
    return FailureDiagnostic(
        "HOST_AUTHORIZATION_REQUIRED", "error",
        "Render host is configured but this batch is not authorized",
        "complete host settings found; no per-batch operator authorization was supplied",
        "A configured machine is not authority to start GPU work or admit a render job.",
        "Record per-batch authorization, scope, timestamp, approver, command boundary, and host identity, then use the separately authorized generation command.",
        "wgp doctor", ("host-refusal.json",),
    )


def _model_diagnostic(report: Mapping[str, Any]) -> FailureDiagnostic:
    manifest = report.get("model_manifest")
    status = manifest.get("status") if isinstance(manifest, dict) else "absent"
    if status != "present":
        return FailureDiagnostic(
            "MODEL_MANIFEST_REQUIRED", "error",
            "Generation model manifest is absent",
            "model manifest absent; zero authorized model identities are recorded",
            "Wangp cannot infer which model bytes, licences, or destinations a render may use.",
            "Supply a complete wangp-dspy.model-assets/v1 manifest for every required model with id, source URL, SHA-256, exact size, license, and absolute destination; then record explicit model-download approval. Wangp does not download models.",
            "wgp doctor --capabilities --models <manifest> --json",
            ("capabilities.json",), {"model_count": 0},
        )
    entries = manifest.get("entries", [])
    pending = [
        str(item.get("id", f"entry-{index}"))
        for index, item in enumerate(entries)
        if isinstance(item, dict) and item.get("status") != "complete"
    ]
    return FailureDiagnostic(
        "MODEL_AUTHORIZATION_REQUIRED", "error",
        "Generation models are not authorized for this batch",
        f"model manifest present; {len(pending)} of {len(entries)} entries are not complete",
        "Model presence alone is not download approval or per-batch authorization.",
        "For each pending model, preserve the exact bytes, verify the recorded SHA-256, and record per-batch download/use authorization. Wangp does not download or substitute models.",
        "wgp first-run download --manifest <manifest> --state <state>",
        ("capabilities.json",), {"pending_models": pending},
    )


def _invalid(message: str, source: str) -> int:
    diagnostic = FailureDiagnostic(
        "CLEAN_PROOF_INPUT_INVALID", "error",
        "Clean-machine proof inputs are invalid", message,
        "The refusal recorder cannot honestly attribute malformed generated outputs.",
        "Rerun the documented clean-machine command without altering its outputs.",
        "sh install.sh --clean-proof <absent-workspace>", (source,),
    )
    print(render_diagnostic(diagnostic), file=sys.stderr)
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof-dir", required=True, type=Path)
    parser.add_argument("--source", required=True)
    parser.add_argument("--clone-source", required=True)
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--installer", required=True, type=Path)
    arguments = parser.parse_args()
    proof = arguments.proof_dir
    try:
        plan = _json(proof / "plan.json")
        host = _json(proof / "host-refusal.json")
        capabilities = _json(proof / "capabilities.json")
        commit = _text(proof / "resolved-commit.txt")
        status = _text(proof / "repository-status.txt")
        raw_argv = (proof / "argv.nul").read_bytes()
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return _invalid(str(exc), str(proof))
    if not isinstance(plan, dict) or plan.get("schema_version") != "wangp-dspy.content-plan/v1":
        return _invalid("plan schema is not wangp-dspy.content-plan/v1", str(proof / "plan.json"))
    if plan.get("summary") != EXPECTED_SUMMARY:
        return _invalid(f"unexpected plan summary: {plan.get('summary')!r}", str(proof / "plan.json"))
    repository = plan.get("repository")
    if not isinstance(repository, dict) or repository.get("commit_sha") != commit or repository.get("clean_tree") is not True:
        return _invalid("plan repository identity does not match the disposable checkout", str(proof / "plan.json"))

    argv = [part.decode("utf-8") for part in raw_argv.split(b"\0") if part]
    changed = [line for line in status.splitlines() if line.strip()]
    diagnostics = [
        _host_diagnostic(host if isinstance(host, dict) else {}),
        _model_diagnostic(capabilities if isinstance(capabilities, dict) else {}),
    ]
    payload = {
        "schema_version": SCHEMA,
        "outcome": "plan_emitted_generation_refused",
        "command": ["sh", str(arguments.installer), *argv],
        "source": {
            "selected": arguments.source,
            "clone_source": arguments.clone_source,
            "checkout": arguments.checkout,
            "resolved_commit": commit,
            "dirty_tree": bool(changed),
            "changed_paths": changed,
        },
        "tools": {
            "git": _text(proof / "git-version.txt"),
            "uv": _text(proof / "uv-version.txt"),
        },
        "installer_sha256": _sha256(arguments.installer),
        "plan": {
            "path": str(proof / "plan.json"),
            "sha256": _sha256(proof / "plan.json"),
            "schema_version": plan["schema_version"],
            "summary": plan["summary"],
        },
        "generation": {
            "attempted": False,
            "queue_admitted": False,
            "ssh_contacted": False,
            "model_downloaded": False,
            "generated_media_bytes": 0,
            "generated_artifact": False,
            "host_run_verified": False,
        },
        "blocked_operator_inputs": list(OPERATOR_REQUIREMENTS),
        "diagnostics": [diagnostic.mapping() for diagnostic in diagnostics],
    }
    output = proof / "blocked-record.json"
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)
    print(f"PLAN_ONLY path={proof / 'plan.json'} generated_artifact=false")
    print(f"GENERATION_REFUSED diagnostics={len(diagnostics)} exit=3")
    for diagnostic in diagnostics:
        print(render_diagnostic(diagnostic), file=sys.stderr)
    print(f"blocked_record={output}", file=sys.stderr)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
