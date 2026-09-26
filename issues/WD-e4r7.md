---
id: WD-e4r7
title: "Bug: make GPU preflight fail closed for occupied compute processes"
status: closed
priority: 0
type: bug
labels: [bug, host-safety, integration, accepted]
parent: WD-3nod
created_at: 2026-09-24T21:11:25Z
created_by: speed
updated_at: 2026-09-25T03:15:53Z
content_hash: "sha256:5200a22eee66bb1d286fd905d1146e2fcd13251942bfce93b5fe2d8e8430f41e"
assignee: dev-WD-e4r7
follows: [WD-651z]
closed_at: 2026-09-25T02:42:09Z
close_reason: "Accepted via pvg story accept"
led_to: [WD-rous, WD-0zj8, WD-bxhc, WD-dmf2, WD-fay0]
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


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-24.

### proof
- [x] Story closed after accepted label was applied.


## Implementation Evidence

Summary: Delivered fail-closed GPU occupancy parsing and admission verdicts at exact pushed head below; direct tests use the real captured CSV row and no host/GPU/network.

Commands run:
- `timeout 3600 uv run --frozen --extra dev pytest -q tests/test_jobs_preflight.py` -> exit 0; 21 passed.
- `timeout 3600 uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-e4r7-full.xml` -> exit 0.
- `timeout 3600 uv run --frozen --extra dev wgp release verify` -> exit 0; `release=ready`, `tag_created=false`.
- `git diff 8f0b225 -- services/jobs/preflight.py` -> full protected differential recorded above.
- `git diff --exit-code 8f0b225 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py scripts/run_film.py` -> exit 0; no diff.
- `git diff --check` -> exit 0; no output.
- `git push -u origin story/WD-e4r7` -> exit 0.

### CI/Test Results
- Targeted: 21/21 passed, 0 failed.
- Full JUnit: tests=2084, errors=0, failures=0, skipped=1.
- Before/after real row: idle/pass -> occupied/fail with pid 1007225, 7808 MiB, and exact llama-server path.
- Malformed alternate columns -> unknown/fail; empty -> idle/pass.

### AC Verification
| AC | Result | Evidence |
| --- | --- | --- |
| 1 | PASS | Exact captured row parses to pid=1007225, memory_mib=7808, exact path; query includes all 3 fields. |
| 2 | PASS | Any occupied state fails and detail names every pid, MiB, process. |
| 3 | PASS | Malformed/alternate/truncated output -> unknown/fail; nonzero rc remains fail. |
| 4 | PASS | Empty and `No running processes found` remain idle/pass. |
| 5 | PASS | Direct no-mock parser tests cover real row, comma/space path, malformed, idle, and check mapping. |
| 6 | PASS | Target, full JUnit, release, differential, protected-no-change, and whitespace gates pass at SHA below. |

SHA: ada69471cbe7cbb1fe4f765432d0bf2063ae9ee4


## nd_contract
status: delivered

### evidence
- Branch/head: `story/WD-e4r7@ada69471cbe7cbb1fe4f765432d0bf2063ae9ee4`; pushed to `origin/story/WD-e4r7` (push exit 0).
- Files: `services/jobs/preflight.py`, `tests/test_jobs_preflight.py`; diff from base: 162 insertions / 17 deletions across 2 files.
- Targeted command (timeout 3600s): `uv run --frozen --extra dev pytest -q tests/test_jobs_preflight.py` -> exit 0, tail `.....................  [100%]`.
- Full command (timeout 3600s): `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-e4r7-full.xml` -> exit 0; parsed JUnit `tests=2084 errors=0 failures=0 skipped=1`.
- Release: `uv run --frozen --extra dev wgp release verify` -> exit 0, `release=ready`, `tag_created=false`.
- Protected gates: `git diff --exit-code 8f0b225 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py scripts/run_film.py` -> exit 0/no diff; `git diff --check` -> exit 0/no output.
- Before/after for exact captured row `1007225, 7808 MiB, /home/straughter/llama.cpp/build/bin/llama-server`: before `PreflightCheck(kind='gpu_state', passed=True, detail='idle')`; after `PreflightCheck(kind='gpu_state', passed=False, detail='GPU occupied: pid=1007225 memory=7808MiB process=/home/straughter/llama.cpp/build/bin/llama-server')`.
- Malformed alternate-column row `7808 MiB, 1007225, /tmp/renderer`: after state `unknown`, check fails with `GPU state unknown (fail closed): invalid pid '7808 MiB'`. Empty output: state `idle`, check passes `idle`. No host, SSH, GPU, or network probe was used for this story.

### proof
- [x] AC1: probe now requests `pid,used_memory,process_name`; direct parser test asserts exact captured pid/memory/path.
- [x] AC2: occupied check fails and names pid, MiB, and process for every parsed process.
- [x] AC3: malformed/alternate/truncated shapes and nonzero rc fail closed as unknown/error; successful surprises never idle.
- [x] AC4: empty and `No running processes found` remain passing idle.
- [x] AC5: direct no-mock parser tests cover real CSV, quoted comma/space path, malformed shapes, idle, and state-to-check mapping.
- [x] AC6: targeted/full/release/protected-differential/unchanged-protected/whitespace gates passed at `ada69471cbe7cbb1fe4f765432d0bf2063ae9ee4`.

