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
content_hash: "sha256:0865d4dc7374a19d458d0cc177428b5f8e5374d4488170ea1c55f8f72580e0d4"
assignee: jmanhype-glm
follows: [WD-xzqp]
closed_at: 2026-08-24T15:11:39Z
close_reason: "PR #21 merged: Pipeline dspy.Module (one-call artifact chain, typed boundary failures, evidence trail) + tasks.py genre registry. 7 e2e stub tests, full suite 244 green."
led_to: [WD-mhr2, WD-qbcj, WD-4k56]
blocks: [WD-h25b]
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
- 2026-09-19T20:39:23Z dep_added: blocks WD-h25b

## Links
- Parent: [[WD-j9nx]]
- Blocks: [[WD-h25b]]
- Follows: [[WD-xzqp]]
- Led to: [[WD-mhr2]], [[WD-qbcj]], [[WD-4k56]]

## Comments
