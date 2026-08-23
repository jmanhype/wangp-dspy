---
id: WD-d06p
title: "cycle 5: MV remux — keeper audio mux, run FULLY through paivot ops (pure plugin-only story)"
status: in_progress
priority: 2
type: task
labels: [dogfood, mv, delivered]
created_at: 2026-08-23T18:15:07Z
created_by: speed
updated_at: 2026-08-23T18:17:01Z
content_hash: "sha256:703a02a3fafe2fb0f0e0a7d0d8170539ea63e0ce90810231b2c9ba9b882c245f"
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

## Links


## Comments
