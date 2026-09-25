---
id: WD-r81u
title: "Finishing generation evidence"
status: in_progress
priority: 2
type: feature
labels: [capability, evidence, external-integration, delivered]
parent: WD-3nod
created_at: 2026-09-24T14:14:06Z
created_by: speed
updated_at: 2026-09-25T19:27:14Z
content_hash: "sha256:e1611ead98ae82bba533c3e92c12d2fb5d896c77c88b6825750665da51e8f073"
blocks: [WD-dmf2, WD-fay0]
was_blocked_by: [WD-2gyw]
assignee: dev-WD-r81u
follows: [WD-2gyw, WD-cpow]
---

## Description
## USER INTENT
The five backend rows in `docs/finishing-capabilities.md` — `ffmpeg`, `rife`, `real_esrgan`, `film`, and `neural_frame_gen` — must reach evidence-backed terminal dispositions. The currently planned cells are ffmpeg interpolation/spatial upscale/film grain/face refinement, RIFE interpolation, Real-ESRGAN spatial upscale, film grain, and neural-frame-gen interpolation/spatial upscale/face refinement. Each ends as `host_run_verified` from a real authorized bundle under `datasets/runs/maestro-parity/WD-r81u/`, or as `unsupported_on_this_hardware` with recorded infeasibility evidence. Existing planning-unsupported off-diagonal cells remain unchanged and are not hardware verdicts.

Finishing parity is about transformed bytes, not configured intent. Every interpolation, spatial-upsampling, grain, codec, or tracked-face-refinement claim requires the immutable before artifact, actual after artifact, both SHA-256 hashes, the exact recorded parameters, measured before/after metadata, queue attempt, and objective comparison. A settings file or plan is never finishing evidence.

## REQUIRED OPERATOR INPUTS — NOT YET PROVIDED
- Per-batch GPU/render-host authorization has NOT been given by this story.
- Model-download approval for every model-backed backend (`rife`, `real_esrgan`, and `neural_frame_gen`) has NOT been given by this story.
- Complete model provenance — identity, immutable hash or version, source, license and explicit acceptance, parameter/asset size, quantization where applicable, and declared VRAM requirement — is required and has NOT been supplied.
- Tracked-face refinement additionally requires track provenance, temporal/geometric bounds, consent record, rights, and selected-track identity; none has been supplied.
- The bundle must record authorization verbatim, including scope, timestamp, approver, exact command boundary, render-host identity, model/download approval, source rights, and stop/failure boundary. Missing input is blocked, not infeasibility.

## No-Fabrication Rule
Documentation, requests, plans, normalized settings, command graphs, model manifests, deterministic databases, reconstruction output, unit tests, dry-runs, queue planning, filenames, prose such as “interpolated” or “upscaled”, and absence of an attempt are never finishing evidence. `host_run_verified` requires actual finished media bytes from an authorized run plus recorded before/after hashes and measured parameters. `unsupported_on_this_hardware` requires an authorized captured refusal/failed attempt or a recorded parameter/quantization/VRAM requirement that provably exceeds the render host; missing authorization, an absent model, a backend planning rejection, or an unrelated tool failure never qualifies.

## OUT OF SCOPE
- A GUI, registry publication, model training, new finishing backend, or new codec.
- Capabilities outside the five named rows or reuse of another lane's output as this lane's finished artifact.
- Changing source media, bypassing the immutable source contract, overwriting an input, or inventing consent for a tracked face.
- Replacing before/after measurements with planned `planned_ffprobe_unverified` values.
- Changing queue admission, renderer policy, wiring, preflight, or `scripts/run_film.py` semantics.

## DIFF BUDGET
- Authored text is about 2 files and under 300 changed LOC: `docs/finishing-capabilities.md` plus manifests/diagnostics under `datasets/runs/maestro-parity/WD-r81u/`.
- Generated evidence is bounded to one shortest useful source/output pair per planned cell plus required logs and metadata; no model weights are committed. Record aggregate bundle size and keep it under 4 GiB unless recorded authorized-failure diagnostics are larger.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-r81u/ -> `wangp-dspy.maestro-parity-evidence/v1` finishing bundles
  spec: one checker-valid sub-bundle per planned backend/cell, with authorization, argv, commit, immutable source and model provenance, queue attempt, before/after hashes, exact controls, measured before/after media metadata, objective gate, infeasibility evidence where applicable, and reviewer verdict.
