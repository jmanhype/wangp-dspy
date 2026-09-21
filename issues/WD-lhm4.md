---
id: WD-lhm4
title: "Deliver stable wgp verbs with doctor preflight"
status: in_progress
priority: 1
type: feature
labels: [integration, delivered]
parent: WD-t534
created_at: 2026-09-21T13:56:15Z
created_by: speed
updated_at: 2026-09-21T17:30:15Z
content_hash: "sha256:403cfb385cf51f75d285fe40bd23d242e20f52fb453bb74b43fa7c9fcfadba5d"
blocks: [WD-fp49, WD-fq1o]
was_blocked_by: [WD-3nwm]
follows: [WD-3nwm]
assignee: dev-WD-lhm4
---

## Description
## USER INTENT
An operator wants stable `wgp` verbs and a doctor preflight instead of memorizing internal script paths. The CLI must make the accepted gateway and durable queue usable without duplicating or altering their semantics.

## Context (Embedded)
- `pyproject.toml` currently declares no console script.
- The no-GPU gateway is `scripts/run_content_brief.py::main(argv: list[str] | None = None) -> int`; it validates a brief, performs deterministic dry planning, and writes `wangp-dspy.content-plan/v1`.
- The durable queue exposes `services.jobs.queue.JobQueue.get(job_id: str) -> JobRecord`, `list_state(state: str) -> List[str]`, and `attempt_history(job_id: str) -> List[Dict]`. `JobRecord` carries `job_id`, `state`, `plan_ref`, `clips`, `failure_count`, `failure_class`, `failure_detail`, `retryable`, and `created_at`.
- Existing no-host planning/reporting helpers are `scripts.run_jobs.dry_run_report(queue) -> dict` and `dry_run_plan(queue, limit=None) -> list`; both are read-only when used with `--dry-run`.
- Existing infrastructure preflight is `services.jobs.preflight.run_preflight(host, *, models: Sequence[dict], min_free_gb: float, disk_path: str, qc_url: str) -> PreflightReport`. Its checks are exactly `ssh_reachable`, `model_files`, `disk_headroom`, `gpu_state`, and `qc_available`; each failed `PreflightCheck` carries kind and detail.
- Doctor must be safe by default: no SSH/network/GPU/model call unless an explicit host probe is requested. Local doctor still reports Python, dependency imports, ffmpeg, ffprobe, host configuration status, supplied model manifest status, and local disk headroom.
- Stable command surface: `wgp doctor`, `wgp brief validate`, `wgp plan`, `wgp status`, and `wgp review`.

## OUT OF SCOPE
- Reimplementing content validation, planning, queue selection, rendering, retries, or QC: the CLI delegates to existing seams.
- Host configuration-file resolution/auto-detection: the following zero-config story extends doctor and render wiring.
- Detailed typed remediation mapping beyond doctor/check-level messages: the failure-UX story owns cross-class diagnostics.
- Any installer or GUI.
- A live remote-host test, GPU work, model inference, or paid hosted service.

## DIFF BUDGET
- Roughly 8 authored files, under 650 authored changed LOC.

## Boundary Map
PRODUCES:
- pyproject.toml -> console-script contract `wgp = "wangp.cli:main"` and packaged `wangp` module.
- wangp/__init__.py -> `__version__: str`
- wangp/cli.py -> `main(argv: Sequence[str] | None = None) -> int`
- wangp/doctor.py -> `collect_doctor_checks(models: Sequence[Mapping[str, str]] | None = None, *, probe_host: bool = False) -> DoctorReport`
- wangp/queue_view.py -> `collect_status(db_path: str | Path, *, job_id: str | None = None) -> QueueStatus`
- docs/wgp-cli.md -> stable verb reference, exit-code contract, JSON output contract, and no-host safety rule.
- README.md -> short entry-point section linking the full CLI reference.
- tests/test_wgp_cli.py -> `test_wgp_plan_wraps_gateway_with_no_gpu_work() -> None`

CONSUMES:
- WD-3nwm: README.md -> quickstart contract
  spec: the CLI entry-point section must extend, not replace, the tested clone-to-plan path.
- (existing): scripts/run_content_brief.py -> `main(argv: list[str] | None = None) -> int`
  spec: `wgp brief validate` uses the same loader validation without writing; `wgp plan` forwards arguments to this main and preserves its exit status and output file contract.
- (existing): scripts/run_jobs.py -> `dry_run_report(queue) -> dict`
  spec: read-only pending/admissibility presentation; `wgp status` never advances queue state.
- (existing): services/jobs/queue.py -> `JobQueue.get(self, job_id: str) -> JobRecord`
  spec: direct read of durable state and failure summary.
