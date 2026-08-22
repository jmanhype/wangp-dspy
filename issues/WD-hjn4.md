---
id: WD-hjn4
title: "RenderQC: VLM-scored output gate with genre thresholds"
status: closed
priority: 2
type: feature
created_at: 2026-08-22T04:26:23Z
created_by: speed
updated_at: 2026-08-22T05:21:36Z
content_hash: "sha256:3f991ccd81582885fe50a1e5522cca99e170f3a85af6fc0caacefbc14cf3aa32"
assignee: dev-WD-hjn4
---

## Description
Story 3 of WD-j9nx. DSPy module scoring rendered video against brief+decision: VLM critique signature (coherence, brief-adherence, concept encoding per genre), threshold table comedy>=7 edu>=8 music>=5 surreal>=4.5 (operator-tunable, module-level constants), verdict pass/revise/reject with typed reasons. QC verdicts feed the existing gates: CONCEPT_ENCODING_FAILURE (informed-good blind-bad) triggers one revision with ONE anchor then human. Tests: DummyLM stubbed VLM critiques, threshold boundary pairs, verdict vocabulary, revision-escalation logic. No real VLM calls in tests (local vLLM path comes later as adapter).

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-22T04:26:49Z status: open -> in_progress
- 2026-08-22T04:26:49Z claimed by dev-WD-hjn4
- 2026-08-22T04:26:49Z status: in_progress -> in_progress
- 2026-08-22T05:21:36Z status: in_progress -> closed

## Links


## Comments