- docs/finishing-capabilities.md -> evidence-backed terminal matrix rows
  event: update exactly the five named backend rows from bundle contents, cite each bundle record, and preserve planning-unsupported off-diagonal boundaries as non-hardware limitations.

CONSUMES:
- WD-2gyw: datasets/runs/maestro-parity/WD-2gyw/ -> checker-valid `host_run_verified` video artifact and provenance
  source: exact immutable source bytes, output hash, model/reference rights, and queue history used as finishing input; a video plan or foreign fixture never supplies this lane's source.
- WD-651z: docs/maestro-parity-evidence-contract.md -> `wangp-dspy.maestro-parity-evidence/v1`
  source: sole canonical authorization, provenance, hash, metadata, gate, disposition, and reviewer contract; this lane must not duplicate or weaken it.
- WD-651z: scripts/verify_maestro_parity.py -> `verify_bundle(bundle: Path) -> VerificationReport`
  event: the accepted checker must exit zero for every finishing bundle and every contract-defined unsupported-hardware disposition used to flip the matrix.
- (existing): docs/finishing-capabilities.md -> current five-row matrix and immutable source request contract
  source: exact backend/cell identities, interpolation and scale factors, model-hash requirement, grain controls, tracked-face consent/bounds, codec graph, and planned-unsupported boundaries.
- (operator): explicit per-batch GPU authorization, model-download approval, model manifest, and face-track consent/rights -> verbatim authorization and rights record
  source: future operator input; not supplied by story creation.

## Story Acceptance Criteria
1. [State] Given a checker-valid WD-2gyw source, explicit authorization, required download approval, and a successful run, a finishing cell flips to `host_run_verified` only when actual before and after bytes, exact parameters, provenance, queue attempt, hashes, measured metadata, and objective comparison are present in a bundle passing the accepted WD-651z checker.
2. [Unwanted] Given absent, blank, partial, mismatched, unauthorized, or rights-invalid input or evidence, the affected cell remains non-verified and is neither dropped nor silently flipped.
3. [State] An interpolation claim records source/output frame rate and frame/duration accounting for the declared x2/x3/x4 factor; a spatial-upscale claim records before/after dimensions and scale factor; a grain claim records strength, size, temporal persistence, seed, and visual comparison; a codec claim records container/codec, pixel format, graph arguments, and stream metadata; and a face-refinement claim records track identity, bounds, consent, selected track, and identity-preservation gate.
4. [Unwanted] A settings file, deterministic plan, command graph, reconstruction result, filename, or prose effect description is represented as `host_run_verified`; such evidence fails.
5. [State] A cell becomes `unsupported_on_this_hardware` only from an authorized captured refusal/failed attempt or a recorded parameter/quantization/VRAM requirement that provably exceeds the measured host, with the proof checker-validated according to the accepted WD-651z disposition contract.
6. [State] All currently planned cells in the five named rows reach terminal evidence states; pre-existing planning-unsupported cells remain explicitly unchanged, and every flipped cell cites its exact bundle/evidence record.
7. [Unwanted] No GUI, publication, training, unauthorized download, extra row/cell, source overwrite, model-weight commit, rights bypass, or protected engine change occurs; `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py` remain unchanged from accepted base `40f8c2b373dec1c84ca5a596c821b740934af6fb`.

