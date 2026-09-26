---
id: WD-obkn
title: "Finishing terminal disposition batch"
status: in_progress
priority: 1
type: task
labels: [capability, finishing, evidence, external-integration, delivered]
parent: WD-3nod
created_at: 2026-09-26T20:53:45Z
created_by: speed
updated_at: 2026-09-26T23:33:25Z
content_hash: "sha256:ed61e80807f9198ae14c9a0acc18b6b69f039855069f55b86199bf8a9304f3ef"
blocks: [WD-fay0]
blocked_by: [WD-r81u, WD-r4n8]
assignee: dev-WD-obkn
follows: [WD-5k28, WD-m7xw]
---

## Description
## USER INTENT
The five remaining finishing cells must stop being an ambiguous backlog: run the corrected local FFmpeg film-grain graph once, and terminalize the neural and face gaps with honest, operator-approved missing-input or host-implementation boundaries rather than fabricated GPU or quality claims.

## Embedded Evidence And Scope
The five current planned cells in `docs/finishing-capabilities.md` are:

1. `ffmpeg` / `film_grain`
2. `ffmpeg` / `face_refinement`
3. `neural_frame_gen` / `interpolation`
4. `neural_frame_gen` / `spatial_upscale`
5. `neural_frame_gen` / `face_refinement`

WD-r4n8 corrected the FFmpeg graph but explicitly did not execute it. At current main, `services/finishing/pipeline.py::_film_grain_filter_graph(...)` downsamples to `ceil(width/size) x ceil(height/size)`, creates seeded held `allf=u` and reseeded `allf=t+u` branches, blends with `temporal_persistence`, scales with nearest neighbor, crops the exact frame, and adds the grain.

The immutable test source is `datasets/runs/maestro-parity/WD-r81u/inputs/source.mp4`, SHA-256 `e8b690774b0df7a73c85505ea507277d2745641b34f68c60c24855882da88859`, measured 480x832, 24 fps, duration `2.333333 s`. The film run must use current-head FFmpeg controls `strength=12.0`, `size=16`, `temporal_persistence=0.5`, and a recorded seed; it must not reuse WD-r81u's pre-correction plan.

Existing boundary evidence says:

- `neural-frame-gen-boundary-probe.txt` found no named `neural_frame_gen` implementation in WanGP; the separate H3 face refiner is a different backend and cannot be relabelled.
- The local no-GPU compiler returns typed `FINISH_NEURAL_PATH_UNAVAILABLE` and never falls back to FFmpeg/RIFE/Real-ESRGAN.
- The compass source has no human face; no track detector, normalized bounds, selected-track identity, rights, or consent exists.
- `predict/finishing.py::FaceTrack` requires non-empty `track_id`, `identity_label`, `source`, `license`, and `consent_ref` with `extra="forbid"`, so a valid consented track cannot be synthesized from the current source.

## REQUIRED OPERATOR INPUTS — NOT YET PROVIDED
This story grants no execution. The operator must separately authorize the exact local FFmpeg command/host/time boundary and explicitly approve terminal missing-input/host-boundary dispositions for the four non-run cells. No SSH, GPU, remote host, download, model use, or face input is authorized by story creation.

## OUT OF SCOPE
- Any model download, neural/GPU execution, remote SSH, provider account, new backend implementation, or substitution of FFmpeg/RIFE/Real-ESRGAN for `neural_frame_gen`.
- Inventing a face track, identity, license, consent reference, detector result, or human-faced source.
- Changing grain semantics, thresholds, queue/preflight/renderer/wiring semantics, or the already verified four finishing cells.
- Reusing WD-r81u's old `noise=alls=12:allf=t+u` output as evidence for the corrected graph.

## DIFF BUDGET
- About 2 authored files and under 250 changed LOC: `docs/finishing-capabilities.md` plus the current-head plan, local ffmpeg logs, lossless/final artifacts, measurements, typed refusals, and boundary records under `datasets/runs/maestro-parity/WD-obkn/`.
- Keep the aggregate bundle under 512 MiB and commit no model weights.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-obkn/ -> terminal five-cell finishing evidence bundle
  spec: operator decisions, current-head graph, immutable source/output hashes, ffmpeg transcripts, measured size/persistence evidence, typed neural refusals, face-input absence proof, checker results, and exact matrix citations.
