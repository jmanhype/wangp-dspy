---
id: WD-fp49
title: "Resolve render hosts from zero-config configuration"
status: closed
priority: 1
type: feature
labels: [integration, delivered]
parent: WD-t534
created_at: 2026-09-21T13:56:16Z
created_by: speed
updated_at: 2026-09-21T19:31:26Z
content_hash: "sha256:3f7cf6ec196c3d81e24cca4d70aa422f38df8945f00b73cedaf2e4c897128042"
was_blocked_by: [WD-lhm4]
follows: [WD-lhm4, WD-m1sj, WD-3nwm]
closed_at: 2026-09-21T19:31:26Z
close_reason: "Accepted: Rework 9df6f888b304ff5ccc97981aed3558fadd430266 independently closes all eleven PR review threads. Reproduced run_qc before RC=1 NameError and after RC=2 actionable; verified ~/.config user_config provenance with XDG unset; all four gpu_seq callers pass the resolved environment; remote marathon exits 2 before local use; adapter raises HostConfigError before host execution; detection is atomic; installed pull root uses XDG data; relative paths fail; SyncNet needs only wgp_python; configured arbitrary interpreter replaces root/venv; marathon compound discovery moved to helpers. Also verified zero forbidden literals, no-GPU doctor ready and exact plan summary, render entry exit 2 with empty fake-SSH log, protected-path diff exit 0, targeted 24 passed, full 1602 passed/1 optional skip, wheel+sdist contain behavior and reproducible hashes, and required CI test SUCCESS at the exact head. verify-delivery label-format failures are known WD-7zrq tracker friction, not substance."
assignee: dev-WD-fp49
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


## Implementation Evidence (Rejection 2 rework)

Commands run:
- RED at b35bad3: `uv run --frozen --extra dev pytest tests/test_wd_fp49_rework.py -q` — exit 1; all 14 newly authored review-regression tests failed against the rejected behavior.
- GREEN at 9df6f88: `uv run --frozen --extra dev pytest tests/test_wd_fp49_rework.py -q` — 15 passed (the added run-jobs exact-key test brings the file to 15).
- Required targeted run at 9df6f88: `uv run --frozen --extra dev pytest tests/test_host_config.py tests/test_runtime_host_wiring.py tests/test_wd_fp49_rework.py -q` — 24 passed.
- Full suite at 9df6f88: `uv run --frozen --extra dev pytest -q` — exit 0; 1,603 collected, 1,602 passed and the pre-existing optional live-host test skipped. Output retained one pre-existing third-party `StarletteDeprecationWarning` from FastAPI's TestClient import; no project test failed.
- Packaging at 9df6f88: `uv build --out-dir /tmp/wd-fp49-dist-head.8Z10Gj` — wheel and sdist built; SHA-256 wheel `d33b360de5500483286e965efe7f71c8be2e2f0f7a4725ca8e3c31d4a16a617a`, sdist `2aff350c425937450f550097aca967b32259f99ae80095746ae61564383114c9`; wheel contains `wangp.toml=true`.
- Protected engine check: `git diff --exit-code main -- services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py` — exit 0.
- Forbidden-literal check: `grep -RInE '"3090"|/home/straughter/Wan2GP' host services scripts predict qc --exclude-dir=datasets --exclude='*test*'` — COUNT=0.
- No-GPU doctor: exit 0, `host_configuration` SKIP, `ready=yes`, and all four resolved fields reported.
- No-GPU plan: exit 0, `clips=4`, `gpu_work=false`, `queue_submitted=false`.
- No-host render entry: exit 2 before SSH with `missing host.target, host.wgp_root, host.wgp_python` and the exact environment/config remediation; no traceback or hang.
- `pvg verify README.md docs/configuration.md docs/wgp-cli.md wangp.toml wangp/config.py wangp/doctor.py wangp/gpu_sequencing.py scripts/ab_render_qc.py scripts/run_batch.py scripts/run_qc.py scripts/marathon/... tests/test_wd_fp49_rework.py --include-tests --format=text` — `VERIFY: PASSED (12 files scanned, 0 issues)`.
- Full changed-path `pvg verify ... --include-tests` — FAILED with 9 pre-existing bare-pass/empty-return findings in legacy portions of `host/wangp_adapter.py`, `scripts/run_jobs.py`, and existing tests (`host/wangp_adapter.py:464,894,919,925`; `scripts/run_jobs.py:82`; `tests/test_night2_convergence.py:246`; `tests/test_seam_hardening.py:312,376`; `tests/test_run_jobs_worker.py:477`). Repairing those control-flow stubs would exceed this configuration-rework scope; the newly authored configuration/module/test surface passes above.
- Push and CI: `git push origin story/WD-fp49`; `gh run watch 35643179609 --repo jmanhype/wangp-dspy --exit-status --interval 10` — success.

