---
id: WD-hjn4
title: "RenderQC: VLM-scored output gate with genre thresholds"
status: open
priority: 2
type: feature
created_at: 2026-08-22T04:26:23Z
created_by: speed
updated_at: 2026-08-22T04:26:23Z
content_hash: "sha256:94420fd6aaef3764da703f9ebf5565444dff42f5e78c63a7f82d9f39edb67293"
---

## Description
Story 3 of WD-j9nx. DSPy module scoring rendered video against brief+decision: VLM critique signature (coherence, brief-adherence, concept encoding per genre), threshold table comedy>=7 edu>=8 music>=5 surreal>=4.5 (operator-tunable, module-level constants), verdict pass/revise/reject with typed reasons. QC verdicts feed the existing gates: CONCEPT_ENCODING_FAILURE (informed-good blind-bad) triggers one revision with ONE anchor then human. Tests: DummyLM stubbed VLM critiques, threshold boundary pairs, verdict vocabulary, revision-escalation logic. No real VLM calls in tests (local vLLM path comes later as adapter).

## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments
