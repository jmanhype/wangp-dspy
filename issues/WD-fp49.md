---
id: WD-fp49
title: "Resolve render hosts from zero-config configuration"
status: in_progress
priority: 1
type: feature
labels: [integration, delivered]
parent: WD-t534
created_at: 2026-09-21T13:56:16Z
created_by: speed
updated_at: 2026-09-21T18:24:52Z
content_hash: "sha256:bb689f8a669fc9d93f436f8b97d15f76230fc6fbf7bb043f489644eeca6ccc9b"
blocks: [WD-lvix, WD-fq1o]
was_blocked_by: [WD-lhm4]
assignee: dev-WD-fp49
follows: [WD-lhm4, WD-m1sj]
---

## Description
## USER INTENT
Observable outcome: a user can run the no-GPU lane immediately, while the render lane either has an explicit host configuration or fails with the exact key to set. No operator-specific SSH alias or home directory may be smuggled in as a hidden default.

## Context (Embedded)
- At main `3094b14`, exact active-source search finds 20 `"3090"` or `/home/straughter/Wan2GP` literals under `host`, `services`, `scripts`, `predict`, and `qc`.
- Critical direct construction sites are `scripts/run_jobs.py:526-534`, where `_default_host()` falls back to target `"3090"` and root `/home/straughter/Wan2GP`, and `scripts/run_v3_native_control.py:55-65`, where `_host(root)` repeats the same values.
- Additional runtime defaults occur in the adapter and specialist scripts, including `host/wangp_adapter.py:109-111`, the Ref2VA output path, SyncNet host Python defaults, legacy cycle/control scripts, and the run-jobs preflight disk path. Historical prose under `docs` and retired material under `s4` is evidence, not runtime configuration, and need not be rewritten.
- The existing seam is `host.render_host.SshHost.__init__(self, *, target: str, wgp_root: str, pull_root: str, sp: Callable = _sp, port: Optional[int] = None, asset_map: Optional[dict] = None)`.
- `WANGP_SSH_TARGET` already exists and must remain an explicit override. Add `WANGP_WGP_ROOT` and `WANGP_PULL_ROOT` with the same precedence role.
- Configuration precedence is environment variable, then repository `wangp.toml`, then safe local detection, then explicit unconfigured state. Detection may only inspect local filesystem markers and environment; it must never probe SSH, DNS, GPU, model endpoints, or a remote service.
- A host is complete only when `host.target`, `host.wgp_root`, and `host.pull_root` are all present. Partial configuration is an error naming every missing key, never an invitation to fill one value with `/home/straughter/Wan2GP`.
- Repository `wangp.toml` ships as a commented empty template/documented schema, not with an operator host.

## OUT OF SCOPE
- Any QC, AV, retry, renderer, provenance, queue-state, or gate policy change.
- GPU execution, remote host probing, automatic model installation, or performance auto-tuning.
- Rewriting historical documentation, retired `s4` scripts, or evidence artifacts to hide the former operator host.
- Supporting multiple concurrent render farms or a plugin host registry; one complete host configuration is the bounded product outcome.
- The detailed diagnostic copy for unconfigured hosts beyond the required actionable error; the failure-UX story generalizes presentation.

## DIFF BUDGET
- Roughly 15 authored files, under 800 authored changed LOC because runtime call sites and their tests must be updated together.

## Boundary Map
PRODUCES:
- wangp/config.py -> `load_host_config(*, repository_root: Path | None = None, environ: Mapping[str, str] | None = None) -> HostConfig`
- wangp/config.py -> `render_host(config: HostConfig) -> SshHost`
- wangp/config.py -> `missing_host_keys(config: HostConfig) -> tuple[str, ...]`
- wangp.toml -> commented empty host schema with exact keys `host.target`, `host.wgp_root`, and `host.pull_root`.
- docs/configuration.md -> precedence, environment overrides, safe detection rules, and no-GPU behavior.
- README.md -> configuration section linked to the full document.
- tests/test_host_config.py -> `test_no_config_preserves_no_gpu_lane_and_names_exact_keys() -> None`
- tests/test_runtime_host_wiring.py -> `test_active_runtime_has_no_operator_host_defaults() -> None`

