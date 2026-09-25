---
id: WD-dmf2
title: "Director composition evidence"
status: open
priority: 2
type: feature
labels: [capability, evidence, external-integration]
parent: WD-3nod
created_at: 2026-09-24T14:14:07Z
created_by: speed
updated_at: 2026-09-24T15:48:06Z
content_hash: "sha256:eca0483c771fa1b4500e004f05f9fa9302b3fd70292c0be0792b6acc6d6348a3"
blocked_by: [WD-2gyw, WD-bxhc, WD-r81u]
blocks: [WD-fay0]
was_blocked_by: [WD-rous]
---

## Description
## USER INTENT
The first nine capability rows in `docs/director-capabilities.md` must reach evidence-backed terminal dispositions across every applicable Prompt, Audio/music-video, and Screenplay cell: deterministic ordered multi-clip plan; per-clip prompt and six-frame overlap; explicit continuity state and transitions; beat-aware measured window mapping; exact/window pacing preservation; auto/manual review checkpoints; immutable non-executable queue records; authorized prompt-only enhancement; and seed-based hash reconstruction. The pre-existing “Generated clip, audio, or finished film” row remains unsupported in this planning lane unless separately authorized and evidenced.

Director evidence requires a completed produced piece, not a composition document. Work is grouped by source mode — Prompt, Audio/music-video, and Screenplay — so progress can be checkpointed independently. Each applicable cell flips to `host_run_verified` only from a real authorized bundle under `datasets/runs/maestro-parity/WD-dmf2/` showing the planned-to-produced relationship. A cell becomes `unsupported_on_this_hardware` only with recorded infeasibility evidence.

Every bundle must preserve the exact relationship from canonical director request and immutable plan record to real queue attempts and produced output: request/plan hashes, record IDs, derived prompts and clip IDs, seeds, recipe and enhancement identity, every upstream source/output hash, every queue submission/admission/retry/exit result, every produced clip and final assembly hash, measured duration/media metadata, mandatory QC gates, and reviewer decision. Pacing and continuity claims require those recorded values plus objective measured evidence, not prose.

## REQUIRED OPERATOR INPUTS — NOT YET PROVIDED
- Per-composition and per-batch GPU/render-host authorization has NOT been given by this story.
- Model-download approval for every downstream model used by the completed piece has NOT been given by this story; upstream lane authorization cannot be inferred or reused without its exact recorded scope.
- Source material and rights for prompt, audio/music-video, screenplay, characters, references, and voices have NOT been supplied.
- Reviewer identity and required checkpoint decision are required for manual review and have NOT been supplied.
- The bundle must record authorization verbatim, including scope, timestamp, approver, exact command boundary, host identity, model/download approvals, source/rights boundary, and failure/stop boundary. Missing input is blocked, not infeasibility.

## No-Fabrication Rule
Director requests, composition documents, deterministic plans, immutable `director_plan_records`, queue snapshots that select no job, enhancement records, reconstruction output, recipe hashes, review policy, unit tests, dry-runs, prose pacing/continuity claims, and upstream artifacts without a produced completed piece are never generation evidence. `host_run_verified` requires actual produced clip/audio/assembly bytes from authorized queue attempts. `unsupported_on_this_hardware` requires an authorized captured refusal/failed attempt or a recorded model/output requirement that provably exceeds the render host; missing authorization, a missing upstream lane, a planning rejection, or a queue not admitted never qualifies.

## OUT OF SCOPE
- A GUI, new director engine, new pacing mode, new review gate, or registry publication.
- Capabilities outside the first nine named rows, including the existing “Generated clip, audio, or finished film” planning-unsupported row.
- Presenting a plan, composition document, or queue-planning database as generation evidence.
- Reusing a lane output as WD-dmf2 output; upstream artifacts may be hash-bound inputs only.
- Bypassing Whisper transcript, identity-vision, mouth-box consensus, SyncNet, assembly, provenance, review, or queue gates.
- Changing queue admission, renderer policy, wiring, preflight, or `scripts/run_film.py` semantics.

