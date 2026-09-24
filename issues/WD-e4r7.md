---
id: WD-e4r7
title: "Bug: make GPU preflight fail closed for occupied compute processes"
status: open
priority: 0
type: bug
labels: [bug, host-safety, integration]
parent: WD-3nod
created_at: 2026-09-24T21:11:25Z
created_by: speed
updated_at: 2026-09-24T21:11:47Z
content_hash: "sha256:d337b8809000f700a68389815130a65c615c41964f5b20648205d8d0c840f214"
blocks: [WD-fay0]
---

## Description
## Context (Embedded)
- Defect discovered during the first authorized host batch, story WD-m0r5, on the RTX 3090 render host.
- At main `8f0b225`, `services/jobs/preflight.py:54` uses `_GPU_PROC_RE = re.compile(r"^\s*(\d+)\s+\S+", re.M)`, which recognizes whitespace-separated output but not comma-separated `nvidia-smi` CSV.
- The probe at `services/jobs/preflight.py:109-122` asks `nvidia-smi` for CSV but returns `gpu_state` as passing with detail `idle` when that regex does not match.
- Captured real host output was exactly: `1007225, 7808 MiB, /home/straughter/llama.cpp/build/bin/llama-server`. The 24576 MiB RTX 3090 had 7808 MiB held by PID 1007225, yet governed preflight printed `gpu_state=idle`.
- Consequence: a governed render can be admitted onto an occupied GPU. This is a fail-open admission correctness defect, not a feature request or capacity optimization.
- The GPU holder was terminated afterward with explicit operator authorization. The defect is latent and no longer blocks the current batch, but it must be fixed before future authorized host work relies on preflight.
- Parent choice: WD-3nod is the only open epic and owns the host-gated Maestro parity generation-evidence programme; WD-m0r5, where the defect was observed, is its child. No open preflight-specific epic exists, so this safety bug belongs where the authorized host-run programme will actually be dispatched.

## USER INTENT
The operator needs host preflight to refuse admission whenever another compute process holds the render GPU, with evidence identifying that process, so authorized parity renders cannot silently share an occupied GPU.

## Root Cause
GPU-state detection regexes only the legacy whitespace row shape and treats every nonmatching successful `nvidia-smi` response as idle. Successful but unparseable output therefore becomes a silently passing admission check instead of a failed check.

## Affected Components
- `services/jobs/preflight.py`
- `tests/test_jobs_preflight.py`
- Existing governed queue admission behavior that consumes `PreflightReport`