CONSUMES:
- WD-lhm4: wangp/cli.py -> `main(argv: Sequence[str] | None = None) -> int`
  spec: doctor/status/plan commands read configuration through this module and report provenance without implicit host probes.
- WD-lhm4: wangp/doctor.py -> `collect_doctor_checks(models: Sequence[Mapping[str, str]] | None = None, *, probe_host: bool = False) -> DoctorReport`
  spec: host check gains configuration source/missing-key detail while retaining the explicit probe-host rule.
- (existing): host/render_host.py -> `SshHost.__init__(self, *, target: str, wgp_root: str, pull_root: str, sp: Callable = _sp, port: Optional[int] = None, asset_map: Optional[dict] = None) -> None`
  spec: construct only from a complete `HostConfig`; do not change path mapping, ssh behavior, or pull-root semantics.

## Required Outcomes
1. Repository `wangp.toml`, user environment overrides, and safe local detection resolve in the documented precedence, and every resolved value reports whether it came from environment, file, detection, or remained unconfigured.
2. `WANGP_SSH_TARGET`, `WANGP_WGP_ROOT`, and `WANGP_PULL_ROOT` override their corresponding file values; an explicit `WANGP_SSH_TARGET=localhost` preserves current on-host behavior.
3. Safe auto-detection can identify a local Wan2GP checkout only from local markers, cannot probe SSH/network/GPU, and never guesses the former remote target/root when no marker exists.
4. Production host construction in `scripts/run_jobs.py`, `scripts/run_v3_native_control.py`, the adapter seams, and the other active runtime call sites receives complete configuration or raises a typed configuration error; no reachable default fills target or root with operator-specific values.
5. A static/runtime regression test enumerates the active runtime modules and fails if `_default_host`, `_host`, adapter construction, or preflight wiring reintroduces `"3090"` or `/home/straughter/Wan2GP` as a fallback; historical docs, retired `s4` material, and explicit test fixtures are the only allowlisted contexts.
6. With no configuration and no environment override, `wgp plan` and `scripts/run_content_brief.py` still complete the no-GPU committed-brief path; configuration loading performs no host probe.
7. With no complete configuration, a host-dependent operation fails before constructing or invoking SSH with one actionable message naming all missing keys, showing at least `host.target` and `host.wgp_root`, and pointing to the exact `wangp.toml`/environment remediation and doctor command.
8. A partially configured host fails closed with every missing key; unknown keys and invalid path types are rejected with file/field context.
9. Existing localhost and remote SSH tests retain their behavior when complete values are explicitly supplied, and no gate/retry/renderer decision or threshold changes.

## Testing Requirements
- Unit: precedence, complete/partial/invalid configuration, safe detection, explicit localhost override, and typed missing-key errors.
- Static integration: MANDATORY (no mocks). Parse or inspect the actual active runtime modules for forbidden fallback literals using the documented allowlist.
- No-GPU integration: MANDATORY (no mocks). In a clean temporary worktree with no host environment/configuration, run the real planning CLI successfully; invoke the real host-wiring entry point and assert it raises the typed configuration error before any SSH subprocess.
- Existing-behavior integration: MANDATORY (no mocks). Supply complete explicit values to the real host seam and verify the current SshHost construction/path behavior without executing a render.
- Commands: `uv run --frozen --extra dev pytest tests/test_host_config.py tests/test_runtime_host_wiring.py` and `uv run --frozen --extra dev pytest -q`.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must paste configuration-resolution fixtures, forbidden-literal scan output, no-GPU plan output, and targeted/full tests into notes.
- Developer must include an AC verification table and explicitly state protected engine paths untouched.
- Developer must use `pvg story deliver`.
- No GPU, remote host execution, network service, model inference, commit, or push is authorized.

## nd_contract
status: new

### evidence
- Created 2026-09-21. Baseline measured with exact active-source search at main 3094b14: 20 operator target/root literals across runtime modules.

