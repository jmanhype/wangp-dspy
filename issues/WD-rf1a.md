---
id: WD-rf1a
title: "Delivered media resolution contradicts the plan envelope for every recorded render"
status: in_progress
priority: 0
type: task
parent: WD-as25
created_at: 2026-09-21T07:00:04Z
created_by: speed
updated_at: 2026-09-23T16:04:26Z
content_hash: "sha256:b3a03ed2bd9c178e77cefb304894b3499d1e4531342d1e0a68e389a1011945e4"
assignee: dev-WD-rf1a
blocks: [WD-l48s]
---

## Description
## USER INTENT
A user can run deterministic preflight replay and see real delivered media dimensions reconciled with the plan envelope rather than every complete row rejected for `delivered_resolution_contradicts_envelope`.

## Symptom
Every recorded render's delivered resolution contradicts the resolution recorded in that run's own plan/envelope, so the production preflight invariant "delivered media envelope == planned envelope" is false for 100% of recorded complete rows.

## Measured evidence
From the preflight spend-gate corpus built in WD-l48s (`datasets/spend-gate/v1/`, `--evidence-mode all-local`):

- `deterministic_preflight` rejects **18 of 18** complete rows, and every rejection carries the single reason `delivered_resolution_contradicts_envelope`.
- The same holds in the tracked subset (13 of 13).
- Concrete instance: the operator-accepted LF004 recovery film delivers **704x576** while the planning envelope for those clips records **480x832**. That film passed every declared QC/AV gate and was operator-accepted, so the delivered numbers are the ones that actually shipped; the envelope field is the wrong one.
- Gate outcomes are unaffected: vision 25/0, whisper post 27/9, av_sync 13/5 all recorded against the delivered media.

## Impact
- The spend-gate deterministic baseline cannot admit any real render until this field is correct, which blocks any calibrated admission work (WD-as25).
- Any other consumer of the planned resolution — aspect-ratio or framing checks, plate sizing, LoRA/model targeting, contact-sheet layout — is reading a number that contradicts reality.
- The contradiction is currently silent: nothing in the pipeline compares the envelope resolution against the delivered media.

## Scope
Determine why the envelope resolution disagrees with delivered media (planner field vs render profile vs post-process/rescale step), then correct the recording or the checks so the invariant is either true or explicitly typed as a known transform. Do not change any QC/AV/retry gate.

## Out of scope
- Any render. This is a recording/verification defect; existing accepted artifacts must not be mutated.
- The union/envelope redesign of other missing queue-envelope fields (separate triage).

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Discovered during WD-l48s replay; reasons attributed per row in `datasets/spend-gate/v1/replay-report.md`.

### proof
- [ ] Pending: identify the divergence point and fix it, or record why the delivered resolution intentionally differs.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-23T15:59:30Z status: open -> in_progress
- 2026-09-23T15:59:30Z claimed by dev-WD-rf1a

- 2026-09-23T16:02:18Z dep_added: blocks WD-l48s

## Links
- Parent: [[WD-as25]]
- Blocks: [[WD-l48s]]

## Comments