Summary: all eleven pre-merge review defects are fixed as configuration plumbing; precedence and fail-closed behavior remain intact, local detection can no longer mix machines, installed users stage outside site-packages, remote marathon use is rejected before local filesystem access, sequencing carries the resolved target, and Wan2GP/remote-SyncNet interpreters are explicitly configurable rather than assumed under `<wgp_root>/venv/bin/python`.

### Commit and PR
- Branch: `story/WD-fp49`
- Commit: `9df6f888b304ff5ccc97981aed3558fadd430266`
- PR: https://github.com/jmanhype/wangp-dspy/pull/153
- CI run: `35643179609` (`CI`), head `9df6f888b304ff5ccc97981aed3558fadd430266`, conclusion `success`; required `test` job `106477194196` passed in 1m58s.

### Review Finding Verification
| # | Rejection finding | Fix | Test / evidence |
| --- | --- | --- | --- |
| 1 | `run_qc.py` `NameError` | `scripts/run_qc.py:20` imports `os` for both configuration reads. | `tests/test_wd_fp49_rework.py:75` executes the real script with no host: RED returned 1 plus `NameError`; GREEN returns 2 with one actionable message. |
| 2 | documented user config ignored | `wangp/config.py:95` uses `Path.home()/.config/wangp/config.toml` when XDG is unset. | `tests/test_wd_fp49_rework.py:98` loads a real file from the documented default path and checks provenance. |
| 3 | batch/A-B lose TOML target | `wangp/gpu_sequencing.py:11` resolves the shared config; `scripts/run_batch.py:55,123` and `scripts/ab_render_qc.py:205,221` pass that environment to every `gpu_seq.sh` call. | File-only resolution test at `tests/test_wd_fp49_rework.py:119`; AST caller-coverage test at `:165` checks all four call sites. |
| 4 | marathon remote root used locally | `scripts/marathon/driver.sh:10-13` resolves target/root/interpreter and rejects any non-`localhost` target before `mkdir`, output discovery, `cp`, `cd`, or render execution. | Real subprocess test at `tests/test_wd_fp49_rework.py:194` exits 2 with `localhost-only` and proves `/home/straughter/marathon` was not created. |
| 5 | adapter `None` reaches `os.path.isfile` | `host/wangp_adapter.py:1596-1608` validates missing root/interpreter keys and raises shared `HostConfigError` before host execution. | Real render-entry test at `tests/test_wd_fp49_rework.py:231`; RED reproduced raw `TypeError`, GREEN names `host.wgp_root` and `host.wgp_python`. |
| 6 | partial config mixes machines | `wangp/config.py:277-291` applies target/root local detection only as an atomic pair when neither is explicit. | `tests/test_wd_fp49_rework.py:301` covers explicit-target-only and explicit-root-only near a real local `Wan2GP/wgp.py` marker. |
| 7 | installed pull root in site-packages | `wangp/config.py:172-184` uses repository staging only for source checkouts and `${XDG_DATA_HOME:-~/.local/share}/wangp/runs/pull` for installed templates. | `tests/test_wd_fp49_rework.py:337` builds an installed layout and rejects any pull root beneath site-packages. |
| 8 | relative roots accepted | `wangp/config.py:108-116` validates file and environment values; root/interpreter fields must be absolute. | Parameterized file+environment tests at `tests/test_wd_fp49_rework.py:370` cover `wgp_root`, `pull_root`, and `wgp_python`. |
| 9 | SyncNet requires unused host keys | `qc/audio_critic/av_sync_gate.py:110-123` resolves only `host.wgp_python`; it no longer calls `require_host_config`. | `tests/test_wd_fp49_rework.py:398` supplies a real host object plus only `WANGP_WGP_PYTHON`; construction succeeds without target/root/pull. |
| 10 | `<root>/venv/bin/python` assumption | Added optional `host.wgp_python` / `WANGP_WGP_PYTHON`; adapter and detached seams consume it at `host/wangp_adapter.py:122-128,685-713,1560-1567`. Safe localhost detection may use the current executable. | `tests/test_wd_fp49_rework.py:420` proves adapter and lock argv use Conda/system/venv executable instead of root-derived venv; existing explicit-override tests remain green. |
| 11 | inline marathon shell chains | Repository/config/output/triage/job/render helpers replace `cd && pwd`, `ls | head`, inline job Python, and direct `./venv/bin/python`. | Source-discipline test at `tests/test_wd_fp49_rework.py:221`; helper implementations are `scripts/marathon/repository-root.sh`, `resolve-config.sh/.py`, `latest-output.py`, `triage-outputs.py`, `prepare-job.py`, `job-premise.py`, `render-job.sh`, and `disk-usage-percent.sh`. |