- docs/finishing-capabilities.md -> terminal five-cell finishing matrix updates
  event: mark only ffmpeg film grain `host_run_verified` on real evidence and mark the other four cells with operator-approved unsupported missing-input/host-boundary labels that do not claim hardware infeasibility.

CONSUMES:
- WD-r81u: datasets/runs/maestro-parity/WD-r81u/ -> immutable source, no-face review evidence, and neural/face boundary records
  source: reuse SHA-256 `e8b690774b...` read-only; cite `missing-required-inputs.md` and `neural-frame-gen-boundary-probe.txt` without relabelling their meaning.
  (existing): services/finishing/pipeline.py -> corrected `_film_grain_filter_graph(request, width, height, frame_rate) -> str`
  spec: current graph encodes ceil-grid size, held/reseeded seeded noise branches, persistence blend, nearest-neighbor expansion, exact crop, and addition; do not alter it.
- WD-651z: docs/maestro-parity-evidence-contract.md -> `wangp-dspy.maestro-parity-evidence/v1`
  source: canonical authorization, hash, gate, disposition, and reviewer semantics; absence of an implementation is not hardware infeasibility.
- WD-651z: scripts/verify_maestro_parity.py -> `verify_bundle(bundle: Path) -> VerificationReport`
  event: checker exit 0 is required for the successful film-grain bundle and any disposition the contract accepts as terminal boundary evidence.

## Story Acceptance Criteria
1. [State] Before execution, the bundle records verbatim operator approval for the exact local FFmpeg run and explicit terminal-disposition decisions for neural/face gaps; no run starts while either approval is absent.
2. [State] The film-grain request is regenerated at the story's recorded repository commit with backend `ffmpeg`, immutable source SHA-256 `e8b690774b0df7a73c85505ea507277d2745641b34f68c60c24855882da88859`, strength `12.0`, size `16`, temporal persistence `0.5`, and a new output path; its graph contains ceil/downsample by 16, both seeded `allf=u` and `allf=t+u` branches, `all_opacity=0.5`, nearest-neighbor x16 expansion, crop to `480x832`, and addition to `[0:v]`.
3. [State] One authorized local FFmpeg execution preserves the source unchanged, records exact argv/exit/stdout/stderr, emits the lossless intermediate and final H.264 output, hashes both, and measures matching duration/dimensions/fps/pixel format plus before/after decoded-frame evidence.
4. [State] A deterministic measurement on the lossless grain intermediate proves the declared controls from actual pixels: grain support is `16x16` within the pre-registered tolerance, held/reseeded mixture behavior is consistent with temporal persistence `0.5`, and the analyzer inputs, algorithm parameters, matrices, and output hashes are retained.
5. [State] The exact graph replay is deterministic for the same source/seed on the same FFmpeg build: replay hashes or decoded-frame hashes match, and any codec-level nondeterminism is measured rather than assumed away.
6. [Unwanted] `neural_frame_gen` interpolation and spatial upscale terminalize only as operator-approved unsupported host-implementation boundaries backed by the typed `FINISH_NEURAL_PATH_UNAVAILABLE` result and zero-hit named-implementation evidence; no FFmpeg/RIFE/Real-ESRGAN output is relabelled and no hardware-infeasibility claim is made.
7. [Unwanted] The two face-refinement cells terminalize only as operator-approved unsupported missing-required-input records proving the source has no human face and every `FaceTrack` source/license/consent/identity/bounds input is absent; no synthetic consent, detector result, or identity claim is created.
8. [State] `docs/finishing-capabilities.md` mechanically updates exactly the five named cells with exact bundle citations; the four existing verified cells and all other backend dispositions remain unchanged.
9. [Unwanted] No GPU process, CUDA backend, SSH command, network/model download, dependency change, source overwrite, or protected engine change occurs; `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py` remain unchanged.
10. [State] The canonical checker accepts the film-grain success evidence and every terminal boundary disposition; backlog lint has 0 errors, full pytest JUnit has `errors=0` and `failures=0`, release verification reports `release=ready` and `tag_created=false`, and diff/protected-file checks pass.