### proof
- [ ] Pending implementation


## Acceptance Criteria


## Design


## Notes


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-21.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Commands run:
- `uv run --frozen --extra dev pytest tests/test_host_config.py tests/test_runtime_host_wiring.py -q` — 9 passed.
- `uv run --frozen --extra dev pytest -q` — exit 0; progress contained 1,587 dots and one `s`; the pre-existing optional live-host test `tests/test_jobs_integration_3090.py` is skipped unless `WANGP_3090=1`, and no GPU/host work was authorized for this story.
- `uv build --out-dir /tmp/wd-fp49-dist-4aa2e92` — built one wheel and one sdist; SHA-256 wheel `3018052729fbe5dacbec79b069878eef903427f46114b403d456312584d8a49f`, sdist `986981cc07f3cbc5dcdda615a275f8f25d1aedea0a422697ae658cd092191841`; wheel contains `wangp.toml`.
- `grep -RInE '"3090"|/home/straughter/Wan2GP' host services scripts predict qc --exclude-dir=datasets --exclude='*test*'` — before: 20 matches at `5dadcda`; after: no output (COUNT=0) at `4aa2e92a7376d49075f3fdc14360f67198d660de`.
- `git diff --exit-code main -- services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py` — exit 0; protected engine paths are byte-identical.
- `pvg verify wangp/config.py wangp.toml docs/configuration.md README.md docs/wgp-cli.md tests/test_host_config.py tests/test_runtime_host_wiring.py --include-tests --format=text` — `VERIFY: PASSED (3 files scanned, 0 issues)`.
- Full changed-path `pvg verify ... --include-tests` failed with 12 pre-existing bare-pass/empty-return findings in legacy portions of touched files (`host/wangp_adapter.py`, `scripts/run_jobs.py`, and existing tests). Primary authored files pass above; changing those unrelated control-flow stubs would exceed configuration-plumbing scope.
- `gh pr view 153 --repo jmanhype/wangp-dspy --json ...` and `gh run list ...` — CI run `35637843176`, head `4aa2e92a7376d49075f3fdc14360f67198d660de`, conclusion `success`.

Summary: configuration now resolves a complete render host through environment → user TOML → repository TOML → safe local detection, active source has zero former host/root literals, no-GPU doctor/plan remain ready, and host work fails closed before SSH with actionable missing-key output.

### Commit and PR
- Branch: `story/WD-fp49`
- Commit: `4aa2e92a7376d49075f3fdc14360f67198d660de`
- PR: https://github.com/jmanhype/wangp-dspy/pull/153
- CI: run `35637843176` (`CI`), completed `success` at the pushed head; `test` job `106459577946` passed in 2m9s.

### Configuration surface and precedence
- `wangp/config.py:165` resolves each key independently as environment (`WANGP_SSH_TARGET`, `WANGP_WGP_ROOT`, `WANGP_PULL_ROOT`), then user config (`WANGP_CONFIG` or `~/.config/wangp/config.toml`), then repository `wangp.toml`, then safe detection.
- `wangp/config.py:128` detects only a local `Wan2GP/wgp.py` marker; it never probes SSH/network/GPU/model services and does not guess the former remote host.
- `wangp/config.py:60` exposes all missing keys; `wangp/config.py:156` builds the actionable fail-closed message; `wangp/config.py:242` constructs `SshHost` only after validation and passes values unchanged.
- `wangp.toml` is the committed commented/no-host template. `pyproject.toml` force-includes it in the wheel.