## PROTECTED ENGINE FILE — REQUIRED, NARROW CHANGE
- `services/jobs/preflight.py` is a PROTECTED ENGINE FILE. Protection is a review boundary, not an absolute ban.
- A protected-file change is required here because `_probe_gpu` currently produces a false `idle` admission verdict from real CSV output. Parser and check semantics cannot be corrected elsewhere without bypassing the admission boundary.
- The change must remain limited to GPU CSV parsing, structured occupancy state, and `gpu_state` verdict mapping. Do not refactor queue, render policy, wiring, or runtime admission.
- Delivery must state the exact accepted head and include the explicit differential `git diff 8f0b225..HEAD -- services/jobs/preflight.py`. The independent PM-Acceptor must verify the delivered tests and gates at that exact head before acceptance; if the head is rebased or changed, evidence and independent acceptance must be rerun.
- All other protected engine files — `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, and `scripts/run_film.py` — must remain unchanged from `8f0b225`.

## OUT OF SCOPE
- Killing, restarting, leasing, or otherwise managing GPU processes: preflight only detects and reports; any intervention requires separate explicit operator authorization.
- Capacity-based partial admission or memory thresholds: this story treats any parsed compute process holding memory as occupied; a capacity policy requires separate triage.
- A general `nvidia-smi` query framework or vendor-version matrix: only the compute-apps fields needed for fail-closed occupancy are in scope.
- GPU rendering, model downloads, host mutation, or live creation of an occupant: tests use the authorized captured real output and deterministic malformed inputs; they must not disturb the host.
- Queue-state machine, renderer selection, spend gates, or parity evidence semantics: those remain governed by their existing stories.

## DIFF BUDGET
- About 2 files and under 180 authored changed LOC: the focused preflight parser/state/check change plus direct parser and check-mapping regressions.
- Documentation changes are not expected; add one only if the implemented `gpu_state` detail contract materially changes.

## Boundary Map
PRODUCES:
- services/jobs/preflight.py -> `GpuComputeProcess` dataclass
  spec: frozen dataclass with `pid: int`, `memory_mib: int`, and `process_name: str`.
- services/jobs/preflight.py -> `GpuComputeState` dataclass
  spec: frozen dataclass with `verdict: Literal["idle", "occupied", "unknown"]`, `processes: tuple[GpuComputeProcess, ...]`, and `reason: str = ""`.
- services/jobs/preflight.py -> `_parse_gpu_compute_apps(output: str) -> GpuComputeState`
  event: parse exact captured CSV rows into structured process entries; recognize the genuine no-process response as idle; return `unknown` with a precise reason for empty-but-unexpected, malformed, missing-field, non-integer-memory, or alternate-column output.
- services/jobs/preflight.py -> `_gpu_check_from_state(state: GpuComputeState) -> PreflightCheck`
  event: return passing `gpu_state` only for `idle`; return a failing check with every observed PID, MiB value, and process name for `occupied`, and a failing fail-closed check for `unknown`.
- services/jobs/preflight.py -> `_probe_gpu(host) -> PreflightCheck`
  spec: existing host-seam signature, updated to request `pid,used_memory,process_name`, parse successful output through `_parse_gpu_compute_apps`, preserve failure on nonzero `nvidia-smi` return code, and never default successful unparseable output to idle.
- tests/test_jobs_preflight.py -> direct no-mock regressions for captured CSV, malformed/alternate columns, genuine idle, and check mapping.

CONSUMES:
- (existing): services/jobs/preflight.py -> `_safe_probe(host, argv, timeout=PROBE_TIMEOUT_SECS) -> tuple[int, str, str]`
  source: existing host-seam error wrapper; retain its nonzero/exception fail-closed behavior.
- (existing): services/jobs/preflight.py -> `run_preflight(host, *, models: Sequence[dict], min_free_gb: float, disk_path: str, qc_url: str) -> PreflightReport`
  source: existing admission entry point; its failed-check aggregation must continue to make a failed `gpu_state` refuse admission.
- (existing): host/render_host.py -> `SshHost.run_probe(argv, timeout) -> (rc, stdout, stderr)`
  source: production host seam; no duplicate host command path or SSH logic may be introduced.

## Story Acceptance Criteria
1. [State] The GPU probe requests `nvidia-smi --query-compute-apps=pid,used_memory,process_name --format=csv,noheader`, and the exact captured row `1007225, 7808 MiB, /home/straughter/llama.cpp/build/bin/llama-server` parses into a structured entry with `pid=1007225`, `memory_mib=7808`, and the exact process path.
2. [Unwanted] Whenever at least one parsed compute process holds memory, `gpu_state` does not report idle: the check fails and its detail names every observed PID, memory in MiB, and process name.
3. [Unwanted] An unparseable, empty-but-unexpected, alternate-column, missing-memory, or otherwise successful-but-unrecognized `nvidia-smi` shape returns `unknown` and fails admission; it never falls back to idle. A nonzero probe return code also continues to fail.
4. [State] A genuine no-compute-process response — specifically empty output or `No running processes found` — remains passing `gpu_state` with idle detail, and existing no-process preflight behavior is otherwise unchanged.
5. [State] Tests invoke `_parse_gpu_compute_apps` directly with the byte-for-byte captured real RTX 3090 output and with a malformed/alternate-column negative input, without host mocks; separate state-to-check assertions prove occupied and unknown both fail while genuine idle passes.
6. [State] Standing gates pass at the exact delivered head: targeted preflight tests; full suite with parsed JUnit `errors=0` and `failures=0`; `uv run --frozen --extra dev wgp release verify` reporting `release=ready` and `tag_created=false`; explicit preflight protected-file differential against `8f0b225`; unchanged differential for the other four protected files; and `git diff --check`.

## Testing Requirements
- Direct parser integration, MANDATORY with no mocks for the parser: use the exact authorized captured output above and assert the complete structured entry.
- Negative parser test: malformed and alternate-column output (for example memory before PID, or PID plus process path without memory) yields `unknown`, not idle, with a useful reason.
- Genuine-idle regression: assert both empty output and `No running processes found` yield idle/pass.
- Check-mapping tests: assert occupied detail contains PID 1007225, `7808` MiB, and `/home/straughter/llama.cpp/build/bin/llama-server`; unknown fails closed; idle alone passes. Nonzero `nvidia-smi` return remains a failed check.
- Commands: run targeted `uv run --frozen --extra dev pytest -q tests/test_jobs_preflight.py`, full `uv run --frozen --extra dev pytest -q --junitxml=/tmp/preflight-gpu-full.xml`, `uv run --frozen --extra dev wgp release verify`, `git diff 8f0b225..HEAD -- services/jobs/preflight.py`, `git diff --exit-code 8f0b225..HEAD -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py scripts/run_film.py`, and `git diff --check`.
- Parse and record the JUnit `tests`, `errors`, `failures`, and `skipped` counters rather than quoting only pytest dots.
- Do not require a live occupied GPU or create a process on the host. If separate authorized read-only 3090 verification is available, it may be appended as supplementary evidence, but the deterministic captured-output tests are mandatory.

## Discovered During
Story WD-m0r5: first authorized image host batch. The observed PID was later terminated with operator authorization; this story records the latent preflight correctness defect and does not claim the host is currently occupied.

## MANDATORY SKILLS
- pvg — story governance, append-only delivery evidence, protected-head review, and release verification.

## Delivery Requirements
- Developer must paste exact command output tails, parsed JUnit counters, release fields, protected-file differentials, exact delivered commit SHA, and an AC verification table.
- Developer must use `pvg story deliver <story-id>`; independent PM acceptance is required at the exact delivered head after rerunning the material tests and gates.

## nd_contract
status: new

### evidence
- Created: 2026-09-24 from WD-m0r5 first-authorized-host-batch discovery at main `8f0b225`.
- Captured host row: `1007225, 7808 MiB, /home/straughter/llama.cpp/build/bin/llama-server`; preflight incorrectly reported `gpu_state=idle`.

### proof
- [ ] Pending implementation and independent exact-head acceptance.

## Context (Embedded)
- Defect discovered during the first authorized host batch, story WD-m0r5, on the RTX 3090 render host.
- At main `8f0b225`, `services/jobs/preflight.py:54` uses `_GPU_PROC_RE = re.compile(r"^\s*(\d+)\s+\S+", re.M)`, which recognizes whitespace-separated output but not comma-separated `nvidia-smi` CSV.
- The probe at `services/jobs/preflight.py:109-122` asks `nvidia-smi` for CSV but returns `gpu_state` as passing with detail `idle` when that regex does not match.
- Captured real host output was exactly: `1007225, 7808 MiB, /home/straughter/llama.cpp/build/bin/llama-server`. The 24576 MiB RTX 3090 had 7808 MiB held by PID 1007225, yet governed preflight printed `gpu_state=idle`.
- Consequence: a governed render can be admitted onto an occupied GPU. This is a fail-open admission correctness defect, not a feature request or capacity optimization.
- The GPU holder was terminated afterward with explicit operator authorization. The defect is latent and no longer blocks the current batch, but it must be fixed before future authorized host work relies on preflight.
- Parent choice: WD-3nod is the only open epic and owns the host-gated Maestro parity generation-evidence programme; WD-m0r5, where the defect was observed, is its child. No open preflight-specific epic exists, so this safety bug belongs where the authorized host-run programme will actually be dispatched.

## USER INTENT
The operator needs host preflight to refuse admission whenever another compute process holds the render GPU, with evidence identifying that process, so authorized parity renders cannot silently share an occupied GPU.

## Root Cause
GPU-state detection regexes only the legacy whitespace row shape and treats every nonmatching successful `nvidia-smi` response as idle. Successful but unparseable output therefore becomes a silently passing admission check instead of a failed check.

## Affected Components
- `services/jobs/preflight.py`
- `tests/test_jobs_preflight.py`
- Existing governed queue admission behavior that consumes `PreflightReport`

## PROTECTED ENGINE FILE — REQUIRED, NARROW CHANGE
- `services/jobs/preflight.py` is a PROTECTED ENGINE FILE. Protection is a review boundary, not an absolute ban.
- A protected-file change is required here because `_probe_gpu` currently produces a false `idle` admission verdict from real CSV output. Parser and check semantics cannot be corrected elsewhere without bypassing the admission boundary.
- The change must remain limited to GPU CSV parsing, structured occupancy state, and `gpu_state` verdict mapping. Do not refactor queue, render policy, wiring, or runtime admission.
- Delivery must state the exact accepted head and include the explicit differential `git diff 8f0b225..HEAD -- services/jobs/preflight.py`. The independent PM-Acceptor must verify the delivered tests and gates at that exact head before acceptance; if the head is rebased or changed, evidence and independent acceptance must be rerun.
- All other protected engine files — `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, and `scripts/run_film.py` — must remain unchanged from `8f0b225`.

