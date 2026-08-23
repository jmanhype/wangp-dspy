---
id: WD-t6i7
title: "Real 3090 smoke render — WanGPAdapter with real critic, keeper evidence"
status: closed
priority: 2
type: task
parent: WD-j9nx
created_at: 2026-08-22T20:12:56Z
created_by: speed
updated_at: 2026-08-23T01:38:49Z
content_hash: "sha256:fb9b2889e2502ea00be3f2fbc5ddfcd9884597b8dbe2bce58df17167e0579d43"
assignee: dev-WD-t6i7
labels: [delivered, accepted]
closed_at: 2026-08-23T01:38:48Z
close_reason: "real 3090 render + QC PASS (6.0/5.0/7.0 surreal) + audit ok; both code fixes merged (b3796c0, 9788f25); three follow-up stories seeded (WD-5zti, WD-d3b9, WD-h0vk)"
---

## Description
1x96f shot through WanGPAdapter (minimax_h3_fl2va_pruned) with real VLM critic, keeper paths committed as evidence. RUNS THROUGH paivot-hermes adapter: operator-seeded story, real Hermes session, plugin tools only (no manual pvg/nd after T0), evidence chain on. First cross-project dogfood — closes generality gap. AC: (1) real render completes (96f, 24fps) (2) real critic QC verdict recorded (3) keeper path(s) committed as evidence chain entries (4) zero manual pvg/nd after session start (5) insight_append used >=1x during the story (dogfoods the new ledger)

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-08-22.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-08-22T22:15:11Z status: open -> in_progress
- 2026-08-22T22:15:11Z claimed by dev-WD-t6i7
- 2026-08-22T22:42:33Z status: in_progress -> in_progress
- 2026-08-23T01:38:48Z status: in_progress -> closed

## Links
- Parent: [[WD-j9nx]]

## Comments