- (existing): services/jobs/queue.py -> `JobQueue.list_state(self, state: str) -> List[str]`
  spec: ordered job ids by state for counts and summaries.
- (existing): services/jobs/queue.py -> `JobQueue.attempt_history(self, job_id: str) -> List[Dict]`
  spec: immutable attempt and failure evidence for `wgp review`.
- (existing): services/jobs/preflight.py -> `run_preflight(host, *, models: Sequence[dict], min_free_gb: float, disk_path: str, qc_url: str) -> PreflightReport`
  spec: used only under explicit `wgp doctor --probe-host`; no implicit network call.

## Required Outcomes
1. Installing the project exposes `wgp`, and `wgp --help` lists exactly the stable verbs above with local, no-GPU defaults.
2. `wgp brief validate BRIEF` performs the existing typed validation without creating a run directory or plan, succeeds with the brief hash, and returns nonzero with a field-specific human message for invalid input.
3. `wgp plan` wraps the existing gateway command, emits the same canonical plan fields and exit code, and performs no SSH, queue submission, model inference, or GPU work.
4. `wgp status --db DB` opens the real SQLite queue read-only, displays state counts and concise per-job state/failure summaries, and leaves job rows, attempt rows, timestamps, and file bytes unchanged.
5. `wgp review --db DB [--job ID]` displays job clips, durable failure summary, immutable attempt history, and referenced evidence paths without changing retry eligibility or state.
6. `wgp doctor` reports Python version, required dependency imports, ffmpeg, ffprobe, host-configuration status, supplied model-manifest coverage, and local disk headroom; every failed/skipped check includes one concrete remediation and no stack trace.
7. Explicit `wgp doctor --probe-host --models MANIFEST` wraps the existing preflight and reports all five existing check kinds; without that flag doctor performs no SSH or hosted-service call.
8. Stable exit codes are documented and tested: 0 success, 2 usage/input/configuration error, 3 failed doctor check, and 4 unexpected internal error; machine-readable `--json` output is deterministic and excludes environment secrets.
9. No gateway, runner, queue-transition, retry, renderer, or QC behavior changes; tests demonstrate the wrapper delegates rather than copying implementation logic.

## Testing Requirements
- Unit: parser routing, exit-code mapping, human/JSON rendering, doctor pass/fail/skip presentation, and no-write validation behavior.
- Integration: MANDATORY (no mocks). Invoke the actual CLI in subprocesses: validate the committed brief, plan it into temporary storage, and inspect a copy of the committed LF004 queue database for status/review without byte mutation.
- Doctor integration: MANDATORY (no mocks). Run local doctor against the actual interpreter/dependency/tool environment and a real temporary JSON model manifest containing at least one missing local file; no SSH flag is passed and no network call is made.
- Commands: `uv run --frozen --extra dev pytest tests/test_wgp_cli.py`, `uv run --frozen --extra dev pytest -q`, and the documented `wgp --help` command.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must paste CLI transcripts and targeted/full test output into notes.
- Developer must include an AC verification table mapping each verb and exit code to a real test.
- Developer must use `pvg story deliver`.
- No GPU, SSH, remote host work, model inference, paid hosted service, commit, or push is authorized.

## nd_contract
status: new

### evidence
- Created 2026-09-21 from the measured absence of a console script and the verified gateway, queue, and preflight APIs at main 3094b14.

### proof
- [ ] Pending implementation


## Acceptance Criteria


## Design


## Notes
Delivery correction: the prior in_progress contract is stale; WD-lhm4 is delivered at 0e50b5a with PR #152 and green CI 35624803571.
### DISCOVERED_BUG
  title: pvg story deliver is not idempotent after label add
  context: A race/ordering in  added the delivered label and appended transition evidence, then returned exit 1 with . The story ends in the correct  +  state, but retrying the documented transition fails.
  affected_files: pvg story-delivery transition implementation
  discovered_during: WD-lhm4
DISCOVERED_BUG clarification: the failed transition command was pvg story deliver WD-lhm4. Its exact stderr was: labels add WD-lhm4 delivered: Error: label delivered already exists on WD-lhm4. The intended story state is in_progress with delivered label, and that final state is present.
Commit: faeac0c9092952f78e5c5944f0dabf4e805b4db2
SHA: faeac0c9092952f78e5c5944f0dabf4e805b4db2

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-21.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: delivered

### evidence
- Producing commit: faeac0c9092952f78e5c5944f0dabf4e805b4db2

### proof
- [x] Commit SHA recorded.

## Implementation Evidence