### Acceptance Criteria Verification
| AC | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| 1 | Precedence/provenance | Existing precedence tests plus `wangp/config.py:233-275`; doctor reports all settings. | PASS |
| 2 | Environment overrides and localhost | Existing complete-host test; `ENVIRONMENT_KEYS` includes all four overrides. | PASS |
| 3 | Safe local detection, no probes/guessing | Atomic local-marker detection at `wangp/config.py:277-291`; detection tests. | PASS |
| 4 | Runtime call sites complete/fail closed | `run_jobs`, adapter, sequencing, QC, marathon, and legacy seams use shared config; targeted/static tests. | PASS |
| 5 | No operator fallback regression | Exact active-source scan COUNT=0 plus existing static runtime test. | PASS |
| 6 | No-GPU planning preserved | Manual doctor/plan outputs above and existing CLI integration tests. | PASS |
| 7 | One actionable pre-SSH render error | Manual exit-2 output above; exact keys and remediation. | PASS |
| 8 | Partial/invalid config rejected with context | Missing-key, unknown-key, type, absolute-path, and atomic-detection tests. | PASS |
| 9 | Existing explicit-host behavior and engine semantics unchanged | Explicit host/interpreter tests; protected-path diff exit 0. | PASS |

PROOF:
- Producing head: `9df6f888b304ff5ccc97981aed3558fadd430266`.
- Full suite: exit 0, 1,602 passed / 1 optional live-host skipped.
- Build: exit 0; wheel contains `wangp.toml`.
- Required CI: run `35643179609`, head `9df6f888b304ff5ccc97981aed3558fadd430266`, conclusion `success`.
- No GPU, SSH, remote host, or model inference was run.

LEARNINGS:
- File-only host configuration must be propagated into subprocess environments; a shared resolver is safer than duplicating one override at one call site.
- Local target and root detection must be atomic or a nearby checkout can silently splice into a remote host.
- Interpreter location is installation-specific and belongs in configuration, not in a path convention attached to `wgp_root`.

### OBSERVATIONS
- The full pytest output retains a pre-existing FastAPI/TestClient deprecation warning, and CI emits runner/action deprecation annotations; both are unrelated to this diff.
- Full changed-path `pvg verify` still reports the nine legacy stub markers listed above; the newly authored files and primary configuration surface pass.

## nd_contract
status: delivered

### evidence
- Rework commit: 9df6f888b304ff5ccc97981aed3558fadd430266.
- Targeted tests: 24 passed; review-regression file: 15 passed; full suite: 1,602 passed / 1 skipped.
- Build wheel SHA-256: d33b360de5500483286e965efe7f71c8be2e2f0f7a4725ca8e3c31d4a16a617a and contains wangp.toml.
- CI run 35643179609 at exact pushed head: success.

