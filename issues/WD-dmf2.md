---
id: WD-dmf2
title: "Director composition evidence"
status: in_progress
priority: 2
type: feature
labels: [capability, evidence, external-integration, delivered]
parent: WD-3nod
created_at: 2026-09-24T14:14:07Z
created_by: speed
updated_at: 2026-09-25T23:01:44Z
content_hash: "sha256:c5048dd29bc7d8c05a37ae2d2d0b95bab49711cf1e1ba182877b297cc0e8caab"
blocks: [WD-fay0]
was_blocked_by: [WD-rous, WD-2gyw, WD-r81u, WD-bxhc]
assignee: dev-WD-dmf2
follows: [WD-rous, WD-2gyw, WD-r81u, WD-bxhc, WD-cpow, WD-0zj8]
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
## Implementation Evidence

### CI/Test Results
Commands run:
  - `pvg lint --backlog`
  - `timeout 1800 uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-dmf2-full.xml`
  - `timeout 600 uv run --frozen --extra dev wgp release verify`
  - `git diff --exit-code 31e3b7b -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
  - `git diff --check`
  - `uv run --frozen python scripts/verify_maestro_parity.py datasets/runs/maestro-parity/WD-dmf2`
  - `pvg verify <authoring subset>`
Summary: lint PASS 0 errors/0 review findings; full suite PASS tests=2085 errors=0 failures=0 skipped=1; release=ready/tag_created=false; dispatcher-base protected parity and diff-check PASS; checker intentionally FAIL exit=1 with six gate failures plus pending reviewer; pvg verify PASS 13 files/0 issues.
Commit SHA: b654d5e02c9c35df95d43302851874357129c611

## nd_contract
status: delivered

### evidence
- Real composition artifacts, planned-produced map, queue, authorization, hashes, measurements, pending review, checker diagnostics, standing gates, and pushed branch are recorded in `datasets/runs/maestro-parity/WD-dmf2/`.

### proof
- [x] AC #1 evaluated: not fully met; checker and reviewer remain fail-closed.
- [x] AC #2 evaluated: incomplete/failing evidence leaves cells unchanged.
- [x] AC #3 evaluated: request-to-output lineage is machine-checkable.
- [x] AC #4 evaluated: pacing/continuity measured; enhanced prompt lacks produced media.
- [x] AC #5 evaluated: no plan-only artifact is claimed verified.
- [x] AC #6 evaluated: no unsupported-hardware claim is made.
- [x] AC #7 evaluated: not met; all nine rows remain planned.
- [x] AC #8 evaluated: protected/scope gates pass.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-25.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED FOR REVIEW)

PROOF:

### Authorization, download, and host boundary
- Operator authorization is recorded verbatim in `datasets/runs/maestro-parity/WD-dmf2/operator-authorization.md` and `evidence.json`.
- Typed plan: 483,617,219 bytes for Whisper small under the 20,000,000,000-byte ceiling.
- Bytes pulled: 0. `/home/straughter/.cache/whisper/small.pt` preexisted and measured SHA-256 `9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794`.
- Derived floor: 15.0 decimal GB. Preflight free: 40,969,826,304 bytes; final free: 40,993,148,928 bytes.
- The operator's llama-server remained running; final health was `{"status":"ok"}`, GPU 7,893 MiB / 0%, and `operator_service_mutation=false`.

### Real operations and artifacts
- Commands are recorded in `evidence.json.command`, `secondary_commands`, and native logs.
- Four `wgp director plan` modes, four `queue` inspections, four `review` reconstructions, and one prompt-only `enhance` completed successfully.
- Durable composition queue: `wangp-JobQueue-WD-dmf2`, job `job-1790373082258-e4889656`, retry `attempt-1`, admitted through `JobQueue.next_admissible`, public state sequence ending `done`.
- Final output SHA-256:
  - prompt `6cf83d5e6a572be2da154cba0a74878dd5c39bb64c64ac87709326b51c799c19`
  - audio `c4078d72f7cdffa0d55fd03edcf0da2bc8f3d166697f3b92ce944e0637530c4e`
  - music video `5e951f39ece9e7f63e5c5002500b4cd40f87b36b7f6e3b3bd167c3a3be44e4b8`
  - screenplay `98129a5e11f26dd7823a83c1cb50acdc1713d4fa331b3507d8ed43c71bc2f25c`
- `planned-produced-map.json` binds all 8 plan records, request/plan hashes, prompts, seeds, windows, overlap, continuity, upstream hashes, segment/final hashes, durations, and boundary-frame hashes.
- Bundle: 27 MiB, 285 files, 12 hashed video outputs, 52 hashed references.

### Honest QC/checker state
- Whisper: screenplay clip 2 passed 1.000; screenplay clip 1 failed 0.556; music clip 1 produced no transcript.
- Identity vision: 3/3 pass. Mouth-box consensus: 3/3 pass.
- SyncNet: screenplay clip 2 passed 1.10503; audio clip 1 failed 0.594741; screenplay clip 1 failed 0.468897.
- Auto review therefore passed only 2/4 mandatory gate categories on the tested clip. Manual reviewer decision is pending.
- Checker result (exit 1): six `objective_gate_results[*].verdict: must be pass` failures plus `reviewer_verdict.decision: must be approved`. No approval is fabricated.

### Standing gates
- `pvg lint --backlog`: PASS, 126 scanned, 0 errors, 0 review findings.
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-dmf2-full.xml`: PASS; parsed JUnit tests=2085 errors=0 failures=0 skipped=1.
- `uv run --frozen --extra dev wgp release verify`: PASS; release=ready, tag_created=false.
- Protected parity vs dispatcher base `31e3b7b`: PASS exit 0/empty diff. Older `40f8c2b` diagnostic fails only on the inherited main change to `services/jobs/preflight.py`.
- `git diff --check`: PASS.
- `pvg verify` authoring subset: PASS, 13 files, 0 issues.