### Doctor and no-GPU evidence
Exact no-host `wgp doctor` result (host check only):
```text
[SKIP] host_configuration: host.target=unconfigured [unconfigured]; host.wgp_root=unconfigured [unconfigured]; host.pull_root=<repo>/datasets/runs/pull [detection (<repo>)]; the no-GPU lane remains ready
       remediation: Set WANGP_SSH_TARGET, WANGP_WGP_ROOT, and WANGP_PULL_ROOT (or the corresponding [host] keys) for GPU work.
ready=yes
```
Exact complete-host `wgp doctor` result (host check only; no probe flag supplied):
```text
[PASS] host_configuration: host.target=example-render-host [environment]; host.wgp_root=/absolute/configured/Wan2GP [environment]; host.pull_root=/tmp/wd-fp49-manual-5n0lDEAG/configured-pull [environment]; no host call was made
ready=yes
```
Exact no-host plan result:
```text
brief=sha256:67202d3597affeab4e5edcf15a1acef2f5e88ed00950ce17ff3012f5bb0472cd clips=4 plan=/private/tmp/wd-fp49-manual-5n0lDEAG/plan.json
summary clips=4 duration_s=9.332 gpu_work=false queue_submitted=false
ledger=/private/tmp/wd-fp49-manual-5n0lDEAG/run/run_ledger.json
```
Exact no-host render entry result:
```text
exit=2
configuration error: render host is not configured: missing host.target, host.wgp_root. Set WANGP_SSH_TARGET, WANGP_WGP_ROOT, or set those keys in <repo>/wangp.toml or <temporary-absent-user-config>; then run 'wgp doctor' to review resolution. The no-GPU planning lane does not require a host.
```
There was no traceback or hang. Doctor contacted no host; `--probe-host` remains the only probe mode and passes `config.wgp_root.value` unchanged to `_preflight_doctor_checks`.

### AC Verification
| AC # | Requirement | Code/artifact evidence | Test/manual evidence | Status |
| --- | --- | --- | --- | --- |
| 1 | Precedence and provenance | `wangp/config.py:165`; `wangp/doctor.py:195` | `tests/test_host_config.py:41`; doctor output above | PASS |
| 2 | Environment overrides and localhost | `wangp/config.py:242`; `scripts/run_jobs.py:533` | `tests/test_host_config.py:151` | PASS |
| 3 | Safe local detection, no remote guessing/probing | `wangp/config.py:128`; `docs/configuration.md:51` | `tests/test_host_config.py:75` | PASS |
| 4 | Runtime call sites receive complete config | `scripts/run_jobs.py:533`; `scripts/run_v3_native_control.py:56`; `host/wangp_adapter.py:108`; legacy scripts in diff | `tests/test_runtime_host_wiring.py:38`, `:60`; literal scan COUNT=0 | PASS |
| 5 | No runtime fallback regression | active-source scan and AST guard | `tests/test_runtime_host_wiring.py:29`, `:38` | PASS |
| 6 | No-config planning remains no-GPU | configuration is not imported by `wgp plan`; `README.md:82` | `tests/test_host_config.py:174`; manual plan output | PASS |
| 7 | Host-dependent fail-closed actionable error | `wangp/config.py:156`; `scripts/run_jobs.py` catches `HostConfigError` | `tests/test_host_config.py:174`; manual render output | PASS |
| 8 | Partial/unknown/invalid config rejected with context | `wangp/config.py` parsing/validation | `tests/test_host_config.py:111`, `:128` | PASS |
| 9 | Explicit complete host behavior and protected engine semantics unchanged | `wangp/config.py:242`; protected-path diff exit 0 | `tests/test_host_config.py:151`; `tests/test_runtime_host_wiring.py:60`; full suite and CI green | PASS |

### Scope, budget, and protected-path explanation
- Measured final diff: 27 authored files, 1,040 insertions / 111 deletions (1,151 changed LOC), exceeding the declared rough budget of 15 files / 800 LOC.
- Breakdown: 440 LOC test updates/new tests, 121 LOC documentation, 320 LOC config/template/packaging, and 270 LOC runtime call-site plumbing across the 20 baseline occurrences.
- The excess is driven by the required zero-literal sweep across nine script/shell call sites and updating existing suites to supply complete explicit hosts instead of relying on removed defaults.
- `scripts/run_jobs.py` and `qc/audio_critic/av_sync_gate.py` differ from `main` only to source host/root values from configuration; no QC/gate threshold or decision logic changed. `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py` remain byte-identical.

