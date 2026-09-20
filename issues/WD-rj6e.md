---
id: WD-rj6e
title: "E2e: execute exactly one approved LF004 governed render"
status: closed
priority: 0
type: task
labels: [e2e]
parent: WD-h73w
created_at: 2026-09-20T19:46:39Z
created_by: speed
updated_at: 2026-09-20T19:48:28Z
content_hash: "sha256:1e1effcf20be1cc631091fdd39c249a79fac276a90f1b5732c2d361dcf4348eb"
was_blocked_by: [WD-rb1f]
closed_at: 2026-09-20T19:48:19Z
close_reason: "Superseded: initial story body duplicated boundary sections during repair; replacement carries the corrected executable contract."
blocks: [WD-42no]
led_to: [WD-z46c]
---

## Description
## USER INTENT
After explicitly approving the LF004 no-GPU plan, the operator wants exactly one governed real render that produces and stores a reviewable keeper-or-reject film artifact.

## Context (Embedded)
This story must not start until the planning story is accepted and the operator explicitly approves the exact plan hash. It uses the existing governed queue, preflight, provenance, vision/Whisper/SyncNet gates, retry policy, and assembly path. Governed retries belong to the one execution; a second independent production run does not.

## OUT OF SCOPE
- Running before explicit approval of the exact plan hash.
- A second independent render run.
- Changing pipeline behavior, gates, risk boundaries, or retry semantics.
- Claiming creative acceptance without an explicit operator verdict.

## DIFF BUDGET
- Runtime artifacts and evidence only unless an execution script is indispensable; under 200 changed LOC.

## Boundary Map
PRODUCES:
- one governed LF004 execution with queue/provenance records
- one reviewable assembled film and contact-sheet/probe review artifacts
- final mechanical gate evidence and operator-review-pending record

CONSUMES:
- accepted LF004 content plan and run ledger
  schema: wangp-dspy.content-plan/v1 plus canonical run ledger
- scripts/run_film.py -> run_film(...)
  spec: run_film(script_file, plates_dir, characters, ..., dry_run: bool = False) -> run result
- existing governed queue, render host, QC, AV, and provenance subsystems
  source: accepted Wangp governed production pipeline modules and remote host policy

## Story Contract
The user can inspect exactly one governed LF004 render whose final film, probes, review visuals, and provenance are stored and hash-identified.

1. Execution begins only after the exact approved plan hash is recorded in nd.
2. Exactly one governed production execution is started; its identifier and every governed retry are recorded.
3. Host and pipeline preflight pass before model/render work.
4. Every emitted cut passes identity vision, mouth-box, Whisper pre/post, and SyncNet gates under current accepted policy.
5. Assembly completes and final media hash, duration, resolution, frame count, and audio properties are recorded.
6. A human-reviewable contact sheet and/or first-frame packet is emitted beside probe evidence.
7. Provenance ties brief, plan, inputs, queue records, settings, retries, QC, assembly, repository state, and final hash together.
8. The story records `operator_review_pending`; no creative acceptance is claimed automatically.
9. No unrelated source behavior changes.

## Testing Requirements
- Exact governed commands required by the accepted LF004 plan.
- All runtime-declared targeted QC/provenance tests.
- `ffprobe` final-media validation.
- Contact-sheet/probe generation and hash recording.
- `git diff --check`

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Operator limited this goal to exactly one Wangp real render.

### proof
- [ ] Story #1: Exact plan approval precedes execution.
- [ ] Story #2: One execution and all retries are accounted for.
- [ ] Story #3: Preflight passes.
- [ ] Story #4: All declared cut gates pass.
- [ ] Story #5: Final media properties and hash are recorded.
- [ ] Story #6: Review visuals are available.
- [ ] Story #7: End-to-end provenance is complete.
- [ ] Story #8: Operator review remains pending.
- [ ] Story #9: No unrelated behavior changes.

## USER INTENT
After explicitly approving the LF004 no-GPU plan, the operator wants exactly one governed real render that produces and stores a reviewable keeper-or-reject film artifact.

## Context (Embedded)
This story must not start until the planning story is accepted and the operator explicitly approves the exact plan hash. It uses the existing governed queue, preflight, provenance, vision/Whisper/SyncNet gates, retry policy, and assembly path. Governed retries belong to the one execution; a second independent production run does not.

## OUT OF SCOPE
- Running before explicit approval of the exact plan hash.
- A second independent render run.
- Changing pipeline behavior, gates, risk boundaries, or retry semantics.
- Claiming creative acceptance without an explicit operator verdict.

## DIFF BUDGET
- Runtime artifacts and evidence only unless an execution script is indispensable; under 200 changed LOC.

## Boundary Map
PRODUCES:
- one governed LF004 execution with queue/provenance records
- one reviewable assembled film and contact-sheet/probe review artifacts
- final mechanical gate evidence and operator-review-pending record

CONSUMES:
- accepted LF004 content plan and run ledger
  schema: wangp-dspy.content-plan/v1 plus canonical run ledger
- scripts/run_film.py -> run_film(...)
  spec: run_film(script_file, plates_dir, characters, ..., dry_run: bool = False) -> run result
