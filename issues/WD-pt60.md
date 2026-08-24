---
id: WD-pt60
title: "j9nx-1: Pipeline dspy.Module + task registry (intent -> briefs -> profile -> assemble -> render -> QC in one call)"
status: in_progress
priority: 2
type: task
labels: [feature, pipeline]
parent: WD-j9nx
created_at: 2026-08-24T14:54:53Z
created_by: speed
updated_at: 2026-08-24T15:07:34Z
content_hash: "sha256:0b4c45a0ed4870931684cc1c32efb326d4ee8dc11b0aee179f4e124caef070d8"
assignee: jmanhype-glm
follows: [WD-xzqp]
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

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-xzqp]]

## Comments
