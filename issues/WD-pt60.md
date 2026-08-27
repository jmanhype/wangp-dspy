---
id: WD-pt60
title: "j9nx-1: Pipeline dspy.Module + task registry (intent -> briefs -> profile -> assemble -> render -> QC in one call)"
status: closed
priority: 2
type: task
labels: [feature, pipeline]
parent: WD-j9nx
created_at: 2026-08-24T14:54:53Z
created_by: speed
updated_at: 2026-08-24T15:11:39Z
content_hash: "sha256:bcc0bf0d6c3767120d71270d994d8046930a4584681a39201871c9dda7a5c105"
assignee: jmanhype-glm
follows: [WD-xzqp]
closed_at: 2026-08-24T15:11:39Z
close_reason: "PR #21 merged: Pipeline dspy.Module (one-call artifact chain, typed boundary failures, evidence trail) + tasks.py genre registry. 7 e2e stub tests, full suite 244 green."
led_to: [WD-mhr2, WD-qbcj, WD-4k56]
---

## Description
The epic's core gap: stages exist and are individually tested but NOTHING chains them — no Pipeline class, no public API. Build a top-level dspy.Module in predict/pipeline.py whose forward() runs the whole flow with typed failures at each stage boundary (per dspy multi-stage pattern: module composes sub-modules; whole program becomes traceable/optimizable, not just leaves). Include a tasks.py-style registry (dspy-gepa-example pattern) binding genre -> dataset -> metric -> QC profile so j9nx-3 renders self-register and j9nx-4 GEPA can target one genre at a time. Public API exports. Acceptance: e2e test with stubbed LM + stubbed host passes; each stage boundary failure is typed; registry lookups work.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-24T15:07:34Z status: open -> in_progress
- 2026-08-24T15:07:34Z auto-follows: linked to predecessor WD-xzqp
- 2026-08-24T15:07:34Z claimed by jmanhype-glm
- 2026-08-24T15:11:39Z status: in_progress -> closed

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-xzqp]]
- Led to: [[WD-mhr2]], [[WD-qbcj]], [[WD-4k56]]

## Comments
