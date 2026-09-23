---
id: WD-as25
title: "Preflight spend intelligence for governed film production"
status: closed
priority: 1
type: epic
created_at: 2026-09-21T05:25:49Z
created_by: speed
updated_at: 2026-09-23T20:14:14Z
content_hash: "sha256:c45d1ab57155ffcf47c8d2b0ce0edc50570f4dd4a72ba0f3d52f88dc6c0c73ac"
closed_at: 2026-09-23T20:14:14Z
close_reason: "All stories accepted"
---

## Description
## Epic Outcome
Make future render-admission decisions measurable without changing any production gate: normalize every recorded clip outcome, replay deterministic and learned baselines on identical leakage-safe splits, and guarantee that future runs keep adding decision-ready rows.

## Scope Boundary
This epic is evidence and evaluation only. It does not authorize GPU work, model deployment, Content Brief Gateway repair, or changes to Whisper, vision, mouth-box, SyncNet, retry, or provenance gates.

## MANDATORY SKILLS
- pvg

## Acceptance Criteria


## Design


## Notes
Reopened 2026-09-23 to host a P0 spend-gate canonicalization regression discovered on merged main 8c67a01 during the WD-h73w full-suite completion gate. The prior epic acceptance remains historical, but its normalized-evidence outcome is not release-green while the operator main checkout fails the LF004 parity test.

## History
- 2026-09-23T17:43:57Z status: open -> closed
- 2026-09-23T18:47:34Z status: closed -> open
- 2026-09-23T20:14:14Z status: open -> closed

## Links


## Comments