### proof
- [x] Review finding 1: real run_qc entry reaches actionable HostConfigError, not NameError.
- [x] Review finding 2: documented ~/.config/wangp/config.toml default is loaded.
- [x] Review finding 3: all gpu_seq callers receive file-resolved WANGP_SSH_TARGET.
- [x] Review finding 4: marathon rejects remote targets before local filesystem use.
- [x] Review finding 5: adapter raises actionable HostConfigError before LocalHost.check_executable(None).
- [x] Review finding 6: explicit target/root never combines with the other locally detected value.
- [x] Review finding 7: installed pull root is user data, never site-packages.
- [x] Review finding 8: relative root/interpreter values fail with source and field context.
- [x] Review finding 9: SyncNet requires only the interpreter it uses.
- [x] Review finding 10: Wan2GP interpreter is explicit and no longer root/venv-derived.
- [x] Review finding 11: marathon output/config work moved to helper scripts.

## nd_contract
status: in_progress

### evidence
- Claimed: 2026-09-21 rework after Rejection 2.

### proof
- [ ] Pending eleven PR-review fixes

## Rejection 2 (pre-merge PR review, PR #153): eleven findings, several are hard regressions

The story was accepted by PM review, but the PR carried eleven unresolved review threads that were
not triaged in that pass (a dispatcher process gap: earlier acceptor briefs explicitly asked for
thread triage; this one did not). I verified the two most severe myself and both are real. The
config work removed working defaults, and the new plumbing is incomplete in several call sites.

Severity grouping:

### Hard functional regressions (P0)
1. **`scripts/run_qc.py` crashes with `NameError`.** Verified by me on the branch: the file uses
   `os.environ` at lines 62 and 74 (added by this change) but never imports `os`
   (AST: `imports_os=false, uses_os=true`). Every QC invocation through that script — including the
   post-render stage — fails before it resolves a host.
2. **The documented user config path is ignored.** Verified by me: `_user_config_path` returns
   `Path.home() / "wangp" / "config.toml"` when `XDG_CONFIG_HOME` is unset, i.e. `~/wangp/config.toml`,
   while README and `docs/configuration.md` document `~/.config/wangp/config.toml`. Users following
   the docs stay unconfigured.
3. **Batch and A/B orchestration lose the target.** `scripts/run_batch.py` and `scripts/ab_render_qc.py`
   call `gpu_seq.sh` without the `WANGP_SSH_TARGET` override that `gpu()` supplies, but `gpu_seq.sh`
   requires it; when the target exists only in TOML configuration, status polling and A/B start/stop
   exit before reaching SSH.
4. **Marathon driver treats a remote root as a local path.** `scripts/marathon/driver.sh` resolves the
   configured `wgp_root` but then uses it with local `ls`, `cp`, `cd`, and interpreter execution, so a
   remote target reads a nonexistent local path instead of using host transport.
5. **Adapter fails with a raw `TypeError`.** `host/wangp_adapter.py` leaves `venv_python`/`wgp_script`
   as `None` when no root is resolvable, and a later render passes `None` into
   `LocalHost.check_executable()` → `os.path.isfile()` raises `TypeError` instead of the actionable
   incomplete-configuration error.

### Correctness (P1)
6. **Partial configuration can mix machines.** Detection fills a missing root from a *locally*
   detected checkout even when the target came from explicit remote configuration (and vice versa),
   producing a host whose target and remote namespace refer to different machines.
7. **Installed users get a site-packages pull root.** The wheel-provided template is discovered inside
   site-packages, so the derived `pull_root` lands under the installation directory; on a read-only
   install this fails, otherwise it writes into the installed package tree.
8. **Relative root values are accepted** despite the absolute-path contract, so a relative
   `host.wgp_root` is interpreted from the SSH login directory and a relative `host.pull_root` from the
   caller's cwd.
9. **`qc/audio_critic/av_sync_gate.py` over-requires configuration.** It calls `require_host_config`
   merely to derive an interpreter path, so local or fake-host callers with an explicit model and
   repository fail during judge construction for keys the derivation never uses.