## DIFF BUDGET
- Authored text is about 3 files and under 350 changed LOC: `docs/director-capabilities.md`, optional matrix/evidence parsing test, and manifests/diagnostics under `datasets/runs/maestro-parity/WD-dmf2/`.
- Generated evidence is bounded to the shortest completed piece required per applicable source mode/capability, its hash-bound upstream inputs, logs, measurements, and review records; no model weights are committed. Record aggregate bundle size and keep it under 6 GiB unless recorded authorized-failure diagnostics are larger.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-dmf2/ -> `wangp-dspy.maestro-parity-evidence/v1` director composition bundles
  spec: checker-valid completed-piece sub-bundles grouped by source mode, with authorization, argv, commit, canonical request/plan/enhancement identities, upstream provenance, queue attempts, planned-versus-produced clip map, output hashes, measured duration/media metadata, mandatory gates, infeasibility evidence where applicable, and reviewer verdict.
- docs/director-capabilities.md -> evidence-backed terminal rows for the nine named capabilities
  event: update exactly those rows and applicable mode cells from bundle contents, cite each bundle record, and preserve the distinct generated-media planning-unsupported row without new evidence.

CONSUMES:
- WD-2gyw: datasets/runs/maestro-parity/WD-2gyw/ -> checker-valid verified video artifacts and provenance
  source: exact video clip hashes, model/reference rights, recipe linkage, and queue history available as director inputs.
- WD-rous: datasets/runs/maestro-parity/WD-rous/ -> checker-valid verified music/audio artifacts and provenance
  source: exact audio hashes, style/reference rights, measured metadata, and queue history available as director inputs.
- WD-bxhc: datasets/runs/maestro-parity/WD-bxhc/ -> checker-valid speech and portable-character artifacts/provenance
  source: exact speech/package hashes, character identity anchor, reference/consent rights, and queue history available as director inputs.
- WD-r81u: datasets/runs/maestro-parity/WD-r81u/ -> checker-valid finished-media bundles
  source: exact before/after hashes and finishing parameters available when the produced piece includes a finished stage.
- WD-651z: docs/maestro-parity-evidence-contract.md -> `wangp-dspy.maestro-parity-evidence/v1`
  source: sole canonical authorization, provenance, hash, metadata, gate, disposition, and reviewer contract; this lane must not duplicate or weaken it.
- WD-651z: scripts/verify_maestro_parity.py -> `verify_bundle(bundle: Path) -> VerificationReport`
  event: the accepted checker must exit zero for every director bundle and contract-defined unsupported-hardware disposition used to flip the matrix.
- (existing): docs/director-capabilities.md -> current nine-row director matrix and source/pacing/review contract
  source: exact mode/cell identities, measured-beat requirement, pacing windows, six-frame overlap, queue/enhancement/reconstruction semantics, and mandatory review gates.
- (operator): explicit per-composition authorization, model-download approval, source/rights inputs, and reviewer decision -> verbatim authorization and review record
  source: future operator input; not supplied by story creation.

## Story Acceptance Criteria
1. [State] Given explicit authorization, all required upstream inputs, and successful real queue attempts, a director cell flips to `host_run_verified` only when a completed piece's produced bytes, planned-versus-produced map, provenance, queue attempts, output hashes, metadata, mandatory gates, and reviewer decision are present in a bundle passing the accepted WD-651z checker.
2. [Unwanted] Given absent, blank, partial, mismatched, unauthorized, rights-invalid, or unreviewed input or evidence, the affected cell remains non-verified and is neither dropped nor silently flipped.
3. [State] Every bundle records the exact canonical director request hash, immutable plan record ID/hash, derived prompt and clip IDs, seeds, recipe/enhancement identity, upstream artifact hashes, queue/job/retry/exit identities, produced clip hashes, assembly hash, and reviewer checkpoint; the planned-versus-produced relationship is machine-checkable.
4. [State] Ordered multi-clip, six-frame overlap, continuity transition, measured beat mapping, and pacing-preservation claims cite the recorded plan values and matching measured output duration/window evidence; enhancement and reconstruction claims cite both original and enhanced/reconstructed hashes.
5. [Unwanted] A director plan, composition document, queue snapshot, reconstruction output, settings file, or prose continuity/pacing description is represented as `host_run_verified`; such evidence fails.
6. [State] A cell becomes `unsupported_on_this_hardware` only from an authorized captured refusal/failed attempt or a recorded model/output requirement that provably exceeds the measured host, with the proof checker-validated according to the accepted WD-651z disposition contract.
7. [State] Every currently planned cell in the first nine rows reaches a terminal evidence state; the existing generated-media unsupported row remains explicitly unchanged, and every flipped cell cites its exact bundle/evidence record.
8. [Unwanted] No GUI, publication, unauthorized download, extra row/cell, model-weight commit, rights bypass, gate bypass, or protected engine change occurs; `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py` remain unchanged from accepted base `40f8c2b373dec1c84ca5a596c821b740934af6fb`.