## Testing Requirements
- Before execution, record verbatim authorization/download approval and verify exact argv, commit, source hash and rights, backend, model identity/hash/license/requirement, factor, target fps, grain controls, codec graph, track bounds/consent, seeds, and output target.
- For every output, retain immutable source and output SHA-256 plus measured before/after ffprobe dimensions, duration, fps, stream layout, codec/pixel format, and applicable face-preservation gate inputs/thresholds/measured values; never copy a declared source value as an after measurement.
- Invoke the accepted WD-651z checker on every complete bundle and require exit zero before a verified update. For hardware infeasibility, invoke its unsupported-evidence mode and retain the authorized failure or requirement arithmetic; if that mode is unavailable or fails, the cell remains unresolved.
- Parse the final matrix and prove all five row identities, every planned-cell transition, every before/after citation, no dropped cells, and unchanged planning-unsupported boundaries.
- Standing gates: `pvg lint --backlog` reports 0 errors and 0 review findings; `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-r81u-full.xml` has parsed JUnit `errors=0` and `failures=0`; `uv run --frozen --extra dev wgp release verify` reports `release=ready`/`tag_created=false`; and `git diff --exit-code 40f8c2b373dec1c84ca5a596c821b740934af6fb -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`.
- Also run `git diff --check`, record aggregate bundle size, and record every parameter and before/after transition.

## Delivery Requirements
- Paste authorization provenance without inventing approval, exact command tails, model requirements, source/output hashes, measured before/after metadata, gate results, checker output, lint result, parsed JUnit counters, release fields, protected-file parity, bundle size, and the final five-row matrix.
- If required operator input or a checker-valid WD-2gyw source remains absent, report the lane as blocked on that input; do not substitute plans, settings, fixtures, or unsupported assertions for finishing evidence.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored on 2026-09-24 from the five planned backend rows in `docs/finishing-capabilities.md:13-42`; operator GPU/download approvals, model provenance, and face-track consent remain outstanding.

### proof
- [ ] Pending implementation and explicit operator authorization.

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence (DELIVERED)

PROOF:

### Authorization and host batch
- Commands: `pvg nd show WD-r81u`; SSH host inventory; `wgp doctor --capabilities --models datasets/runs/maestro-parity/WD-r81u/model-download-manifest.json --json`; `wgp first-run download ... --resume rife-v4.26-model`; final synchronous `timeout 3600 ssh ... timeout 3500 /home/straughter/Wan2GP/wd-r81u/host-scripts/wd_r81u_run.sh`.
- Authorization is verbatim in `operator-authorization.md`. Planned and actual network transfer: 71,567,775 bytes (RIFE 24,636,301 + Real-ESRGAN portable archive 46,931,474) under the 20,000,000,000-byte ceiling.
- Derived disk floor: 16.067 GiB = 0.067 GiB transfer + 1.0 GiB bounded working set + 15 GiB safety floor. Measured host free bytes: 41,534,517,248 before download and 41,012,895,744 after final host contact.
- GPU discipline: llama-server PID 2591141 remained running; final host state records it as the only GPU process. An unrelated vb7-venv process briefly visible after one run was not started or stopped by this lane.

### Artifacts and measurements
- Native exit: 0. Seven hashed MP4 outputs and immutable source SHA-256 `e8b690774b0df7a73c85505ea507277d2745641b34f68c60c24855882da88859` are recorded in `output-hashes.txt`, `media-qc.json`, and `evidence.json`.
- Executed: FFmpeg interpolation/spatial/grain/codec, WanGP RIFE v4.26 CUDA x2, WanGP film grain, and Real-ESRGAN NCNN x4plus x2. All 29 objective gates pass in `objective-gates.json`.
- Queue: `job-1790361058753-0d9a6130`, attempt-1, admitted through done.
- Bundle: 135 files, 18,242,490 bytes at final analysis.

