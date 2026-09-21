---
id: WD-rf1a
title: "Delivered media resolution contradicts the plan envelope for every recorded render"
status: open
priority: 0
type: task
parent: WD-as25
created_at: 2026-09-21T07:00:04Z
created_by: speed
updated_at: 2026-09-21T07:00:04Z
content_hash: "sha256:801ef41f678c0c1ebc6fe51dca2a1d2cd85ede79345c4829a6aa2fe21db228a6"
---

## Description
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


## Links
- Parent: [[WD-as25]]

## Comments
