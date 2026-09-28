---
id: WD-b3fn
title: "Director structural limitation disposition"
status: open
priority: 1
type: task
labels: [director, evidence, operator-decision]
parent: WD-3nod
created_at: 2026-09-28T13:27:29Z
created_by: speed
updated_at: 2026-09-28T13:27:29Z
content_hash: "sha256:6abb49ed5700796c297135e88bb55ec92fad3c0092a5fd091caee8e1859634eb"
blocks: [WD-fay0]
---

## Description
## Context

## USER INTENT
The Maestro-parity programme must stop carrying ambiguous `planned` director cells. The operator has now selected the structural-disposition branch instead of another media rework.

## Operator decision
Verbatim operator input:

> Approve

Recorded at `2026-09-28T13:20:11Z` in response to the three-way question covering director structural limitation, cloning-reference consent, and one no-new-download H3 clean-machine run. This story uses that approval only for the director branch.

Decision:

- Do not rework clip 1 again in this story.
- Do not change Whisper or SyncNet thresholds.
- Record the accepted media-specific objective failures as the operator-approved structural limitation for the remaining executable director planning cells.
- This is not a claim that the RTX 3090 cannot pass the gates: WD-dmf2 clip 2 passed the same 1.0 SyncNet bar.

## Embedded current state
At merged main `6ac1023b522726705d3ea560216f211003a1d4bd`, `docs/director-capabilities.md` has exactly 23 `planned` executable cells. The two already accepted `Auto/manual review checkpoints` cells remain `host_run_verified` and must not be disturbed.

The accepted WD-dmf2 objective evidence records three failing clip-1 gates:

- Whisper screenplay clip 1 score `0.556` against `0.6`
- SyncNet audio clip 1 confidence `0.594741` against `1.0`
- SyncNet screenplay clip 1 confidence `0.468897` against `1.0`

The same accepted bundle records SyncNet screenplay clip 2 confidence `1.10503`, proving that the threshold is reachable and that the limitation is media-specific rather than a global hardware impossibility.

## OUT OF SCOPE
- No new director media generation, GPU work, model download, provider spend, or clip-1 rework.
- No Whisper, vision, mouth-box, SyncNet, queue, renderer, wiring, preflight, or `scripts/run_film.py` semantic/threshold change.
- No modification of the two already verified review-checkpoint cells.
- No voice/character consent or clean-machine work; those have separate stories.

## DIFF BUDGET
- About 3 files and under 250 changed LOC: the director matrix, a small structural-disposition evidence bundle, and narrowly scoped tests or transition evidence.

## Boundary Map
PRODUCES:
- docs/director-capabilities.md -> operator-approved terminal dispositions for exactly the 23 currently planned executable director cells
  spec: each affected cell begins with `unsupported` and links the new structural-limitation decision record; zero `planned` tokens remain in the director matrix.
- datasets/runs/maestro-parity/WD-director-structural-limitation/ -> operator decision and mechanical matrix-transition evidence
  event: stores verbatim approval, the three failed measurements, the passing clip-2 counterexample, before/after rows, changed-cell count, and unrelated-row check.

CONSUMES:
- WD-dmf2: datasets/runs/maestro-parity/WD-dmf2/gate-derivation.json -> objective gate records with `name`, `measured`, `threshold`, and `verdict`
  source: the three exact failing values and the passing clip-2 counterexample must be read from this accepted artifact, not rewritten from memory.
- WD-7fvx: docs/director-capabilities.md -> current accepted review-checkpoint matrix state
  source: the two `host_run_verified` cells must remain byte-for-byte equivalent in status and evidence link.

## Story Acceptance Criteria
1. [State] A new decision record stores the verbatim `Approve` authorization, timestamp, operator identity, exact three-value failure evidence, passing clip-2 counterexample, and explicit non-hardware boundary.
2. [State] `docs/director-capabilities.md` transitions exactly the 23 currently planned executable director cells to an `unsupported` structural-media-limitation disposition linked to that record.
3. [State] A mechanical before/after transition artifact proves 23 changed cells, zero director `planned` cells after, two preserved `host_run_verified` cells, and no unrelated capability row changes.
4. [Unwanted] No threshold, QC gate, production engine semantic, protected file, media artifact, or historical WD-dmf2/WD-7fvx evidence is changed.
5. [State] Targeted director/capability tests and any new matrix-transition test pass.
6. [State] The undeselected full suite, `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity from `6ac1023b`, and `git diff --check` pass at the delivered head.

## Testing Requirements
- Add or adapt a deterministic matrix transition test if the existing director tests do not already prove count and scope.
- Run the focused director test module and the relevant capability documentation tests.
- Run the undeselected full suite with parsed JUnit counters.
- Run all standing gates listed in AC 6.
- Record coverage for any newly added Python test/report helper; if the change is documentation/evidence-only, explicitly record why Python coverage is not applicable.

## Delivery Requirements
- Record the exact matrix diff, before/after counts, all gate values with pass/fail status, commit SHA, branch, PR, CI run, and standard delivery proof sections.
- Include `## Implementation Evidence`, `Summary:`, `Commands run:`, `SHA:`, `### CI/Test Results`, `### AC Verification`, and `LEARNINGS:`.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Created from operator approval at `2026-09-28T13:20:11Z`, merged main `6ac1023b522726705d3ea560216f211003a1d4bd`, and accepted WD-dmf2/WD-7fvx evidence.

### proof
- [ ] Pending structural decision record, exact 23-cell matrix transition, scoped tests, and standing gates.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-28T13:27:32Z dep_added: blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]

## Comments