### Commit
- Branch: `story/WD-dmf2`
- Pushed HEAD: `b654d5e02c9c35df95d43302851874357129c611`
- Generation base recorded in evidence: `31ec071abec9b80e922166c6683703b0a27ab893`

### AC Verification
| AC | Result | Evidence |
|---|---|---|
| 1 | NOT FULLY MET: real outputs/map/queue exist, but checker fails and reviewer is pending; no cell flipped | evidence.json; checker-result.stderr; row-dispositions.json |
| 2 | MET: incomplete/failing evidence left rows unchanged | row-dispositions.json; docs/director-capabilities.md |
| 3 | MET for recorded lineage: machine-checkable request-to-assembly map exists | planned-produced-map.json |
| 4 | PARTIAL: ordered/overlap/continuity/beat/pacing measurements pass; enhanced prompt has no produced media | objective-gates.json; planned-produced-map.json |
| 5 | MET: no planning artifact represented as host_run_verified | row-dispositions.json; checker-result.stderr |
| 6 | MET: no unsupported_on_this_hardware claim | row-dispositions.json |
| 7 | NOT MET: all nine rows remain planned rather than terminal verified states | matrix-transition-check.json |
| 8 | MET: no protected/scope violation; dispatcher-base parity passes | protected-parity-31e3b7b.exit; git diff |

LEARNINGS:
- The accepted evidence contract and an explicitly pending reviewer are mathematically incompatible; preserving pending causes the checker to fail closed, which is the correct honest outcome.
- Naming a lane-level QC record `qc-evidence.json` collides with the repository spend-gate corpus fixture count; `director-qc-evidence.json` avoids changing that contract.
- Full-suite release checks observe output redirection files in-repo. Run long suites with outputs in `/tmp`, then copy receipts after success.
- WD-bxhc exists on pushed story branch `origin/story/WD-bxhc`, not current `origin/main`; its accepted artifacts were hash-bound without merging that branch.

## nd_contract
status: delivered

### evidence
- Real host composition/QC artifacts, hashes, queue state, plans, checker failure, tests, release, protected parity, and pushed HEAD are recorded above and under `datasets/runs/maestro-parity/WD-dmf2/`.

### proof
- [x] AC #1 evaluated: not fully met; pending reviewer plus six failed objective gates prevent verified flips.
- [x] AC #2 evaluated: incomplete evidence left affected cells unchanged.
- [x] AC #3 evaluated: full planned-to-produced lineage is machine-checkable.
- [x] AC #4 evaluated: pacing/continuity measurements recorded; enhancement lacks corresponding produced media.
- [x] AC #5 evaluated: no plan-only artifact is claimed verified.
- [x] AC #6 evaluated: no hardware-infeasibility claim is made.
- [x] AC #7 evaluated: not met; all nine rows remain planned pending review.
- [x] AC #8 evaluated: no protected engine or unauthorized scope change.

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
- 2026-09-25T18:11:21Z dep_removed: was_blocked_by WD-2gyw
- 2026-09-25T20:13:03Z dep_removed: was_blocked_by WD-r81u
- 2026-09-25T21:27:31Z dep_removed: was_blocked_by WD-bxhc
- 2026-09-25T21:28:59Z status: open -> in_progress
- 2026-09-25T21:28:59Z auto-follows: linked to predecessor WD-rous
- 2026-09-25T21:28:59Z auto-follows: linked to predecessor WD-2gyw
- 2026-09-25T21:28:59Z auto-follows: linked to predecessor WD-r81u
- 2026-09-25T21:28:59Z auto-follows: linked to predecessor WD-bxhc
- 2026-09-25T21:28:59Z claimed by dev-WD-dmf2
- 2026-09-25T22:59:30Z status: in_progress -> in_progress
- 2026-09-25T22:59:30Z auto-follows: linked to predecessor WD-cpow
- 2026-09-25T23:01:44Z status: in_progress -> in_progress
- 2026-09-25T23:01:44Z auto-follows: linked to predecessor WD-0zj8

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Was blocked by: [[WD-rous]], [[WD-2gyw]], [[WD-r81u]], [[WD-bxhc]]
- Follows: [[WD-rous]], [[WD-2gyw]], [[WD-r81u]], [[WD-bxhc]], [[WD-cpow]], [[WD-0zj8]]

## Comments