Commands run:
- `uv run --frozen --extra dev pytest -q tests/test_wgp_cli.py` — PASS, 17/17.
- `uv run --frozen --extra dev pytest -q` — PASS, 1,578 passed / 1 pre-existing environment-gated skip / 0 failed; one owned Starlette deprecation warning shown below.
- `uv run --frozen --extra dev wgp --help` — PASS; exact stable verbs: `doctor`, `brief`, `plan`, `status`, `review`.
- `git diff --check` — PASS.
- `git diff --exit-code main -- services/director/renderers/policy.py services/director/wiring.py qc/ host/ scripts/run_film.py scripts/run_jobs.py` — PASS (exit 0). `services/jobs/preflight.py` is also unchanged.
- `pvg verify .github/workflows/ci.yml docs/wgp-cli.md pyproject.toml tests/test_wgp_cli.py wangp/cli.py wangp/doctor.py wangp/queue_view.py --include-tests --format=text` — `VERIFY: PASSED (4 files scanned, 0 issues)`.
- `uv build` — PASS, produced both `dist/wangp_dspy-0.1.0.tar.gz` and `dist/wangp_dspy-0.1.0-py3-none-any.whl`.
- Wheel/install smoke outside the source checkout: `uv venv /tmp/wd-lhm4-wheel-smoke.J2dcjM/venv`; `uv pip install --python .../venv/bin/python dist/wangp_dspy-0.1.0-py3-none-any.whl`; then from `/tmp/wd-lhm4-wheel-smoke.J2dcjM`, with `WANGP_SSH_TARGET` and `PYTHONPATH` unset, `.../venv/bin/wgp doctor` — exit 0 / `ready=yes`. Imported module origins were both under the throwaway venv site-packages, not the repository. Wheel SHA-256: `ac8dcb9903b824a4be9fcb6850fbb31ee4ba4b81798fb53efc1839f04b91cc0c`; sdist SHA-256: `d7ccbe167290ff74f27d261ad1c216ff1396ba3bc7df601d7e13072295d1e497`.
- Subprocess-enabled Coverage.py run of the targeted CLI suite — TOTAL **83%** (`cli.py` 84%, `doctor.py` 70%, `queue_view.py` 92%, `__init__.py` 100%).
- Required CI at the exact pushed head: run **35631378806**, workflow `CI`, head SHA below, status `completed`, conclusion `success`, URL https://github.com/jmanhype/wangp-dspy/actions/runs/35631378806.

Summary: Fixed all seven PR-review defects while preserving the delegated engine seams; built and installed a real wheel outside the repository; made queue review filesystem-immutable; and verified the full suite, packaging, CLI, and CI at the pushed head.