## Testing Requirements
- Real local-process integration MANDATORY with no mocks: execute the exact current-head FFmpeg graph, capture both stages, and run the measurement analyzer against emitted bytes.
- Run no-GPU typed-request probes for neural interpolation and spatial upscale and retain exit 2 plus `FINISH_NEURAL_PATH_UNAVAILABLE`; prove no media was emitted.
- Re-verify the existing no-face frame, zero-hit named-implementation evidence, and mandatory `FaceTrack` fields; do not perform SSH or host discovery.
- Invoke the WD-651z checker on the successful and disposition evidence; parse the final matrix for exactly the five intended transitions and no collateral changes.
- Run `pvg lint --backlog`; `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-obkn-full.xml`; `uv run --frozen --extra dev wgp release verify`; `git diff --check`; and protected-file parity against the recorded base.

## Delivery Requirements
- Paste operator decisions, current-head plan/graph identity, ffmpeg command and output tails, source/intermediate/final hashes, ffprobe summaries, measurement matrices, deterministic replay result, typed refusals, face-input evidence, checker result, matrix transition, lint/JUnit/release/parity outputs, and bundle size.
- If local-ffmpeg authorization or terminal-disposition approval is absent, record only that blocker and leave all five cells planned.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored on 2026-09-26 from the current five planned finishing cells, accepted WD-r4n8 corrected graph, WD-r81u immutable source/boundary evidence, and current `FaceTrack` validation contract.

### proof
- [ ] Pending explicit local-ffmpeg authorization and operator-approved terminal dispositions.

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence (structural normalization)

### CI/Test Results
Commands run:
- uv run --frozen --extra dev pytest -q tests/test_finishing_capabilities.py tests/test_maestro_parity_evidence.py tests/test_no_maestro_verbatim.py --junitxml=/tmp/WD-obkn-scoped.xml
- uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-obkn-full.xml
- uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-obkn-full-clean.xml
- uv run --frozen python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-obkn
- pvg lint --backlog
- uv run --frozen --extra dev wgp release verify
- pvg verify docs/finishing-capabilities.md datasets/runs/maestro-parity/WD-obkn/operator-decisions.md datasets/runs/maestro-parity/WD-obkn/terminal-boundaries.md datasets/runs/maestro-parity/WD-obkn/analyze_film_grain.py --format=text
- git diff --check
- git diff --exit-code 2b4714bf45d8f9e9cccf4c5796ac21afa501ea5a -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py
- git push -u origin story/WD-obkn
- git ls-remote origin refs/heads/story/WD-obkn
- pvg story deliver WD-obkn

Summary: checker PASS with owned_warnings=0; scoped pytest 136/136 PASS; backlog lint 139 scanned with 0 errors and 0 review findings; release=ready and tag_created=false; pvg verify PASS; diff and protected-file parity PASS. Pre-commit full JUnit was 2108 tests, 2 expected dirty-tree release failures, 0 errors, 1 skipped. Clean-tree full retry was dispatcher-stopped at 47% during the concurrent LF004 launcher hang and is NOT claimed as a pass. Bundle size is 26,612 KiB. Coverage: not_applicable; no production runtime control flow changed and no instrumented percentage is claimed.

### Commit
SHA: 2d778cef293ef3c5a441a35e15d89d715999e10d
Branch: story/WD-obkn
Remote: origin/story/WD-obkn at the same SHA.

LEARNINGS:
- Keep the canonical literal CI/Test Results, Commands run, Summary, and SHA labels expected by pvg verify-delivery.
- The honest full-suite boundary remains explicit: no clean full pass is fabricated after dispatcher termination at 47%.

## nd_contract
status: delivered

### evidence
- Pushed SHA 2d778cef293ef3c5a441a35e15d89d715999e10d; canonical checker/scoped suite/lint/release/diff/protected/pvg verify PASS; full clean-suite boundary recorded honestly.

### proof
- [x] Structural delivery proof contains commands, summaries, commit SHA, and LEARNINGS.
- [ ] Clean full-suite completion remains concurrency-blocked and is not claimed.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-26.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED at parent direction)

PROOF:

### Commit
- Branch: `story/WD-obkn`
- Local and pushed SHA: `2d778cef293ef3c5a441a35e15d89d715999e10d`
- Push: `git push -u origin story/WD-obkn`
- Remote byte check: `git ls-remote origin refs/heads/story/WD-obkn` returned `2d778cef293ef3c5a441a35e15d89d715999e10d`.
- Worktree after push: clean and tracking `origin/story/WD-obkn`.