## OUT OF SCOPE
- Killing, restarting, leasing, or otherwise managing GPU processes: preflight only detects and reports; any intervention requires separate explicit operator authorization.
- Capacity-based partial admission or memory thresholds: this story treats any parsed compute process holding memory as occupied; a capacity policy requires separate triage.
- A general `nvidia-smi` query framework or vendor-version matrix: only the compute-apps fields needed for fail-closed occupancy are in scope.
- GPU rendering, model downloads, host mutation, or live creation of an occupant: tests use the authorized captured real output and deterministic malformed inputs; they must not disturb the host.
- Queue-state machine, renderer selection, spend gates, or parity evidence semantics: those remain governed by their existing stories.

## DIFF BUDGET
- About 2 files and under 180 authored changed LOC: the focused preflight parser/state/check change plus direct parser and check-mapping regressions.
- Documentation changes are not expected; add one only if the implemented `gpu_state` detail contract materially changes.

## Boundary Map
PRODUCES:
- services/jobs/preflight.py -> `GpuComputeProcess` dataclass
  spec: frozen dataclass with `pid: int`, `memory_mib: int`, and `process_name: str`.
- services/jobs/preflight.py -> `GpuComputeState` dataclass
  spec: frozen dataclass with `verdict: Literal["idle", "occupied", "unknown"]`, `processes: tuple[GpuComputeProcess, ...]`, and `reason: str = ""`.