### CI/test results
- Commands run:
  - `pvg lint --backlog`
  - `timeout 1800 uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-r81u-full.xml`
  - `timeout 300 uv run --frozen --extra dev wgp release verify`
  - `git diff --exit-code c91a6d8 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
  - `git diff --check`
  - `uv run --frozen python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-r81u`
  - `pvg verify <all story-changed files> --format=text`
- Summary: lint PASS (126 scanned, 0 errors, 0 review findings); full suite PASS (2085 tests, 0 failures, 0 errors, 1 pre-existing skip, 832.196 s); release ready/tag_created=false; protected parity PASS; diff-check PASS; pvg verify PASS (8 files, 0 issues).
- Canonical checker: expected delivery-time FAIL, exit 1, only `reviewer_verdict.decision: must be approved`. Reviewer remains pending and no row is flipped, as instructed.

### Commit
- Native-producing clean commit: `13f352f776b211fe8dfd552ff0752d75c7469b82`
- Delivered branch HEAD: `c1a7efd7a512652f9f414743a47081f6bb9ee72e`
- Branch: `story/WD-r81u`, pushed to origin.

### AC Verification
| AC | Requirement | Evidence Location | Status |
|---|---|---|---|
| 1 | Checker-valid flip | `evidence.json`, `checker-result.txt`, `matrix-transition-check.json` | PARTIAL: seven real candidate outputs; no flip while reviewer/checker is pending |
| 2 | Invalid evidence stays non-verified | `missing-required-inputs.md`, unchanged matrix | PASS |
| 3 | Exact operation parameters/metadata | `execution-summary.md`, `media-qc.json`, ffprobe files | PASS for executed cells; face cells unresolved |
| 4 | Plans are not finishing evidence | `output-hashes.txt`, `media-qc.json` | PASS |
| 5 | No unsupported-without-proof | unchanged matrix, boundary probe | PASS |
| 6 | All planned cells terminal | `matrix-transition-check.json` | BLOCKED: face consent/source and named neural implementation remain absent |
| 7 | Prohibited changes absent | `protected-parity-c91a6d8.txt`, `git-diff-check.txt` | PASS |

LEARNINGS:
- Ubuntu FFmpeg 6.1.1 rejects FFV1 in MP4; Matroska staging is required while preserving the final MP4 graph.
- Image-sequence remuxes need explicit input `-framerate`; output-only `-r` stretches or drops frames.
- The Nix fetchzip SRI hash describes extracted output, not the portable ZIP bytes; exact archive bytes must be hashed directly.
- A reviewer-pending bundle intentionally fails the canonical checker; capability rows must remain unchanged until independent review.

### OBSERVATIONS (unrelated)
- [ISSUE] `.venv/lib/python3.14/site-packages/fastapi/testclient.py:1`: StarletteDeprecationWarning (`httpx` with `starlette.testclient` deprecated) appears in the full suite.
- [CONCERN] full suite contains one pre-existing skipped test despite 2085 executed/passing tests.

### DISCOVERED_BUG
  title: Finishing command graph emits FFV1 into an MP4 staging path
  context: On host FFmpeg 6.1.1, the planned FFV1 intermediate command fails with `Could not find tag for codec ffv1` when its destination ends in `.mp4`. The deterministic tests do not execute the graph, so this host incompatibility was not caught.
  affected_files: services/finishing/pipeline.py
  discovered_during: WD-r81u

### DISCOVERED_BUG
  title: Planned film-grain size and temporal persistence are not execution controls
  context: The typed request records bounded size/persistence values, but the command graph emits only `noise=alls=...:allf=t+u` and WanGP's `add_film_grain` emits per-pixel independent noise. Measured actual controls are size 1 and temporal persistence 0, so the planned 16/0.5 values are not implemented.
  affected_files: services/finishing/pipeline.py; postprocessing/film_grain.py
  discovered_during: WD-r81u

### DISCOVERED_BUG
  title: neural_frame_gen has no native executable backend
  context: The no-GPU graph labels FFmpeg/RIFE/Real-ESRGAN-shaped commands with backend `neural_frame_gen`, while a host search finds no named implementation. Reusing another backend would fabricate the row identity.
  affected_files: services/finishing/pipeline.py; docs/finishing-capabilities.md
  discovered_during: WD-r81u

## nd_contract
status: delivered

### evidence
- Branch `story/WD-r81u` pushed at `c1a7efd7a512652f9f414743a47081f6bb9ee72e`.
- Real outputs, hashes, measurements, queue, authorization, diagnostics, and gates are under `datasets/runs/maestro-parity/WD-r81u/`.
- Native-producing commit: `13f352f776b211fe8dfd552ff0752d75c7469b82`; final native exit 0.

### proof
- [x] Seven real finishing artifacts are hash-bound with measured before/after metadata and 29 passing objective gates.
- [x] Authorization/download ceiling, 71,567,775 bytes pulled, disk floor, and final host state are recorded.
- [x] Lint 0/0; JUnit 2085/0 failures/0 errors; release ready/tag false; protected parity and diff-check pass.
- [x] Reviewer remains pending; canonical checker fails only that required approval; matrix flips are zero.
- [ ] Face-track consent/rights and a source face are absent, so face-refinement cells remain unresolved.
- [ ] No named `neural_frame_gen` host implementation exists, so its interpolation/spatial/face cells remain unresolved.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-25.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

PROOF:

### Authorization and host batch
- Commands: `pvg nd show WD-r81u`; SSH host inventory; `wgp doctor --capabilities --models datasets/runs/maestro-parity/WD-r81u/model-download-manifest.json --json`; `wgp first-run download ... --resume rife-v4.26-model`; final synchronous `timeout 3600 ssh ... timeout 3500 /home/straughter/Wan2GP/wd-r81u/host-scripts/wd_r81u_run.sh`.
- Authorization is verbatim in `operator-authorization.md`. Planned and actual network transfer: 71,567,775 bytes (RIFE 24,636,301 + Real-ESRGAN portable archive 46,931,474) under the 20,000,000,000-byte ceiling.
- Derived disk floor: 16.067 GiB = 0.067 GiB transfer + 1.0 GiB bounded working set + 15 GiB safety floor. Measured host free bytes: 41,534,517,248 before download and 41,012,895,744 after final host contact.
- GPU discipline: llama-server PID 2591141 remained running; final host state records it as the only GPU process. An unrelated vb7-venv process briefly visible after one run was not started or stopped by this lane.

### Artifacts and measurements
- Native exit: 0. Seven hashed MP4 outputs and immutable source SHA-256 `e8b690774b0df7a73c85505ea507277d2745641b34f68c60c24855882da88859` are recorded in `output-hashes.txt`, `media-qc.json`, and `evidence.json`.
- Executed: FFmpeg interpolation/spatial/grain/codec, WanGP RIFE v4.26 CUDA x2, WanGP film grain, and Real-ESRGAN NCNN x4plus x2. All 29 objective gates pass in `objective-gates.json`.
- Queue: `job-1790361058753-0d9a6130`, attempt-1, admitted through done.
- Bundle: 135 files, 18,242,490 bytes at final analysis.

### CI/test results
- Commands run:
  - `pvg lint --backlog`
  - `timeout 1800 uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-r81u-full.xml`
  - `timeout 300 uv run --frozen --extra dev wgp release verify`
  - `git diff --exit-code c91a6d8 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
  - `git diff --check`
  - `uv run --frozen python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-r81u`
  - `pvg verify <all story-changed files> --format=text`
