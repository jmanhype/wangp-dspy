---
id: WD-42no
title: "E2e: execute exactly one approved LF004 governed render"
status: in_progress
priority: 0
type: task
labels: [e2e, capstone]
parent: WD-h73w
created_at: 2026-09-20T19:48:19Z
created_by: speed
updated_at: 2026-09-20T23:37:24Z
content_hash: "sha256:0fe57be250efad7e9ef9c3e85057b35153e32d7e9c769abc3c88d984d263a686"
blocked_by: [WD-rb1f, WD-rj6e]
was_blocked_by: [WD-z46c]
assignee: dev-WD-42no
follows: [WD-z46c]
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

## Acceptance Criteria


## Design


## Notes
## Fail-Closed LF004 Boundary Evidence

The approved execution did not proceed to cuts 3/4. Cut 2 exhausted the accepted three-attempt QC retry policy and is durable-queue dead-lettered:

- Seed 904 raw SHA-256 `7351334145399bd4b26454760e97869da412e3015d441ea31516365c4ad3b397`: post-Whisper score 0.167; transcript included hallucinated preceding dialogue.
- Seed 905 raw SHA-256 `93075b7b7633289b2f956fb23d4fe40061650c140aff9f6af2195daa6b7d65ff`: post-Whisper score 0.167; intended line repeated.
- Seed 906 raw SHA-256 `cb1293c6e987f6a5224b3649c27392b9f75cbec769b4a1ed1ad1f944c64e71de`: Whisper pre/post passed (post score 1.0), but identity/action vision rejected ghosting/double-exposure artifacts (`action_match=0.1`, `speaker_attribution=0.1`).
- Queue states: cut 1 `done`; cut 2 `dead_letter` after 3 `qc_gate` failures; cuts 3/4 remain `pending` behind cut 2.
- Contact sheets and hashes: `datasets/runs/provenance/lf004-operator-dogfood-20260920/cut2-deadletter-review/`.
- Independent seed-905 visual re-judge passed identity/action but observed the speaker mouth closed; it is not a substitute because post-Whisper and AV gates remain failed.

No gate was relaxed and no fourth render was started. Continuing with seed 907 would exceed the current approved retry policy and needs a new explicit operator-approved recovery story.

## nd_contract
status: in_progress

### evidence
- Durable queue and attempt failure records above; dead-letter review artifacts on disk.

### proof
- [x] Fail closed at cut 2 rather than relaxing Whisper/vision/retry gates.
- [ ] Operator decision required before any additional render or recovery story.

## Operator Render Approval

Approved UTC: 2026-09-20T20:47:21Z
Operator response: yes
Exact canonical plan SHA-256: 70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86
Authorization: exactly one governed LF004 production execution through the accepted Wangp pipeline. This approval does not authorize a second independent run, live-hook changes, or unrelated work.

## History
- 2026-09-20T19:48:19Z dep_added: blocked_by WD-z46c
- 2026-09-20T19:48:47Z dep_added: blocked_by WD-rb1f
- 2026-09-20T19:48:47Z dep_added: blocked_by WD-rj6e
- 2026-09-20T20:14:46Z dep_removed: was_blocked_by WD-z46c
- 2026-09-20T20:47:21Z status: open -> in_progress
- 2026-09-20T20:47:21Z auto-follows: linked to predecessor WD-z46c
- 2026-09-20T20:47:21Z claimed by dev-WD-42no

## Links
- Parent: [[WD-h73w]]
- Blocked by: [[WD-rb1f]], [[WD-rj6e]]
- Was blocked by: [[WD-z46c]]
- Follows: [[WD-z46c]]

## Comments