- services/jobs/preflight.py -> `_parse_gpu_compute_apps(output: str) -> GpuComputeState`
  event: parse exact captured CSV rows into structured process entries; recognize the genuine no-process response as idle; return `unknown` with a precise reason for empty-but-unexpected, malformed, missing-field, non-integer-memory, or alternate-column output.
- services/jobs/preflight.py -> `_gpu_check_from_state(state: GpuComputeState) -> PreflightCheck`
  event: return passing `gpu_state` only for `idle`; return a failing check with every observed PID, MiB value, and process name for `occupied`, and a failing fail-closed check for `unknown`.
- services/jobs/preflight.py -> `_probe_gpu(host) -> PreflightCheck`
  spec: existing host-seam signature, updated to request `pid,used_memory,process_name`, parse successful output through `_parse_gpu_compute_apps`, preserve failure on nonzero `nvidia-smi` return code, and never default successful unparseable output to idle.
- tests/test_jobs_preflight.py -> direct no-mock regressions for captured CSV, malformed/alternate columns, genuine idle, and check mapping.

CONSUMES:
- (existing): services/jobs/preflight.py -> `_safe_probe(host, argv, timeout=PROBE_TIMEOUT_SECS) -> tuple[int, str, str]`
  source: existing host-seam error wrapper; retain its nonzero/exception fail-closed behavior.
- (existing): services/jobs/preflight.py -> `run_preflight(host, *, models: Sequence[dict], min_free_gb: float, disk_path: str, qc_url: str) -> PreflightReport`
  source: existing admission entry point; its failed-check aggregation must continue to make a failed `gpu_state` refuse admission.