### protected-file-differential
```diff
diff --git a/services/jobs/preflight.py b/services/jobs/preflight.py
index df26c2a..95b894f 100644
--- a/services/jobs/preflight.py
+++ b/services/jobs/preflight.py
@@ -13,9 +13,11 @@ duplicate).
 """
 from __future__ import annotations
 
+import csv
+import io
 import re
 from dataclasses import dataclass, field
-from typing import List, Optional, Sequence
+from typing import List, Literal, Optional, Sequence
 
 PROBE_TIMEOUT_SECS = 30
 
@@ -49,9 +51,67 @@ class PreflightReport:
         return [c for c in self.checks if not c.passed]
 
 
-# nvidia-smi --query-compute-apps output: pid, process name — a row
-# with a digit-led pid means SOMETHING holds the GPU (stale tenant).
-_GPU_PROC_RE = re.compile(r"^\s*(\d+)\s+\S+", re.M)
+@dataclass(frozen=True)
+class GpuComputeProcess:
+    pid: int
+    memory_mib: int
+    process_name: str
+
+
+@dataclass(frozen=True)
+class GpuComputeState:
+    verdict: Literal["idle", "occupied", "unknown"]
+    processes: tuple[GpuComputeProcess, ...]
+    reason: str = ""
+
+
+def _parse_gpu_compute_apps(output: str) -> GpuComputeState:
+    """Parse nvidia-smi CSV compute-app rows, failing closed on surprises."""
+    text = (output or "").strip()
+    if text == "" or text == "No running processes found":
+        return GpuComputeState("idle", ())
+
+    processes = []
+    for row in csv.reader(io.StringIO(text), skipinitialspace=True):
+        if len(row) != 3:
+            return GpuComputeState(
+                "unknown", tuple(processes),
+                f"expected 3 CSV fields, got {len(row)}: {row!r}")
+        pid_text, memory_text, process_name = (value.strip() for value in row)
+        try:
+            pid = int(pid_text)
+        except ValueError:
+            return GpuComputeState(
+                "unknown", tuple(processes), f"invalid pid {pid_text!r}")
+        memory_match = re.fullmatch(r"(\d+)\s*(?:MiB)?", memory_text)
+        if memory_match is None or not process_name:
+            return GpuComputeState(
+                "unknown", tuple(processes),
+                f"invalid compute-app row: pid={pid}, "
+                f"used_memory={memory_text!r}, "
+                f"process_name={process_name!r}")
+        processes.append(GpuComputeProcess(
+            pid, int(memory_match.group(1)), process_name))
+    return GpuComputeState("occupied", tuple(processes))
+
+
+def _gpu_check_from_state(state: GpuComputeState) -> PreflightCheck:
+    if state.verdict == "idle":
+        return PreflightCheck("gpu_state", True, "idle")
+    if state.verdict == "occupied":
+        occupants = _gpu_occupant_detail(state.processes)
+        return PreflightCheck("gpu_state", False, f"GPU occupied: {occupants}")
+    detail = f"GPU state unknown (fail closed): {state.reason}"
+    if state.processes:
+        detail += f"; observed {_gpu_occupant_detail(state.processes)}"
+    return PreflightCheck(
+        "gpu_state", False, detail)
+
+
+def _gpu_occupant_detail(processes):
+    return ", ".join(
+        f"pid={proc.pid} memory={proc.memory_mib}MiB "
+        f"process={proc.process_name}" for proc in processes)
 
 
 def _safe_probe(host, argv, timeout=PROBE_TIMEOUT_SECS):
@@ -108,18 +168,15 @@ def _probe_disk(host, disk_path, min_free_gb) -> PreflightCheck:
 
 def _probe_gpu(host) -> PreflightCheck:
     rc, out, _err = _safe_probe(
-        host, ["nvidia-smi", "--query-compute-apps=pid,process_name",
-               "--format=csv,noheader"])
+        host, [
+            "nvidia-smi",
+            "--query-compute-apps=pid,used_memory,process_name",
+            "--format=csv,noheader",
+        ])
     if rc != 0:
         return PreflightCheck("gpu_state", False,
                               f"nvidia-smi rc={rc}")
-    m = _GPU_PROC_RE.search(out or "")
-    if m:
-        return PreflightCheck(
-            "gpu_state", False,
-            f"GPU busy: stale tenant pid {m.group(1)} "
-            f"({out.strip().splitlines()[0]})")
-    return PreflightCheck("gpu_state", True, "idle")
+    return _gpu_check_from_state(_parse_gpu_compute_apps(out))
 
 
 def _probe_qc(host, qc_url) -> PreflightCheck:
@@ -151,5 +208,6 @@ def run_preflight(host, *, models: Sequence[dict], min_free_gb: float,
 
 __all__ = [
     "PreflightCheck", "PreflightReport", "PreflightError",
+    "GpuComputeProcess", "GpuComputeState",
     "run_preflight", "PROBE_TIMEOUT_SECS",
 ]
```


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-24.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-24T21:11:26Z dep_added: blocks WD-fay0
- 2026-09-25T01:36:22Z status: open -> in_progress
- 2026-09-25T01:36:22Z auto-follows: linked to predecessor WD-651z
- 2026-09-25T01:36:22Z claimed by dev-WD-e4r7
- 2026-09-25T02:24:07Z status: in_progress -> in_progress
- 2026-09-25T02:42:09Z status: in_progress -> closed
- 2026-09-25T02:42:09Z dep_removed: no_longer_blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Follows: [[WD-651z]]
- Led to: [[WD-rous]], [[WD-0zj8]], [[WD-bxhc]], [[WD-dmf2]], [[WD-fay0]]

## Comments

### 2026-09-25T03:15:53Z speed
MERGED to main as d8671f3 (squash of PR #185). Accepted at ada69471cbe7cbb1fe4f765432d0bf2063ae9ee4, rebased to 72170ba0021e2656d925921bf0e95646f632ed52 with the story files byte-identical to the accepted head. Required check 'test' completed/success. Protected-file change independently accepted: narrow parsing/verdict plumbing only.