### Operator decisions and current-head plan
- Operator authorization and four terminal dispositions were recorded before media execution in `datasets/runs/maestro-parity/WD-obkn/operator-decisions.md`.
- Request: `datasets/runs/maestro-parity/WD-obkn/request.json`.
- Command: `uv run --frozen wgp finish plan --request datasets/runs/maestro-parity/WD-obkn/request.json --dry-run --json > datasets/runs/maestro-parity/WD-obkn/current-head-plan.json`.
- Plan identity: `command_graph_sha256=0db6e426d6b96edf504131b657acac06d254c4540397a10dad3d4d18266d7722`; seed `8108`; source SHA-256 `e8b690774b0df7a73c85505ea507277d2745641b34f68c60c24855882da88859`.
- Current graph is unchanged at `services/finishing/pipeline.py:187-211`: ceil/downsample by 16, seeded `allf=u` and `allf=t+u`, `all_opacity=0.5`, nearest-neighbor x16, crop `480x832`, addition to `[0:v]`.

### FFmpeg execution and hashes
Commands represented by exact argv/cwd/exit/stream hashes in `primary-execution.json` and `replay-execution.json`:
- Planned probe: exit 0.
- Corrected lossless grain stage: exit 0; tail `frame=56 ... Lsize=7422KiB time=00:00:02.33 ... speed=3.74x`.
- Planned H.264 codec stage: exit 0; tail `frame=56 ... Lsize=542KiB time=00:00:02.25 ... speed=3.02x`.
- Source hash before and after: `e8b690774b0df7a73c85505ea507277d2745641b34f68c60c24855882da88859`; decoded source hash also matched before/after.
- Primary/replay lossless FFV1 SHA-256: `856a5f7af12f285e54a79a22cc04011687fceda1ef55ca3d4cfdc50f60619336` (byte-identical).
- Primary/replay final H.264 SHA-256: `5d3dfc20deb5d2879d677b7a4af327b417d9a32ea23629afc92491b6994adaff` (byte-identical).
- FFprobe: source, FFV1, and H.264 are all 480x832, 24 fps, 2.333333 s, 56 frames, `yuv420p`; final retains AAC 32 kHz stereo. Summaries are in `ffprobe-summary.json`.
- Command: `python3 datasets/runs/maestro-parity/WD-obkn/analyze_film_grain.py`.

### Pixel measurement
- Verdict: PASS (`measurement-results.json`; matrices in `measurement-matrices.npz`).
- Horizontal support: `15.735622357819338` px; vertical support: `15.143568751741263` px; both within pre-registered `[15,17]`.
- Lag-16 correlations: horizontal `-0.016801219307941165`, vertical `-0.056554122895396824`; both within absolute tolerance `0.10`.
- Persistence statistic: `0.4924941396514256`; different-phase median `-0.005015892705023033`.
- Strength proxy: p99 absolute block residual `9.682057291666675`, maximum `16`; tolerances `[8,14]` and `<=24`.
- Analyzer inputs, exact algorithm parameters, matrices, all 56-frame decoded hashes, and artifact hashes are retained.

### Terminal boundaries
- Neural interpolation and spatial upscale commands both returned exit 2 with only `FINISH_NEURAL_PATH_UNAVAILABLE`; no expected output file exists (`neural-boundaries.json`).
- Zero-hit named-implementation evidence is copied and hashed at `inputs/neural-frame-gen-boundary-probe.txt`; H3 face refinement remains a different backend.
- Face record: `face-input-boundary.json` proves the reviewed frame has no human face and all 12 mandatory `FaceTrack` fields are absent; no synthetic detector/identity/license/consent was created.
- Boundary interpretation: `terminal-boundaries.md:1-15`.

### Matrix transition and checker
- Command: `python3 /tmp/wd_obkn_matrix_check.py`.
- Result: exactly 5 intended cell changes, all other matrix cells unchanged (`matrix-transition-check.json`).
- Command: `uv run --frozen python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-obkn`.
- Result at pushed commit: `PASS wangp-dspy.maestro-parity-evidence/v1 datasets/runs/maestro-parity/WD-obkn owned_warnings=0`.
- Bundle size: `26,612 KiB`, below 512 MiB; no model weights.

