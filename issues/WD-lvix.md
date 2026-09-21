---
id: WD-lvix
title: "Present actionable failure diagnostics"
status: open
priority: 2
type: feature
labels: [integration]
parent: WD-t534
created_at: 2026-09-21T13:56:16Z
created_by: speed
updated_at: 2026-09-21T13:56:16Z
content_hash: "sha256:201d3ad7aa07cb383f3f5e9a3fe11d234ddfb500a5ac4ede5ff92d2fd1c7879a"
blocks: [WD-carq, WD-fq1o]
was_blocked_by: [WD-fp49]
---

## Description
## USER INTENT
When infrastructure or a declared gate fails, the operator needs a short diagnosis and one safe next command, like an OOM recovery banner. A traceback plus dead-letter row is not production usability.

## Context (Embedded)
- Existing infrastructure checks are typed by `services.jobs.preflight.PreflightCheck(kind, passed, detail)` and reported by `PreflightReport.failed_checks`; kinds are `ssh_reachable`, `model_files`, `disk_headroom`, `gpu_state`, and `qc_available`.
- Model failures already distinguish a missing path from a hash mismatch, including the expected hash prefix. Disk detail already reports available GiB, minimum GiB, and path. These facts need presentation, not new policy.
- Durable queue summary is carried by `JobRecord.failure_class`, `failure_detail`, and `failure_count`; `JobQueue.attempt_history(job_id)` returns immutable rows containing `attempt_no`, `status`, failure class/detail/signature, and timestamps.
- Current accepted failure classes used by the executor include `render_error`, `truncated_render_log`, `preflight`, `qc_gate`, and transport/log failures. Gate evidence paths may already exist in clip/QC records.
- Safe retry commands already exist: `--retry-failed` for eligible failed jobs and `--retry-dead-letter --reason TEXT` for terminal dead letters. The diagnostic must respect `retryable`, repeated-fingerprint protection, and the audited reason requirement; it must never suggest bypassing `allow_deterministic_replay`.
- Diagnostic output must be useful in text and JSON, preserve enough detail for evidence, and avoid leaking secret values. Paths, check kinds, hashes, states, and counts are not secrets.

## OUT OF SCOPE
- Changing any gate threshold, gate order, retry count, dead-letter transition, renderer admission, or provenance rule.
- Automatically deleting files, killing processes, modifying remote hosts, downloading models, or applying a remediation.
- A graphical banner/UI; this story delivers terminal/JSON diagnostics.
- Diagnosing arbitrary unrelated service failures beyond the named infrastructure and gate classes.
- Re-running a render in tests or performing GPU/remote work.

## DIFF BUDGET
- Roughly 7 authored files, under 500 authored changed LOC.

## Boundary Map
PRODUCES:
- wangp/diagnostics.py -> `classify_preflight(report: PreflightReport) -> tuple[FailureDiagnostic, ...]`
- wangp/diagnostics.py -> `classify_queue_failure(record: JobRecord, history: Sequence[Mapping[str, object]]) -> FailureDiagnostic`
- wangp/diagnostics.py -> `render_diagnostic(diagnostic: FailureDiagnostic) -> str`
- docs/troubleshooting.md -> failure-class catalog, exact remediation for each class, and safe retry/resume commands.
- README.md -> troubleshooting section links the diagnostic catalog.
- tests/test_failure_diagnostics.py -> `test_real_queue_failure_emits_remediation_and_resume_hint() -> None`

CONSUMES:
- WD-lhm4: wangp/cli.py -> `main(argv: Sequence[str] | None = None) -> int`
  spec: doctor/status/review catch expected failures at this boundary and render diagnostics using the stable exit-code contract.
- WD-lhm4: wangp/queue_view.py -> `collect_status(db_path: str | Path, *, job_id: str | None = None) -> QueueStatus`
  spec: status/review supply the real JobRecord and attempt history to the classifier.
- WD-fp49: wangp/config.py -> `missing_host_keys(config: HostConfig) -> tuple[str, ...]`
  spec: host diagnostics name the exact unresolved keys and configured source instead of guessing an SSH alias.