## Testing Requirements
- Before execution, record verbatim authorization/download approval and verify exact argv, commit, mode, canonical request, source/rights hashes, character and reference anchors, seeds, pacing policy, review mode, upstream bundle hashes, planned clip map, and queue targets.
- For every completed piece, retain each queue submission/admission/retry/exit result, every produced clip and final output SHA-256, measured duration/dimensions/fps/audio metadata, mandatory gate inputs/thresholds/measured values, and reviewer decision; a queue ID without produced bytes is insufficient.
- Prove planned-versus-produced alignment for every claimed capability: clip order/count, prompts, overlap, continuity states/transitions, beat/window/pacing values, enhancement delta, and reconstructed hashes.
- Invoke the accepted WD-651z checker on every complete bundle and require exit zero before a verified update. For hardware infeasibility, invoke its unsupported-evidence mode and retain the authorized failure or requirement arithmetic; if unavailable or failing, the cell remains unresolved.
- Parse the final matrix and prove the nine row identities, every applicable mode-cell transition, every queue/output citation, no dropped rows/cells, and no changed generated-media unsupported row without evidence.
- Standing gates: `pvg lint --backlog` reports 0 errors and 0 review findings; `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-dmf2-full.xml` has parsed JUnit `errors=0` and `failures=0`; `uv run --frozen --extra dev wgp release verify` reports `release=ready`/`tag_created=false`; and `git diff --exit-code 40f8c2b373dec1c84ca5a596c821b740934af6fb -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`.
- Also run `git diff --check`, record aggregate bundle size, and record every planned-versus-produced and matrix transition.

## Delivery Requirements
- Paste authorization and reviewer provenance without inventing approval, exact command tails, source/upstream/output hashes, queue attempts and exits, measured metadata, gate results, checker output, lint result, parsed JUnit counters, release fields, protected-file parity, bundle size, and the final nine-row matrix.
- If required operator input, rights, reviewer decision, or an upstream checker-valid artifact remains absent, report the affected mode as blocked on that input; do not substitute plans, composition documents, dry-runs, or unsupported assertions for completed-piece evidence.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored on 2026-09-24 from the nine planned director capability rows and source-mode contract in `docs/director-capabilities.md:5-43`; operator authorization, downloads, source rights, and reviewer decisions remain outstanding.

### proof
- [ ] Pending implementation and explicit operator authorization.

## Acceptance Criteria


## Design


## Notes
## MANDATORY SKILLS
- pvg

Observable outcome: an explicitly authorized future run stores the composed director output, inputs, command, commit, and provenance under datasets/runs/maestro-parity/WD-dmf2/; no GPU batch is authorized by this story and no composition result is claimed without that bundle.

## History
- 2026-09-24T14:14:07Z dep_added: blocked_by WD-2gyw
- 2026-09-24T14:14:07Z dep_added: blocked_by WD-rous
- 2026-09-24T14:14:07Z dep_added: blocked_by WD-bxhc
- 2026-09-24T14:14:07Z dep_added: blocked_by WD-r81u
- 2026-09-24T14:14:08Z dep_added: blocks WD-651z
- 2026-09-24T14:14:10Z dep_added: blocks WD-fay0
- 2026-09-24T14:39:54Z dep_removed: no_longer_blocks WD-651z
- 2026-09-25T05:04:03Z dep_removed: was_blocked_by WD-rous

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Blocked by: [[WD-2gyw]], [[WD-bxhc]], [[WD-r81u]]
- Was blocked by: [[WD-rous]]

## Comments