### CI/Test and gate results
- Commands run:
  - `uv run --frozen --extra dev pytest -q tests/test_finishing_capabilities.py tests/test_maestro_parity_evidence.py tests/test_no_maestro_verbatim.py --junitxml=/tmp/WD-obkn-scoped.xml`
  - `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-obkn-full.xml`
  - Clean-tree retry: `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-obkn-full-clean.xml`
  - `pvg lint --backlog`
  - `uv run --frozen --extra dev wgp release verify`
  - `pvg verify docs/finishing-capabilities.md datasets/runs/maestro-parity/WD-obkn/operator-decisions.md datasets/runs/maestro-parity/WD-obkn/terminal-boundaries.md datasets/runs/maestro-parity/WD-obkn/analyze_film_grain.py --format=text`
  - `git diff --check`
  - `git diff --exit-code 2b4714bf45d8f9e9cccf4c5796ac21afa501ea5a -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
- Summary:
  - Scoped suite PASS: 136 tests, 0 failures, 0 errors, 0 skipped.
  - Pre-commit full suite: 2,108 tests, 2 failures, 0 errors, 1 skipped. Both failures were the release tests that deliberately require a clean repository; the evidence was uncommitted at that moment. After commit, `wgp release verify` passed `release=ready`, `tag_created=false`.
  - Clean full-suite retry did NOT complete. It reached 47%, then dispatcher directed termination of only WD-obkn PIDs 99411/99130/73854 after the LF004 launcher test hung concurrently with another full suite. Exit 143; no clean full-suite pass or JUnit is claimed.
  - Backlog lint PASS: 139 scanned, 0 errors, 0 review findings.
  - Release PASS: version/changelog/recipe schema/tree all pass; `release=ready`, `tag_created=false`.
  - pvg verify PASS: 0 issues.
  - `git diff --check` exit 0.
  - Protected-file parity from base `2b4714bf` exit 0.
- Coverage: not_applicable at delivery; no production runtime control flow was changed. No instrumented coverage percentage was claimed.

### AC Verification
| AC # | Requirement | Code/Evidence Location | Test/Check Location | Status |
|---|---|---|---|---|
| 1 | Pre-execution operator approval and terminal decisions | `operator-decisions.md` | Plan/execution timestamps and `current-head-plan.json` | PASS |
| 2 | Current-head request/graph controls and seed | `request.json`; `services/finishing/pipeline.py:187-211` | `current-head-plan.json` graph/hash | PASS |
| 3 | Local stages, immutable source, hashes, metadata, decoded evidence | `primary-execution.json` | `ffprobe-summary.json`, frame hashes | PASS |
| 4 | Pixel-derived size/strength/persistence measurement | `analyze_film_grain.py:73-180` | `measurement-results.json`, matrices | PASS |
| 5 | Same-build deterministic replay and measured codec bytes | `replay-execution.json` | identical FFV1/H.264 hashes | PASS |
| 6 | Neural interpolation/spatial unsupported host boundary | `terminal-boundaries.md:3-7` | typed exit-2 probes in `neural-boundaries.json` | PASS |
| 7 | Face cells missing all required inputs | `terminal-boundaries.md:9-11` | `face-input-boundary.json` | PASS |
| 8 | Exactly five matrix cells transition | `docs/finishing-capabilities.md:19-25,44-46` | `matrix-transition-check.json` | PASS |
| 9 | No prohibited process/change; protected files unchanged | execution records | protected parity exit 0 | PASS |
| 10 | Checker plus all full gates | `evidence.json`; gate logs | checker/lint/release/diff/protected PASS | PARTIAL: clean full-suite completion is not claimed because dispatcher stopped the concurrent-hang attempt at 47% |

LEARNINGS:
- Record approval and exact command boundaries inside the story worktree before invoking the planner or media process; the planner correctly fail-closed when the first patched approval file landed outside the worktree.
- Commit completed evidence before long clean-tree verification so release tree checks do not misclassify intentional evidence as a dirty release.
- Pixel autocorrelation plus retained matrices is a compact way to prove grain support without committing 64 MiB of decoded raw frames.
- Concurrent full-suite runs can reproduce a >30-minute LF004 launcher heredoc hang; do not claim or retry a full pass until that boundary is isolated.
- The honest terminal labels distinguish missing named implementation or missing required inputs from hardware infeasibility.

### DISCOVERED_BUG
  title: Concurrent full suites can hang LF004 launcher setup test
  context: On clean WD-obkn at 2d778cef, full pytest reached 47% and stayed in test_launcher_setup_is_root_relative_from_foreign_cwd. WD-obkn PIDs 73854/99130/99411 were blocked; sample showed nested bash in heredoc_write -> write. A concurrent WD-7fvx full suite had analogous stuck launcher processes. Dispatcher directed stopping only WD-obkn, which exited 143.
  affected_files: tests/test_lf004_recovery_tooling.py, datasets/content_briefs/lf004-operator-dogfood-56f/run/run_recovery_once.sh
  discovered_during: WD-obkn

### DISCOVERED_BUG
  title: Full suite emits StarletteDeprecationWarning
  context: Pre-commit full pytest emitted `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated, install httpx2 instead` from fastapi/testclient.py. This is outside WD-obkn and no dependency change was authorized.
  affected_files: tests using FastAPI TestClient; project dependency constraints
  discovered_during: WD-obkn

## nd_contract
status: delivered

### evidence
- Pushed commit `2d778cef293ef3c5a441a35e15d89d715999e10d`; checker PASS; scoped tests, lint, release, pvg verify, diff, and protected parity PASS; execution/measurement/boundary artifacts under `datasets/runs/maestro-parity/WD-obkn/`.

### proof
- [x] AC #1: operator approval recorded before execution
- [x] AC #2: current-head request/graph controls recorded
- [x] AC #3: local media execution and hashes recorded
- [x] AC #4: deterministic pixel measurement retained
- [x] AC #5: FFV1 and H.264 replay bytes matched
- [x] AC #6: neural cells terminalized by typed host boundary
- [x] AC #7: face cells terminalized by missing inputs
- [x] AC #8: exactly five intended matrix cells changed
- [x] AC #9: no prohibited action and protected files unchanged
- [ ] AC #10: clean full-suite completion remains concurrency-blocked; no full pass is fabricated


## Clean full-suite concurrent-hang boundary (interim)

- Clean-tree commit: 2d778cef293ef3c5a441a35e15d89d715999e10d.
- Attempt: uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-obkn-full-clean.xml.
- Progress: reached 47%; then tests/test_lf004_recovery_tooling.py::test_launcher_setup_is_root_relative_from_foreign_cwd did not return.
- Exact owned tree: pytest PID 73854; launcher bash PID 99130; nested bash PID 99411.
- Stack evidence: macOS sample of PID 99411 showed reader_loop -> execute_command_internal -> execute_simple_command -> execute_disk_command -> do_redirections -> heredoc_write -> write for effectively the entire one-second sample.
- Concurrent boundary: a separate WD-7fvx full suite simultaneously had the same launcher test blocked in analogous nested bash processes. This suggests a concurrent full-suite interaction and is not claimed as a WD-obkn code failure or a full-suite pass.
- Parent-directed termination: sent SIGTERM only to WD-obkn PIDs 99411, 99130, and 73854 after >30 minutes; WD-7fvx processes were not touched. The terminated attempt ended 143 at 47%; no clean full-suite pass is claimed.
- Awaiting explicit parent signal before any full-suite retry.

## History
- 2026-09-26T20:53:46Z dep_added: blocks WD-fay0
- 2026-09-26T20:53:47Z dep_added: blocked_by WD-r81u
- 2026-09-26T20:53:48Z dep_added: blocked_by WD-r4n8
- 2026-09-26T20:57:49Z status: open -> in_progress
- 2026-09-26T20:57:49Z auto-follows: linked to predecessor WD-5k28
- 2026-09-26T20:57:49Z claimed by dev-WD-obkn
- 2026-09-26T23:31:13Z status: in_progress -> in_progress
- 2026-09-26T23:31:13Z auto-follows: linked to predecessor WD-m7xw

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Blocked by: [[WD-r81u]], [[WD-r4n8]]
- Follows: [[WD-5k28]], [[WD-m7xw]]

## Comments
