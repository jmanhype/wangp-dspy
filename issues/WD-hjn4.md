---
id: WD-hjn4
title: "RenderQC: VLM-scored output gate with genre thresholds"
status: in_progress
priority: 2
type: feature
created_at: 2026-08-22T04:26:23Z
created_by: speed
updated_at: 2026-08-22T04:26:49Z
content_hash: "sha256:c2b1f4769f2476f5a911523bc33a5ee92030f4253dcfcae1c1f8f3d7c9ae22d1"
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

## Links


## Comments