- existing governed queue, render host, QC, AV, and provenance subsystems
  source: accepted Wangp governed production pipeline modules and remote host policy

## Story Contract
The user can inspect exactly one governed LF004 render whose final film, probes, review visuals, and provenance are stored and hash-identified.

1. Execution begins only after the exact approved plan hash is recorded in nd.
2. Exactly one governed production execution is started; its identifier and every governed retry are recorded.
3. Host and pipeline preflight pass before model/render work.
4. Every emitted cut passes identity vision, mouth-box, Whisper pre/post, and SyncNet gates under current accepted policy.
5. Assembly completes and final media hash, duration, resolution, frame count, and audio properties are recorded.
6. A human-reviewable contact sheet and/or first-frame packet is emitted beside probe evidence.
7. Provenance ties brief, plan, inputs, queue records, settings, retries, QC, assembly, repository state, and final hash together.
8. The story records `operator_review_pending`; no creative acceptance is claimed automatically.
9. No unrelated source behavior changes.

## Testing Requirements
- Exact governed commands required by the accepted LF004 plan.
- All runtime-declared targeted QC/provenance tests.
- `ffprobe` final-media validation.
- Contact-sheet/probe generation and hash recording.
- `git diff --check`

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Operator limited this goal to exactly one Wangp real render.

### proof
- [ ] Story #1: Exact plan approval precedes execution.
- [ ] Story #2: One execution and all retries are accounted for.
- [ ] Story #3: Preflight passes.
- [ ] Story #4: All declared cut gates pass.
- [ ] Story #5: Final media properties and hash are recorded.
- [ ] Story #6: Review visuals are available.
- [ ] Story #7: End-to-end provenance is complete.
- [ ] Story #8: Operator review remains pending.
- [ ] Story #9: No unrelated behavior changes.

## USER INTENT
After explicitly approving the LF004 no-GPU plan, the operator wants exactly one governed real render that becomes a reviewable keeper-or-reject film artifact.

## Context (Embedded)
This story must not start until the planning story is accepted and the operator explicitly approves the exact plan hash. It uses the existing governed queue, preflight, provenance, vision/Whisper/SyncNet gates, retry policy, and assembly path. Governed retries belong to the one execution; a second independent production run does not.

## OUT OF SCOPE
- Running before explicit approval of the exact plan hash.
- A second independent render run.
- Changing pipeline behavior, gates, risk boundaries, or retry semantics.
- Claiming creative acceptance without an explicit operator verdict.

## DIFF BUDGET
- Runtime artifacts and evidence only unless an execution script is indispensable; under 200 changed LOC.

## Boundary Map
PRODUCES:
- one governed LF004 execution with queue/provenance records
- one reviewable assembled film and contact-sheet/probe review artifacts
- final mechanical gate evidence and operator-review-pending record

CONSUMES:
- accepted LF004 content plan and run ledger
- scripts/run_film.py -> run_film(...)
- existing governed queue, render host, QC, AV, and provenance subsystems

## Acceptance Criteria
1. Execution begins only after the exact approved plan hash is recorded in nd.
2. Exactly one governed production execution is started; its identifier and every governed retry are recorded.
3. Host and pipeline preflight pass before model/render work.
4. Every emitted cut passes identity vision, mouth-box, Whisper pre/post, and SyncNet gates under current accepted policy.
5. Assembly completes and final media hash, duration, resolution, frame count, and audio properties are recorded.
6. A human-reviewable contact sheet and/or first-frame packet is emitted beside probe evidence.
7. Provenance ties brief, plan, inputs, queue records, settings, retries, QC, assembly, repository state, and final hash together.
8. The story records `operator_review_pending`; no creative acceptance is claimed automatically.
9. No unrelated source behavior changes.

## Testing Requirements
- Exact governed commands required by the accepted LF004 plan.
- All runtime-declared targeted QC/provenance tests.
- `ffprobe` final-media validation.
- Contact-sheet/probe generation and hash recording.
- `git diff --check`

## nd_contract
status: new

### evidence
- Operator limited this goal to exactly one Wangp real render.

### proof
- [ ] AC #1: Exact plan approval precedes execution.
- [ ] AC #2: One execution and all retries are accounted for.
- [ ] AC #3: Preflight passes.
- [ ] AC #4: All declared cut gates pass.
- [ ] AC #5: Final media properties and hash are recorded.
- [ ] AC #6: Review visuals are available.
- [ ] AC #7: End-to-end provenance is complete.
- [ ] AC #8: Operator review remains pending.
- [ ] AC #9: No unrelated behavior changes.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-20T19:46:39Z dep_added: blocked_by WD-rb1f
- 2026-09-20T19:48:18Z dep_removed: was_blocked_by WD-rb1f
- 2026-09-20T19:48:19Z status: open -> closed
- 2026-09-20T19:48:47Z dep_added: blocks WD-42no

## Links
- Parent: [[WD-h73w]]
- Blocks: [[WD-42no]]
- Was blocked by: [[WD-rb1f]]
- Led to: [[WD-z46c]]

## Comments
