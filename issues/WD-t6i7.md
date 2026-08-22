---
id: WD-t6i7
title: "Real 3090 smoke render — WanGPAdapter with real critic, keeper evidence"
status: in_progress
priority: 2
type: task
parent: WD-j9nx
created_at: 2026-08-22T20:12:56Z
created_by: speed
updated_at: 2026-08-22T22:42:33Z
content_hash: "sha256:9854f9563273eb4884b04fa4120e096f51764c07981fd4ab1049f6f335713ada"
assignee: dev-WD-t6i7
---

## Description
1x96f shot through WanGPAdapter (minimax_h3_fl2va_pruned) with real VLM critic, keeper paths committed as evidence. RUNS THROUGH paivot-hermes adapter: operator-seeded story, real Hermes session, plugin tools only (no manual pvg/nd after T0), evidence chain on. First cross-project dogfood — closes generality gap. AC: (1) real render completes (96f, 24fps) (2) real critic QC verdict recorded (3) keeper path(s) committed as evidence chain entries (4) zero manual pvg/nd after session start (5) insight_append used >=1x during the story (dogfoods the new ledger)

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-22T22:15:11Z status: open -> in_progress
- 2026-08-22T22:15:11Z claimed by dev-WD-t6i7
- 2026-08-22T22:42:33Z status: in_progress -> in_progress

## Links
- Parent: [[WD-j9nx]]

## Comments