- Summary: lint PASS (126 scanned, 0 errors, 0 review findings); full suite PASS (2085 tests, 0 failures, 0 errors, 1 pre-existing skip, 832.196 s); release ready/tag_created=false; protected parity PASS; diff-check PASS; pvg verify PASS (8 files, 0 issues).
- Canonical checker: expected delivery-time FAIL, exit 1, only `reviewer_verdict.decision: must be approved`. Reviewer remains pending and no row is flipped, as instructed.

### Commit
- Native-producing clean commit: `13f352f776b211fe8dfd552ff0752d75c7469b82`
- Delivered branch HEAD: `c1a7efd7a512652f9f414743a47081f6bb9ee72e`
- Branch: `story/WD-r81u`, pushed to origin.

### AC Verification
| AC | Requirement | Evidence Location | Status |
|---|---|---|---|
| 1 | Checker-valid flip | `evidence.json`, `checker-result.txt`, `matrix-transition-check.json` | PARTIAL: seven real candidate outputs; no flip while reviewer/checker is pending |
| 2 | Invalid evidence stays non-verified | `missing-required-inputs.md`, unchanged matrix | PASS |
| 3 | Exact operation parameters/metadata | `execution-summary.md`, `media-qc.json`, ffprobe files | PASS for executed cells; face cells unresolved |
| 4 | Plans are not finishing evidence | `output-hashes.txt`, `media-qc.json` | PASS |
| 5 | No unsupported-without-proof | unchanged matrix, boundary probe | PASS |
| 6 | All planned cells terminal | `matrix-transition-check.json` | BLOCKED: face consent/source and named neural implementation remain absent |
| 7 | Prohibited changes absent | `protected-parity-c91a6d8.txt`, `git-diff-check.txt` | PASS |