10. **Wan2GP interpreter assumption is too narrow.** `host/wangp_adapter.py` derives the renderer
    interpreter as `<host.wgp_root>/venv/bin/python`; Wan2GP supports arbitrary venv paths, Conda, and
    system Python, so those supported installs fail executable validation (the same assumption also
    reaches the default SyncNet interpreter).

### Rule violation (P2)
11. **Inline shell chains in the marathon driver.** `scripts/marathon/driver.sh` uses inline command
    substitutions and `ls | head` pipelines inside assignments, contrary to this repository's shell
    discipline (script files over inline compound one-liners).

Required: fix each with a test that fails against the current behaviour; keep the zero-hardcoded-literal
property; no gate/retry/QC-decision semantics changes; `uv run --frozen --extra dev pytest -q` and
`uv build` must stay green; update the docs if any documented path or precedence changes. If item 9 or
10 cannot be fixed without touching protected engine semantics, say so explicitly and propose the
smallest safe change instead of guessing.

## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-21.

### proof
- [x] Story closed after accepted label was applied.


## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-09-21.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


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
- 2026-09-21T18:39:27Z status: in_progress -> open
- 2026-09-21T18:39:27Z released by speed
- 2026-09-21T18:46:12Z status: open -> closed
- 2026-09-21T18:46:12Z dep_removed: no_longer_blocks WD-lvix
- 2026-09-21T18:46:12Z dep_removed: no_longer_blocks WD-fq1o
- 2026-09-21T18:47:35Z status: closed -> open
- 2026-09-21T18:48:28Z status: open -> in_progress
- 2026-09-21T18:48:28Z auto-follows: linked to predecessor WD-3nwm
- 2026-09-21T18:48:28Z claimed by dev-WD-fp49
- 2026-09-21T19:16:28Z status: in_progress -> in_progress
- 2026-09-21T19:31:26Z status: in_progress -> closed

## Links
- Parent: [[WD-t534]]
- Was blocked by: [[WD-lhm4]]
- Follows: [[WD-lhm4]], [[WD-m1sj]], [[WD-3nwm]]

## Comments

### 2026-09-21T18:39:27Z speed
## PM Decision
REJECTED [2026-09-21]:
EXPECTED: The story Boundary Map produces `wangp/config.py -> render_host(config: HostConfig) -> SshHost`, and the pm_acceptor quality gate requires a type specification on every public function.
DELIVERED: `wangp/config.py:242` exports `def render_host(config: HostConfig):` with no return annotation. An AST audit reports `render_host: parameter_annotations=[True] returns=False`.
GAP: The public API does not match the declared boundary contract and fails the public-function type gate. This is not the known tracker-format friction.
FIX: Add a type-checking-only `SshHost` reference (avoiding the runtime import cycle) and declare `render_host(config: HostConfig) -> SshHost`; keep behavior unchanged. Re-run `uv run --frozen --extra dev pytest tests/test_host_config.py tests/test_runtime_host_wiring.py -q` and the full suite.

Independently reproduced passing evidence: precedence fixtures (environment over user over repository, per key; XDG user config; local marker detection), forbidden literal grep 20 -> 0 (raw byte count 23 -> 0), exact no-host plan fields, one actionable render error, fake-SSH log never created, doctor provenance without probes, protected engine diff exit 0, targeted 9 passed, full 1587 passed / 1 optional live-host skip, reproducible wheel/sdist hashes, and CI run 35637843176 success at 4aa2e92a7376d49075f3fdc14360f67198d660de. The 1,151-LOC overrun explanation is credible (test LOC independently measures exactly 440 and the broad causes are visible in the diff).

## nd_contract
status: rejected

### evidence
- AST audit of `wangp/config.py`: `render_host` lacks a return annotation at line 242.
- All required behavioral, static, build, and CI verification otherwise passed at the delivered head.

### proof
- [ ] Boundary Map: `render_host(config: HostConfig) -> SshHost` public signature is not implemented as declared.