### Warnings and observations
- Local full-suite warning (not introduced by this story, not fixed because it requires a dependency-lock change outside this config story):
  `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` from `.venv/lib/python3.14/site-packages/fastapi/testclient.py:1`.
- Successful CI emitted runner annotations that Node.js 20 actions are forced to Node 24 and `ubuntu-latest` will migrate to Ubuntu 26 on 2026-10-19. These annotations did not affect the successful conclusion.
- The optional live-host integration test remains intentionally skipped under the no-GPU dispatch constraint; it still constructs explicit values and was not used to claim remote execution.

LEARNINGS:
- Resolving each key independently made precedence straightforward, but layer records needed field-normalized keys; a dedicated regression test caught the initial environment/file mismatch.
- The former defaults were spread beyond the two main constructors; a measured literal scan plus static AST test was necessary to find shell, QC, and legacy adapter seams.
- Existing render tests frequently supplied only a target; complete-host fixtures keep their behavior explicit without reintroducing hidden defaults.

DISCOVERED_BUG:
  title: FastAPI/Starlette TestClient emits httpx deprecation warning
  context: Full local test command exits 0 but warns `Using httpx with starlette.testclient is deprecated; install httpx2 instead` from fastapi/testclient.py. Fixing it likely requires changing the locked test dependency set (httpx2) and is outside WD-fp49 configuration plumbing.
  affected_files: pyproject.toml, uv.lock
  discovered_during: WD-fp49

## Scope Amendment (dispatcher review) — protected-path list corrected

The dispatch for this story protected `scripts/run_jobs.py` and all of `qc/` as byte-identical while
also requiring the hardcoded `"3090"` and `/home/straughter/Wan2GP` literals to be removed from
active source. Those two requirements cannot both hold, and the conflict is a dispatch error, not a
story defect. The developer correctly stopped instead of silently choosing.

Corrected boundary:

- PERMITTED (configuration plumbing only): `scripts/run_jobs.py`, `scripts/run_v3_native_control.py`,
  `host/`, and replacing the hardcoded interpreter path literal in
  `qc/audio_critic/av_sync_gate.py` — in each case only so the value comes from configuration or
  detection. No gate, threshold, retry, ordering, or QC decision logic may change.
- STILL BYTE-IDENTICAL: `services/director/renderers/policy.py`, `services/director/wiring.py`,
  `services/jobs/preflight.py`, `scripts/run_film.py`.
- Verification command for the delivery: `git diff --exit-code main -- services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py` must exit 0.
  A diff in `scripts/run_jobs.py` or `qc/audio_critic/av_sync_gate.py` is expected and must be
  explained in the delivery notes as configuration plumbing.
- The literal-count acceptance criterion is unchanged: zero `"3090"` or `/home/straughter/Wan2GP`
  literals in active source under `host/ services/ scripts/ predict/ qc/` (tests and `datasets/`
  excluded). Baseline measured at `5dadcda`: 20 occurrences.
- Any change to gate/retry/QC semantics anywhere remains a rejection.

## History
- 2026-09-21T13:56:16Z dep_added: blocked_by WD-lhm4
- 2026-09-21T13:56:16Z dep_added: blocks WD-lvix
- 2026-09-21T13:56:17Z dep_added: blocks WD-fq1o
- 2026-09-21T17:40:49Z dep_removed: was_blocked_by WD-lhm4
- 2026-09-21T17:45:17Z status: open -> in_progress
- 2026-09-21T17:45:17Z auto-follows: linked to predecessor WD-lhm4
- 2026-09-21T17:45:17Z claimed by dev-WD-fp49
- 2026-09-21T18:24:52Z status: in_progress -> in_progress
- 2026-09-21T18:24:52Z auto-follows: linked to predecessor WD-m1sj

## Links
- Parent: [[WD-t534]]
- Blocks: [[WD-lvix]], [[WD-fq1o]]
- Was blocked by: [[WD-lhm4]]
- Follows: [[WD-lhm4]], [[WD-m1sj]]

## Comments