- (existing): host/render_host.py -> `SshHost.run_probe(argv, timeout) -> (rc, stdout, stderr)`
  source: production host seam; no duplicate host command path or SSH logic may be introduced.

## Story Acceptance Criteria
1. [State] The GPU probe requests `nvidia-smi --query-compute-apps=pid,used_memory,process_name --format=csv,noheader`, and the exact captured row `1007225, 7808 MiB, /home/straughter/llama.cpp/build/bin/llama-server` parses into a structured entry with `pid=1007225`, `memory_mib=7808`, and the exact process path.
2. [Unwanted] Whenever at least one parsed compute process holds memory, `gpu_state` does not report idle: the check fails and its detail names every observed PID, memory in MiB, and process name.
3. [Unwanted] An unparseable, empty-but-unexpected, alternate-column, missing-memory, or otherwise successful-but-unrecognized `nvidia-smi` shape returns `unknown` and fails admission; it never falls back to idle. A nonzero probe return code also continues to fail.
4. [State] A genuine no-compute-process response — specifically empty output or `No running processes found` — remains passing `gpu_state` with idle detail, and existing no-process preflight behavior is otherwise unchanged.
5. [State] Tests invoke `_parse_gpu_compute_apps` directly with the byte-for-byte captured real RTX 3090 output and with a malformed/alternate-column negative input, without host mocks; separate state-to-check assertions prove occupied and unknown both fail while genuine idle passes.
6. [State] Standing gates pass at the exact delivered head: targeted preflight tests; full suite with parsed JUnit `errors=0` and `failures=0`; `uv run --frozen --extra dev wgp release verify` reporting `release=ready` and `tag_created=false`; explicit preflight protected-file differential against `8f0b225`; unchanged differential for the other four protected files; and `git diff --check`.

## Testing Requirements
- Direct parser integration, MANDATORY with no mocks for the parser: use the exact authorized captured output above and assert the complete structured entry.
- Negative parser test: malformed and alternate-column output (for example memory before PID, or PID plus process path without memory) yields `unknown`, not idle, with a useful reason.
- Genuine-idle regression: assert both empty output and `No running processes found` yield idle/pass.
- Check-mapping tests: assert occupied detail contains PID 1007225, `7808` MiB, and `/home/straughter/llama.cpp/build/bin/llama-server`; unknown fails closed; idle alone passes. Nonzero `nvidia-smi` return remains a failed check.
- Commands: run targeted `uv run --frozen --extra dev pytest -q tests/test_jobs_preflight.py`, full `uv run --frozen --extra dev pytest -q --junitxml=/tmp/preflight-gpu-full.xml`, `uv run --frozen --extra dev wgp release verify`, `git diff 8f0b225..HEAD -- services/jobs/preflight.py`, `git diff --exit-code 8f0b225..HEAD -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py scripts/run_film.py`, and `git diff --check`.
- Parse and record the JUnit `tests`, `errors`, `failures`, and `skipped` counters rather than quoting only pytest dots.
- Do not require a live occupied GPU or create a process on the host. If separate authorized read-only 3090 verification is available, it may be附加 as supplementary evidence, but the deterministic captured-output tests are mandatory.

## Discovered During
Story WD-m0r5: first authorized image host batch. The observed PID was later terminated with operator authorization; this story records the latent preflight correctness defect and does not claim the host is currently occupied.

## MANDATORY SKILLS
- pvg — story governance, append-only delivery evidence, protected-head review, and release verification.

## Delivery Requirements
- Developer must paste exact command output tails, parsed JUnit counters, release fields, protected-file differentials, exact delivered commit SHA, and an AC verification table.
- Developer must use `pvg story deliver <story-id>`; independent PM acceptance is required at the exact delivered head after rerunning the material tests and gates.

## nd_contract
status: new

### evidence
- Created: 2026-09-24 from WD-m0r5 first-authorized-host-batch discovery at main `8f0b225`.
- Captured host row: `1007225, 7808 MiB, /home/straughter/llama.cpp/build/bin/llama-server`; preflight incorrectly reported `gpu_state=idle`.

### proof
- [ ] Pending implementation and independent exact-head acceptance.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-24T21:11:26Z dep_added: blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]

## Comments