LEARNINGS:
- Ubuntu FFmpeg 6.1.1 rejects FFV1 in MP4; Matroska staging is required while preserving the final MP4 graph.
- Image-sequence remuxes need explicit input `-framerate`; output-only `-r` stretches or drops frames.
- The Nix fetchzip SRI hash describes extracted output, not the portable ZIP bytes; exact archive bytes must be hashed directly.
- A reviewer-pending bundle intentionally fails the canonical checker; capability rows must remain unchanged until independent review.

### OBSERVATIONS (unrelated)
- [ISSUE] `.venv/lib/python3.14/site-packages/fastapi/testclient.py:1`: StarletteDeprecationWarning (`httpx` with `starlette.testclient` deprecated) appears in the full suite.
- [CONCERN] full suite contains one pre-existing skipped test despite 2085 executed/passing tests.

### DISCOVERED_BUG
  title: Finishing command graph emits FFV1 into an MP4 staging path
  context: On host FFmpeg 6.1.1, the planned FFV1 intermediate command fails with `Could not find tag for codec ffv1` when its destination ends in `.mp4`. The deterministic tests do not execute the graph, so this host incompatibility was not caught.
  affected_files: services/finishing/pipeline.py
  discovered_during: WD-r81u

### DISCOVERED_BUG
  title: Planned film-grain size and temporal persistence are not execution controls
  context: The typed request records bounded size/persistence values, but the command graph emits only `noise=alls=...:allf=t+u` and WanGP's `add_film_grain` emits per-pixel independent noise. Measured actual controls are size 1 and temporal persistence 0, so the planned 16/0.5 values are not implemented.
  affected_files: services/finishing/pipeline.py; postprocessing/film_grain.py
  discovered_during: WD-r81u

### DISCOVERED_BUG
  title: neural_frame_gen has no native executable backend
  context: The no-GPU graph labels FFmpeg/RIFE/Real-ESRGAN-shaped commands with backend `neural_frame_gen`, while a host search finds no named implementation. Reusing another backend would fabricate the row identity.
  affected_files: services/finishing/pipeline.py; docs/finishing-capabilities.md
  discovered_during: WD-r81u

## nd_contract
status: delivered

### evidence
- Branch `story/WD-r81u` pushed at `c1a7efd7a512652f9f414743a47081f6bb9ee72e`.
- Real outputs, hashes, measurements, queue, authorization, diagnostics, and gates are under `datasets/runs/maestro-parity/WD-r81u/`.
- Native-producing commit: `13f352f776b211fe8dfd552ff0752d75c7469b82`; final native exit 0.

### proof
- [x] Seven real finishing artifacts are hash-bound with measured before/after metadata and 29 passing objective gates.
- [x] Authorization/download ceiling, 71,567,775 bytes pulled, disk floor, and final host state are recorded.
- [x] Lint 0/0; JUnit 2085/0 failures/0 errors; release ready/tag false; protected parity and diff-check pass.
- [x] Reviewer remains pending; canonical checker fails only that required approval; matrix flips are zero.
- [ ] Face-track consent/rights and a source face are absent, so face-refinement cells remain unresolved.
- [ ] No named `neural_frame_gen` host implementation exists, so its interpolation/spatial/face cells remain unresolved.


## MANDATORY SKILLS
- pvg

Observable outcome: an explicitly authorized future run emits hashed finished-media artifacts and metadata under datasets/runs/maestro-parity/WD-r81u/; no GPU batch is authorized by this story and no finishing result is claimed without that bundle.

