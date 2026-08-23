---
id: WD-d06p
title: "cycle 5: MV remux — keeper audio mux, run FULLY through paivot ops (pure plugin-only story)"
status: closed
priority: 2
type: task
labels: [dogfood, mv, accepted]
created_at: 2026-08-23T18:15:07Z
created_by: speed
updated_at: 2026-08-23T18:17:07Z
content_hash: "sha256:50eaab2c7bc5a9539a06892afc4fdb2f049166a8a212cc5ab8eb465acfc64190"
closed_at: 2026-08-23T18:17:06Z
close_reason: "cycle 5 pure-paivot run: remux seam built and applied, output verified (duration match), lifecycle through plugin ops only after T0"
---

## Description
Second pure dogfood: like WD-t6i7 but audio. Take the cycle-4 4-shot kaiju multishot (pull6 mv1.mp4, 17.6s), mux a keeper audio track (heartmula or local audio gen), remux via the Assembler lane — every step dispatched through paivot plugin ops in a real Hermes session: story_claim (orchestrator), story_deliver with evidence (developer), story_accept (pm_acceptor), insight_append for findings. Zero manual pvg/nd after T0. Exercises: remux lane (never run post-separator-fix), audio integration, evidence chain for non-render artifacts.

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-08-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-08-23T18:17:00Z status: open -> in_progress
- 2026-08-23T18:17:06Z status: in_progress -> closed

## Links


## Comments
