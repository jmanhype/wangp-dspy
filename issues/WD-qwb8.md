---
id: WD-qwb8
title: "ProfileSelector: render brief -> WanGP/H3 profile decision"
status: in_progress
priority: 2
type: feature
created_at: 2026-08-22T04:16:54Z
created_by: speed
updated_at: 2026-08-22T04:17:22Z
content_hash: "sha256:c1ed4558059847d44f306033b0fab0a01e845fb5fa2c5a823de19c619e790163"
assignee: dev-WD-qwb8
---

## Description
Story 2 of WD-j9nx. DSPy module choosing render profile params from a RenderBrief: model (H3 vs alternatives), resolution (720p/768p), shot length (>=4s = 96f floor per H3 convention), seed policy, profile name mapping to WangP profiles. Signature: brief -> profile decision JSON. Tests with DummyLM: floor constraints enforced (typed rejection below 96f), enum validation of model/resolution, unknown profile rejected. TDD strict, same gates.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-22T04:17:22Z status: open -> in_progress
- 2026-08-22T04:17:22Z claimed by dev-WD-qwb8

## Links


## Comments