## History
- 2026-09-24T14:14:06Z dep_added: blocked_by WD-2gyw
- 2026-09-24T14:14:07Z dep_added: blocks WD-dmf2
- 2026-09-24T14:14:08Z dep_added: blocks WD-651z
- 2026-09-24T14:14:10Z dep_added: blocks WD-fay0
- 2026-09-24T14:39:54Z dep_removed: no_longer_blocks WD-651z
- 2026-09-25T18:11:21Z dep_removed: was_blocked_by WD-2gyw
- 2026-09-25T18:14:32Z status: open -> in_progress
- 2026-09-25T18:14:32Z auto-follows: linked to predecessor WD-2gyw
- 2026-09-25T18:14:32Z claimed by dev-WD-r81u
- 2026-09-25T19:25:09Z status: in_progress -> in_progress
- 2026-09-25T19:25:09Z auto-follows: linked to predecessor WD-cpow

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-dmf2]], [[WD-fay0]]
- Was blocked by: [[WD-2gyw]]
- Follows: [[WD-2gyw]], [[WD-cpow]]

## Comments

### 2026-09-25T19:27:14Z speed
## Implementation Evidence (DELIVERED)

PROOF:

### Authorization and host batch
- Commands: `pvg nd show WD-r81u`; SSH host inventory; `wgp doctor --capabilities --models datasets/runs/maestro-parity/WD-r81u/model-download-manifest.json --json`; `wgp first-run download ... --resume rife-v4.26-model`; final synchronous `timeout 3600 ssh ... timeout 3500 /home/straughter/Wan2GP/wd-r81u/host-scripts/wd_r81u_run.sh`.
- Authorization is verbatim in `operator-authorization.md`. Planned and actual network transfer: 71,567,775 bytes (RIFE 24,636,301 + Real-ESRGAN portable archive 46,931,474) under the 20,000,000,000-byte ceiling.
- Derived disk floor: 16.067 GiB = 0.067 GiB transfer + 1.0 GiB bounded working set + 15 GiB safety floor. Measured host free bytes: 41,534,517,248 before download and 41,012,895,744 after final host contact.
- GPU discipline: llama-server PID 2591141 remained running; final host state records it as the only GPU process. An unrelated vb7-venv process briefly visible after one run was not started or stopped by this lane.

### Artifacts and measurements
- Native exit: 0. Seven hashed MP4 outputs and immutable source SHA-256 `e8b690774b0df7a73c85505ea507277d2745641b34f68c60c24855882da88859` are recorded in `output-hashes.txt`, `media-qc.json`, and `evidence.json`.
- Executed: FFmpeg interpolation/spatial/grain/codec, WanGP RIFE v4.26 CUDA x2, WanGP film grain, and Real-ESRGAN NCNN x4plus x2. All 29 objective gates pass in `objective-gates.json`.
- Queue: `job-1790361058753-0d9a6130`, attempt-1, admitted through done.
- Bundle: 135 files, 18,242,490 bytes at final analysis.