- (existing): services/jobs/preflight.py -> `run_preflight(host, *, models: Sequence[dict], min_free_gb: float, disk_path: str, qc_url: str) -> PreflightReport`
  spec: classification consumes failed checks verbatim; it does not rerun probes or mutate admission.
- (existing): services/jobs/queue.py -> `JobQueue.get(self, job_id: str) -> JobRecord`
  spec: real durable state/failure summary source.
- (existing): services/jobs/queue.py -> `JobQueue.attempt_history(self, job_id: str) -> List[Dict]`
  spec: real immutable attempt evidence and retry lineage.

## Required Outcomes
1. `FailureDiagnostic` stably carries diagnostic code, severity, user title, observed fact, concrete remediation, exact next command when safe, machine JSON shape, and evidence references.
2. Host unreachable/unconfigured maps to the resolved target or exact missing configuration keys, points to doctor/configuration remediation, and never emits a raw SSH traceback as the primary user message.
3. Missing model and hash-mismatch diagnostics preserve the full remote/local path and expected hash prefix, identify whether the file is absent or wrong, and point to the model-manifest/doctor command without downloading anything.
4. Disk-headroom diagnostics preserve available bytes/GiB, required minimum, and path, recommend non-destructive space recovery/verification, and never automatically delete artifacts.
5. Gate-rejection diagnostics identify the declared gate, precise recorded rejection reason, relevant evidence path, and `wgp review` command; they explicitly do not offer threshold changes or gate bypass.
6. Failed/dead-letter diagnostics respect `retryable` and attempt history: eligible failed jobs show the existing retry command, dead letters show the audited reason-reopen command, and blocked deterministic replay explains that an effective input must change or explicit replay authorization is required.
7. An unknown failure class still receives a stable generic diagnostic with original class/detail, evidence paths, review command, and a request to file the unknown class rather than pretending to understand it.
8. `wgp doctor`, `wgp status`, and `wgp review` emit these diagnostics consistently in human and JSON modes with no secret values; unexpected exceptions retain the stable internal-error exit code and a concise containment message.
9. Queue rows, attempt rows, failure classes/details, retryability, timestamps, and all gate decisions remain byte-for-byte unchanged by diagnostic rendering.

## Testing Requirements
- Unit: each named class, unknown class, JSON shape, secret redaction, evidence-path preservation, and retry/dead-letter branching.
- Integration: MANDATORY (no mocks). Create a real temporary SQLite queue through `JobQueue`, record genuine failures/attempts with its public APIs, then read it through the CLI/status collector and assert rendered remediation and unchanged database evidence.
- Preflight integration: MANDATORY (no mocks). Build real `PreflightReport` checks for missing model/hash mismatch/low disk from actual local filesystem observations or an explicit host probe is not required; no mocks and no network.
- Invalid brief integration: MANDATORY (no mocks). An actual invalid committed-shaped brief reaches the CLI boundary and renders a typed diagnostic with no traceback.
- Commands: `uv run --frozen --extra dev pytest tests/test_failure_diagnostics.py` and `uv run --frozen --extra dev pytest -q`.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must paste representative text/JSON diagnostics for every named class into notes.
- Developer must include an AC verification table and database before/after hashes or equivalent immutable-evidence proof.
- Developer must use `pvg story deliver`.
- No GPU, SSH, remote mutation, model download, paid hosted service, commit, or push is authorized.

## nd_contract
status: new

### evidence
- Created 2026-09-21 from verified PreflightReport/JobRecord/attempt-history structures and current executor failure classes at main 3094b14.

### proof
- [ ] Pending implementation


## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-21T13:56:16Z dep_added: blocked_by WD-fp49
- 2026-09-21T13:56:16Z dep_added: blocks WD-carq
- 2026-09-21T13:56:17Z dep_added: blocks WD-fq1o
- 2026-09-21T18:46:12Z dep_removed: was_blocked_by WD-fp49

## Links
- Parent: [[WD-t534]]
- Blocks: [[WD-carq]], [[WD-fq1o]]
- Was blocked by: [[WD-fp49]]

## Comments