Commit SHA: `faeac0c9092952f78e5c5944f0dabf4e805b4db2` (branch `story/WD-lhm4`, PR #152).

### Review-finding evidence
| Finding | Fix and evidence | Status |
|---|---|---|
| 1. Installed entry point imports unpackaged `scripts` at startup | `wangp/cli.py:136` now imports the gateway only inside `_run_plan`; `pyproject.toml:41` ships the required top-level packages without duplicate nested entries. `tests/test_wgp_cli.py:441` builds wheel+sdist, installs into a fresh venv outside the repo, runs `wgp doctor`, and proves module origins are venv site-packages. Manual smoke above also exited 0 with `ready=yes`. | PASS |
| 2. `status`/`review` mutate queue filesystems | `wangp/queue_view.py:62` opens through a read-only `JobQueue` adapter using `mode=ro&immutable=1` (`wangp/queue_view.py:69`) plus `PRAGMA query_only=ON`; no WAL/SHM sidecars are created. `tests/test_wgp_cli.py:147` and `:171` copy the committed LF004 DB into fresh temporary directories and assert directory listing and SHA-256 are unchanged. Manual reproduction observed `before=q.db`, `after=q.db`, and identical SHA-256 `fcefccf496ab8f1c2275271cb901528bda820708ac5f2ada09c0d349c1349ca4` for both verbs. | PASS |
| 3. Missing provenance exits 0 | `wangp/queue_view.py:217` rejects a missing bundle/provenance file and `:253` rejects zero recognized pairs as typed input errors. `tests/test_wgp_cli.py:193` covers both absent and `{}` provenance and expects exit 2 with explicit messages. | PASS |
| 4. Corrupt local model passes | `wangp/doctor.py:116` streams 1 MiB chunks through SHA-256; `wangp/doctor.py:128` reports every missing/unreadable/mismatched local model. `tests/test_wgp_cli.py:299` uses a real corrupt file and wrong digest, expecting exit 3 and remediation. | PASS |
| 5. Host probe with no manifest succeeds | `wangp/doctor.py:242` requires at least one valid `remote_path`; `wangp/doctor.py:291` appends a failed `model_files` check without contacting a host. `tests/test_wgp_cli.py:330` expects exit 3, actionable detail/remediation, and no `ssh_reachable` check. | PASS |
| 6. Full render host passes disk check | `wangp/doctor.py:18` sets the documented remote minimum to 50 GB and `wangp/doctor.py:226` passes it to the unchanged preflight seam. `tests/test_wgp_cli.py:356` runs the real five-check subprocess path against a 49G report and expects `disk_headroom` failure with `(min 50.0G)`. | PASS |
| 7. Valid remote models fail path validation | Manifest loading now separates `local_path` and `remote_path` (`wangp/cli.py:42`). `wangp/doctor.py:200` resolves relative paths under the Wan2GP root and preserves absolute remote paths. `tests/test_wgp_cli.py:356` proves a missing local path does not invalidate valid relative and absolute remote files, checks real hashes, and reports all five kinds; `tests/test_wgp_cli.py:396` proves a genuinely missing remote model fails. | PASS |

### Packaging and CI
- `uv build` now emits both distributables; the nested Hatch package declarations that duplicated `qc/audio_critic` were removed at `pyproject.toml:41`. This packaging correction also satisfies **WD-m1sj** by reference; WD-m1sj tracker state was intentionally not touched.
- CI now runs `uv build` and asserts exactly one `.whl` plus one `.tar.gz` at `.github/workflows/ci.yml:34`. The required run completed successfully at the pushed head.

### AC Verification
| AC # | Requirement | Evidence | Status |
|---|---|---|---|
| 1 | Installed `wgp`; exact stable help verbs | `pyproject.toml:19`, `pyproject.toml:41`, `tests/test_wgp_cli.py:67`, wheel smoke | PASS |
| 2 | Typed validation without planning | `wangp/cli.py:125`, `tests/test_wgp_cli.py:75` | PASS |
| 3 | Delegated no-GPU/no-submit plan | lazy gateway import `wangp/cli.py:136`, `tests/test_wgp_cli.py:93` | PASS |
| 4 | Read-only real queue status | `wangp/queue_view.py:62`, `tests/test_wgp_cli.py:147` | PASS |
| 5 | Read-only clips/failures/attempts/evidence | `wangp/queue_view.py:128`, `tests/test_wgp_cli.py:171` | PASS |
| 6 | Local doctor coverage/remediation | `wangp/doctor.py:113`, `wangp/doctor.py:291`, `tests/test_wgp_cli.py:192`, `:299` | PASS |
| 7 | Explicit five-kind host preflight / default no-call | `wangp/doctor.py:200`, `:214`, `:242`; `tests/test_wgp_cli.py:330`, `:356`, `:396` | PASS |
| 8 | Stable exit codes and deterministic JSON | `wangp/cli.py:266`, docs, `tests/test_wgp_cli.py:420` | PASS |
| 9 | No engine/queue/QC semantic changes | protected-file diff exit 0; `services/jobs/preflight.py` unchanged; tests exercise wrappers | PASS |

### Diff-budget explanation
`git diff --numstat main...HEAD` measures **1,538 insertions / 1 deletion across 9 files**, not under 650: `wangp/` runtime 922 lines, no-mock subprocess tests 521 lines, operator docs 85 lines, and packaging/CI 10 lines. The runtime scope inherently spans five verbs, canonical JSON/error contracts, ten local doctor checks, five remote checks, separate local/remote model namespaces, streaming hashes, immutable SQLite review, and recursive provenance verification. The test scope is similarly inherent: real CLI subprocesses, committed queue fixture byte/listing identity, local subprocess preflight command fixtures, and build/install/out-of-repo wheel validation. I therefore retained the wider auditable integration coverage rather than weakening it to fit a line target.

### Owned warnings and remaining defect
- Full-suite warning (pre-existing): `StarletteDeprecationWarning: Using 'httpx' with 'starlette.testclient' is deprecated; install 'httpx2' instead` from `.venv/.../fastapi/testclient.py:1`. Test outcome remains 1,578 passed / 1 skipped / 0 failed.
- Successful CI still emits runner annotations: `actions/setup-python@v5` and `astral-sh/setup-uv@v6` target deprecated Node.js 20 (forced to Node 24), and `ubuntu-latest` will migrate to Ubuntu 26 on 2026-10-19.
- Remaining out-of-scope installed-wheel defect: from `/tmp/wd-lhm4-wheel-smoke.J2dcjM`, command `env -u WANGP_SSH_TARGET -u PYTHONPATH ./venv/bin/wgp plan --brief <repo>/datasets/content_briefs/lf004-operator-dogfood-56f/brief.json --plates <repo>/datasets/content_briefs/lf004-operator-dogfood/plates --out ./plan.json --run-dir ./run` exits **4** with `RepositoryIdentityError: git rev-parse --show-toplevel failed for .../site-packages: fatal: not a git repository`. Startup/import and doctor are fixed, but the existing planning gateway assumes a Git checkout; no unauthorized gateway semantic change was made in this story.

### DISCOVERED_BUG
  title: Installed wgp plan assumes a Git checkout for repository identity
  context: A wheel-installed `wgp plan` starts and imports correctly outside the source tree, but the delegated planning gateway resolves repository identity from installed site-packages and fails before planning. This is beyond WD-lhm4's seven review defects and would alter gateway semantics if fixed here.
  affected_files: `scripts/run_content_brief.py`, `scripts/run_film.py`, `services/director/run_ledger.py`
  discovered_during: WD-lhm4

LEARNINGS:
- `mode=ro` alone can still create SQLite WAL/SHM sidecars; `immutable=1` was required to prove both byte and directory immutability for the committed WAL-mode queue.
- The wheel failure was packaging plus import timing, not gateway behavior: lazy dispatch and shipping the delegated scripts package preserves semantics while making startup work.
- Local executable command fixtures exercise the real preflight subprocess seam and path/hash handling without SSH, GPU, model inference, or Python mocks.
- Separating `local_path` from Wan2GP-relative/absolute `remote_path` is necessary; one path cannot be valid in both filesystem namespaces.
- CI build verification caught the Hatch duplicate-package problem that source-tree editable installs hide.

## nd_contract
status: delivered

### evidence
- Commit `faeac0c9092952f78e5c5944f0dabf4e805b4db2`; pushed branch `story/WD-lhm4`; PR #152.
- Targeted CLI tests: 17 passed. Full suite: 1,578 passed, 1 skipped, 0 failed. Coverage: 83%.
- `uv build`: wheel and sdist both produced and hash-recorded. Throwaway-venv `wgp doctor`: exit 0, ready=yes.
- Required CI run 35631378806 at exact head: completed/success.
- Protected engine diff, `git diff --check`, and `pvg verify` all passed.

### proof
- [x] AC #1: installed stable `wgp` surface and exact help verbs are wheel-tested.
- [x] AC #2: typed brief validation and no-write behavior are subprocess-tested.
- [x] AC #3: plan delegates to the existing no-GPU gateway and remains no-submit.
- [x] AC #4: status is database-byte and filesystem-listing immutable on the committed queue.
- [x] AC #5: review is database-byte and filesystem-listing immutable and reports durable evidence.
- [x] AC #6: local doctor verifies supplied local model hashes and reports actionable failures/skips.
- [x] AC #7: host probing requires explicit remote models, checks all five kinds, uses 50 GB minimum, and stays no-call by default.
- [x] AC #8: exit codes and deterministic secret-free JSON are documented and tested.
- [x] AC #9: protected gateway/runner/queue/QC semantics are unchanged.

## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-09-21.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## nd_contract
status: delivered

### evidence
- The authoritative delivery evidence above was produced at pushed commit 0e50b5a592a8e392c1595c5f3de024f2d820589f; PR #152 and CI run 35624803571 are green.  was invoked; it completed the transition/evidence append but returned exit 1 because the delivered label had already been added.

### proof
- [x] All nine WD-lhm4 acceptance criteria verified in the authoritative table above.

## Implementation Evidence (DELIVERED)

PROOF:

### CI/Test Results
- Commands run:
  - `uv run --frozen --extra dev pytest tests/test_wgp_cli.py` — **11 passed in 8.78s**.
  - `uv run --frozen --extra dev pytest -q tests/test_wgp_cli.py` — **11 passed**.
  - `uv run --frozen --extra dev pytest -q tests/` — **exit 0**. Progress contained **1,572 passing dots and one `s`** (the pre-existing 3090 integration skip); collected total is 1,573.
  - `uv run --frozen --extra dev pytest -q` — exit 0 with the same suite shape before the final formatting-only compaction.
  - Subprocess-enabled coverage run for `tests/test_wgp_cli.py`: **TOTAL 86%** (`wangp/cli.py` 85%, `wangp/doctor.py` 87%, `wangp/queue_view.py` 86%, `wangp/__init__.py` 100%).
  - `git diff --check` — PASS.
  - `git diff --exit-code main -- services/director/renderers/policy.py services/director/wiring.py qc/ host/ scripts/run_film.py scripts/run_jobs.py` — PASS; no protected engine/runner files changed.
  - `pvg verify wangp/__init__.py wangp/cli.py wangp/doctor.py wangp/queue_view.py docs/wgp-cli.md README.md pyproject.toml tests/test_wgp_cli.py --include-tests --format=text` — **VERIFY: PASSED (5 files scanned, 0 issues)**.
- Required CI: `gh run list --branch story/WD-lhm4` read at pushed head:
  - run id **35624803571**
  - workflow **CI**
  - head SHA **0e50b5a592a8e392c1595c5f3de024f2d820589f**
  - status **completed**, conclusion **success**
  - URL: https://github.com/jmanhype/wangp-dspy/actions/runs/35624803571

### Commit / PR
- Branch: `story/WD-lhm4`
- Commit: `0e50b5a592a8e392c1595c5f3de024f2d820589f` (`0e50b5a`)
- PR: https://github.com/jmanhype/wangp-dspy/pull/152
- Worktree is clean at the pushed commit.

### CLI transcripts (exact output tails)
`env -u WANGP_SSH_TARGET uv run --frozen --extra dev wgp doctor | tail -20`:
```text
[PASS] python: Python 3.14.4
[PASS] uv: uv available at /Users/speed/.local/bin/uv
[PASS] dependency_imports: 8 imports available
[PASS] ffprobe: ffprobe available at /opt/homebrew/bin/ffprobe
[PASS] ffmpeg: ffmpeg available at /opt/homebrew/bin/ffmpeg
[PASS] queue_database: SQLite 3.50.4 is available for JobQueue databases
[SKIP] model_files: No model manifest supplied; not required for no-GPU planning
       remediation: Supply --models with path and sha256 entries before host work.
[SKIP] host_configuration: No render host configured; the no-GPU lane remains ready
       remediation: Set WANGP_SSH_TARGET or wait for the WD-fp49 config file for GPU work.
[PASS] local_disk_headroom: 134G free on the repository volume
ready=yes
```

`uv run --frozen --extra dev wgp plan --brief datasets/content_briefs/lf004-operator-dogfood-56f/brief.json --plates datasets/content_briefs/lf004-operator-dogfood/plates --out /tmp/wd-lhm4-cli/plan.json --run-dir /tmp/wd-lhm4-cli/run | tail -10`:
```text
brief=sha256:67202d3597affeab4e5edcf15a1acef2f5e88ed00950ce17ff3012f5bb0472cd clips=4 plan=/private/tmp/wd-lhm4-cli/plan.json
summary clips=4 duration_s=9.332 gpu_work=false queue_submitted=false
ledger=/private/tmp/wd-lhm4-cli/run/run_ledger.json
```
Canonical plan `summary`: `clip_count=4`, `planned_duration_s=9.332`, `dry_run=true`, `gpu_work=false`, `queue_submitted=false`.

### AC Verification
| AC # | Requirement | Code Location | Test Location | Status |
|---|---|---|---|---|
| 1 | Installed `wgp`; help lists exactly doctor/brief/plan/status/review | `pyproject.toml:19`; `wangp/cli.py:195` | `tests/test_wgp_cli.py:46` | PASS |
| 2 | Typed brief validation, brief hash, field-specific failure, no plan | `wangp/cli.py:110`; consumes `predict.content_brief.load_content_brief` | `tests/test_wgp_cli.py:54` | PASS |
| 3 | Plan wraps existing gateway and remains no-GPU/no-submit | `wangp/cli.py:119`; calls `scripts.run_content_brief.main` | `tests/test_wgp_cli.py:72` | PASS |
| 4 | Read-only real SQLite queue state/counts/failures/attempts with byte identity preserved | `wangp/queue_view.py:60`; uses `JobQueue.list_state/get/attempt_history` and `scripts.run_jobs.dry_run_report` | `tests/test_wgp_cli.py:122` | PASS |
| 5 | Queue clips/failure/immutable attempts/evidence plus final review artifacts and provenance hashes | `wangp/queue_view.py:94`, `wangp/queue_view.py:181` | `tests/test_wgp_cli.py:144`, `tests/test_wgp_cli.py:158` | PASS |
| 6 | Local doctor checks Python/uv/imports/ffmpeg/ffprobe/SQLite/host seam/models/disk with remediations | `wangp/doctor.py:197` | `tests/test_wgp_cli.py:168` | PASS |
| 7 | Explicit host probe reports exactly five existing preflight kinds; default makes no host call | `wangp/doctor.py:154` wraps `services.jobs.preflight.run_preflight`; `wangp/doctor.py:197` | `tests/test_wgp_cli.py:205`, `tests/test_wgp_cli.py:214` | PASS |
| 8 | Stable 0/2/3/4 codes and deterministic secret-free JSON | `wangp/cli.py:251`; `docs/wgp-cli.md` | `tests/test_wgp_cli.py:122`, `tests/test_wgp_cli.py:248`, `tests/test_wgp_cli.py:258` | PASS |
| 9 | No gateway/runner/queue-transition/retry/renderer/QC semantic changes; wrapper delegates | Protected-file diff against main is clean; `wangp/cli.py`, `wangp/queue_view.py` call existing seams only | `tests/test_wgp_cli.py:72`, `tests/test_wgp_cli.py:122` | PASS |

Additional operator-facing documentation: `README.md:71` and `docs/wgp-cli.md`.

LEARNINGS:
- The stable wrapper could preserve all engine semantics with zero edits to the protected runner/QC files; the existing seams were sufficient.
- `JobQueue` can open the copied committed fixture without changing database bytes, but the test must copy first because SQLite may create WAL/SHM sidecars.
- Verifying only content-derived path/hash pairs from `final-provenance.json` avoids the known cross-checkout row-identity trap; this run has 21 such checks and all match.
- `pytest -q` in this repository does not print a final count on success, so the full-run count was derived from the 100% progress report (1,572 dots, one `s`) and the 1,573 collected tests.

### OBSERVATIONS (unrelated)
- The full suite has one environment-gated skip from the existing 3090 integration test; no new test is skipped.
- `uv build` was not run because duplicate package declarations are already tracked by WD-m1sj; `uv run wgp` proves the entry point.

### DISCOVERED_BUG
  title: Full suite emits Starlette/httpx deprecation warning
  context: `uv run --frozen --extra dev pytest -q tests/` exits 0 but warns at `.venv/lib/python3.14/site-packages/fastapi/testclient.py:1`: StarletteDeprecationWarning about using `httpx` with `starlette.testclient`; it recommends `httpx2`. This is dependency/toolchain maintenance outside WD-lhm4.
  affected_files: `pyproject.toml` dependency/test extra resolution
  discovered_during: WD-lhm4

### DISCOVERED_BUG
  title: Prompt-director test docstring emits Python SyntaxWarning
  context: An initial full-suite invocation warned at `tests/test_prompt_director.py:195` that `"\w"` is an invalid escape sequence. The final cached run did not repeat it, but the source remains non-raw and Python will eventually reject/alter the escape.
  affected_files: `tests/test_prompt_director.py:195`
  discovered_during: WD-lhm4

### DISCOVERED_BUG
  title: CI workflow emits runner deprecation annotations
  context: Successful run 35624803571 reported that `actions/setup-python@v5` and `astral-sh/setup-uv@v6` target deprecated Node.js 20 and are forced to Node 24; it also warned that `ubuntu-latest` migrates to Ubuntu 26 on 2026-10-19.
  affected_files: `.github/workflows/ci.yml:18`, `.github/workflows/ci.yml:22`, `.github/workflows/ci.yml:25`
  discovered_during: WD-lhm4

## nd_contract
status: delivered

### evidence
- Commit `0e50b5a592a8e392c1595c5f3de024f2d820589f`; PR #152.
- Targeted CLI tests: 11 passed. Full suite: exit 0, 1,572 passed / 1 pre-existing skip. Coverage: 86%.
- Required CI run 35624803571 at the exact pushed head: success.
- `git diff --check`, protected-file diff, and `pvg verify` all passed.

### proof
- [x] AC #1: `wgp` console entry point and exact stable help verbs are installed/tested.
- [x] AC #2: typed brief validation, hash success, and field-specific non-writing failure are tested.
- [x] AC #3: `wgp plan` delegates to the existing no-GPU gateway and preserves summary/output contract.
- [x] AC #4: real JobQueue status is read-only and byte identity is asserted.
- [x] AC #5: queue review and final provenance artifact/hash review are tested.
- [x] AC #6: local doctor readiness/remediation behavior is tested.
- [x] AC #7: explicit five-kind host preflight and default no-call behavior are tested.
- [x] AC #8: stable exit codes and deterministic JSON are tested/documented.
- [x] AC #9: protected engine semantics are unchanged and delegation is demonstrated.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-21.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: in_progress

### evidence
- Claimed by dev-WD-lhm4; implementation started at main bc9b13f on story/WD-lhm4.

### proof
- [ ] Pending implementation

## History
- 2026-09-21T13:56:15Z dep_added: blocked_by WD-3nwm
- 2026-09-21T13:56:16Z dep_added: blocks WD-fp49
- 2026-09-21T13:56:17Z dep_added: blocks WD-fq1o
- 2026-09-21T15:36:38Z dep_removed: was_blocked_by WD-3nwm
- 2026-09-21T15:41:16Z status: open -> in_progress
- 2026-09-21T15:41:16Z auto-follows: linked to predecessor WD-3nwm
- 2026-09-21T15:41:16Z claimed by dev-WD-lhm4
- 2026-09-21T16:22:47Z status: in_progress -> in_progress
- 2026-09-21T16:26:19Z status: in_progress -> in_progress
- 2026-09-21T16:26:40Z status: in_progress -> in_progress
- 2026-09-21T16:28:42Z status: in_progress -> in_progress
- 2026-09-21T16:34:13Z status: in_progress -> open
- 2026-09-21T16:34:13Z released by speed
- 2026-09-21T16:40:36Z status: open -> in_progress
- 2026-09-21T16:40:36Z claimed by dev-WD-lhm4
- 2026-09-21T17:28:56Z status: in_progress -> in_progress

## Links
- Parent: [[WD-t534]]
- Blocks: [[WD-fp49]], [[WD-fq1o]]
- Was blocked by: [[WD-3nwm]]
- Follows: [[WD-3nwm]]

## Comments

### 2026-09-21T13:59:00Z speed
Self-contained data note: the real read-only queue integration fixture is the Git-tracked database datasets/lf004-operator-dogfood-56f-recovery-20260921.jobs.db. Tests must copy it to temporary storage before opening if SQLite could create WAL/SHM sidecars; the committed database must remain byte-identical.

### 2026-09-21T16:34:13Z speed
## PM Decision
REJECTED [2026-09-21]:

EXPECTED: The story requires delivery notes containing the CLI transcripts, targeted/full test output, an AC-by-AC verification table, and delivery through pvg story deliver. The pm_acceptor contract also requires exact commands/counts/commit SHA/coverage, a LEARNINGS section, zero unowned warnings, and an explanation for exceeding the roughly-under-650-authored-LOC budget.

DELIVERED: The implementation itself independently passed behavioral verification at 0e50b5a592a8e392c1595c5f3de024f2d820589f: 11/11 CLI tests passed; full suite was 1572 passed, 1 skipped, 0 failed; README/doc examples worked; engine paths were unchanged. However, authoritative story evidence is absent: pvg story verify-delivery WD-lhm4 exited 1 with 4 checks passed and 5 failed (missing authoritative delivered contract, Implementation Evidence, Commands run, Summary, and commit SHA). The story comments contain only the queue-fixture note; the PR body is not the authoritative delivery record and lacks the required transcripts, AC table, coverage, and LEARNINGS. The story diff is 1108 insertions across 8 files versus the stated under-650 LOC budget, with no delivered explanation. The full test run also emitted one StarletteDeprecationWarning that is not owned in the story evidence.

GAP: A PM cannot infer authoritative developer proof from an external PR description, and the unexplained diff-budget and warning exceedances violate the delivery contract even though the runtime behavior passed.

FIX: Re-deliver with an authoritative story evidence block containing exact CLI transcripts, every command run and pass/fail count, coverage, commit SHA and branch, an AC-by-AC table, a LEARNINGS section, and either an explanation for the 1108-line diff or a reduced diff. File or explicitly own the pre-existing StarletteDeprecationWarning as required by the zero-warnings rule. Then run pvg story verify-delivery WD-lhm4 successfully before PM review.

## nd_contract
status: rejected

### evidence
- pvg story verify-delivery WD-lhm4: exit 1; Passed 4, Failed 5.
- pvg nd comments list WD-lhm4: only queue-fixture note, no developer evidence.
- git diff --numstat main...HEAD totals 1108 insertions, 1 deletion across 8 files.
- Independent full pytest execution: 1572 passed, 1 skipped, 0 failed, plus one StarletteDeprecationWarning.

### proof
- [ ] Authoritative story implementation evidence, commands, commit SHA, coverage, AC table, and LEARNINGS are present.
- [ ] pvg story verify-delivery WD-lhm4 passes.
- [ ] The diff-budget overrun is explained or reduced.
- [ ] The full-suite warning is owned or eliminated.

### 2026-09-21T17:29:56Z speed
## Implementation Evidence

Commands run: targeted/full pytest, git diff checks, pvg verify, uv build, throwaway-venv wheel doctor smoke, and required CI watch/read.
Summary: all seven review defects fixed at faeac0c9092952f78e5c5944f0dabf4e805b4db2; 17 targeted passed, 1578 full passed / 1 skip, CI 35631378806 success.
Commit: faeac0c9092952f78e5c5944f0dabf4e805b4db2

## nd_contract
status: delivered

### evidence
- Full authoritative evidence is in the story Implementation Evidence note above.
- Producing commit: faeac0c9092952f78e5c5944f0dabf4e805b4db2.

### proof
- [x] AC #1 through AC #9 verified with commands, tests, build smoke, and CI evidence.