### CI/test results
- Commands run:
  - `pvg lint --backlog`
  - `timeout 1800 uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-r81u-full.xml`
  - `timeout 300 uv run --frozen --extra dev wgp release verify`
  - `git diff --exit-code c91a6d8 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
  - `git diff --check`
  - `uv run --frozen python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-r81u`
  - `pvg verify <all story-changed files> --format=text`
- Summary: lint PASS (126 scanned, 0 errors, 0 review findings); full suite PASS (2085 tests, 0 failures, 0 errors, 1 pre-existing skip, 832.196 s); release ready/tag_created=false; protected parity PASS; diff-check PASS; pvg verify PASS (8 files, 0 issues).
- Canonical checker: expected delivery-time FAIL, exit 1, only `reviewer_verdict.decision: must be approved`. Reviewer remains pending and no row is flipped, as instructed.

### Commit
- Native-producing clean commit: `13f352f776b211fe8dfd552ff0752d75c7469b82`
- Delivered branch HEAD: `c1a7efd7a512652f9f414743a47081f6bb9ee72e`
- Branch: `story/WD-r81u`, pushed to origin.

### AC Verification
| AC | Requirement | Evidence Location | Status |
|---|---|---|---|
| 1 | Checker-valid flip | `evidence.json`, `checker-result.txt`, `matrix-transition-check.json` | PARTIAL: seven real candidate outputs; no flip while reviewer/checker is pending |
| 2 | Invalid evidence stays non-verified | `missing-required-inputs.md`, unchanged matrix | PASS |
| 3 | Exact operation parameters/metadata | `execution-summary.md`, `media-qc.json`, ffprobe files | PASS for executed cells; face cells unresolved |
| 4 | Plans are not finishing evidence | `output-hashes.txt`, `media-qc.json` | PASS |
| 5 | No unsupported-without-proof | unchanged matrix, boundary probe | PASS |
| 6 | All planned cells terminal | `matrix-transition-check.json` | BLOCKED: face consent/source and named neural implementation remain absent |
| 7 | Prohibited changes absent | `protected-parity-c91a6d8.txt`, `git-diff-check.txt` | PASS |

LEARNINGS:
- Ubuntu FFmpeg 6.1.1 rejects FFV1 in MP4; Matroska staging is required while preserving the final MP4 graph.
- Image-sequence remuxes need explicit input `-framerate`; output-only `-r` stretches or drops frames.
- The Nix fetchzip SRI hash describes extracted output, not the portable ZIP bytes; exact archive bytes must be hashed directly.
- A reviewer-pending bundle intentionally fails the canonical checker; capability rows must remain unchanged until independent review.

### OBSERVATIONS (unrelated)
- [ISSUE] `.venv/lib/python3.14/site-packages/fastapi/testclient.py:1`: StarletteDeprecationWarning (`httpx` with `starlette.testclient` deprecated) appears in the full suite.
- [CONCERN] full suite contains one pre-existing skipped test despite 2085 executed/passing tests.

### DISCOVERED_BUG
  title: Finishing command graph emits FFV1 into an MP4 staging path
  context: On host FFmpeg 6.1.1, the planned FFV1 intermediate command fails with `Could not find tag for codec ffv1` when its destination ends in `.mp4`. The deterministic tests do not execute the graph, so this host incompatibility was not caught.
  affected_files: services/finishing/pipeline.py
  discovered_during: WD-r81u

### DISCOVERED_BUG
  title: Planned film-grain size and temporal persistence are not execution controls
  context: The typed request records bounded size/persistence values, but the command graph emits only `noise=alls=...:allf=t+u` and WanGP's `add_film_grain` emits per-pixel independent noise. Measured actual controls are size 1 and temporal persistence 0, so the planned 16/0.5 values are not implemented.
  affected_files: services/finishing/pipeline.py; postprocessing/film_grain.py
  discovered_during: WD-r81u

### DISCOVERED_BUG
  title: neural_frame_gen has no native executable backend
  context: The no-GPU graph labels FFmpeg/RIFE/Real-ESRGAN-shaped commands with backend `neural_frame_gen`, while a host search finds no named implementation. Reusing another backend would fabricate the row identity.
  affected_files: services/finishing/pipeline.py; docs/finishing-capabilities.md
  discovered_during: WD-r81u

## nd_contract
status: delivered

### evidence
- Branch `story/WD-r81u` pushed at `c1a7efd7a512652f9f414743a47081f6bb9ee72e`.
- Real outputs, hashes, measurements, queue, authorization, diagnostics, and gates are under `datasets/runs/maestro-parity/WD-r81u/`.
- Native-producing commit: `13f352f776b211fe8dfd552ff0752d75c7469b82`; final native exit 0.

### proof
- [x] Seven real finishing artifacts are hash-bound with measured before/after metadata and 29 passing objective gates.
- [x] Authorization/download ceiling, 71,567,775 bytes pulled, disk floor, and final host state are recorded.
- [x] Lint 0/0; JUnit 2085/0 failures/0 errors; release ready/tag false; protected parity and diff-check pass.
- [x] Reviewer remains pending; canonical checker fails only that required approval; matrix flips are zero.
- [ ] Face-track consent/rights and a source face are absent, so face-refinement cells remain unresolved.
- [ ] No named `neural_frame_gen` host implementation exists, so its interpolation/spatial/face cells remain unresolved.

