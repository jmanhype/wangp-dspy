---
id: WD-r81u
title: "Finishing generation evidence"
status: in_progress
priority: 2
type: feature
labels: [capability, evidence, external-integration]
parent: WD-3nod
created_at: 2026-09-24T14:14:06Z
created_by: speed
updated_at: 2026-09-25T18:14:32Z
content_hash: "sha256:b777d5d96227e0ce32fc53a7710921ddd317f0a4520f623d5bcc0c73e2ad5b83"
blocks: [WD-dmf2, WD-fay0]
was_blocked_by: [WD-2gyw]
assignee: dev-WD-r81u
follows: [WD-2gyw]
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

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-dmf2]], [[WD-fay0]]
- Was blocked by: [[WD-2gyw]]
- Follows: [[WD-2gyw]]

## Comments
