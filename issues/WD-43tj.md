---
id: WD-43tj
title: "Maestro parity: TaoMate host boundary"
status: in_progress
priority: 1
type: task
labels: [capability, evidence]
parent: WD-3nod
created_at: 2026-09-26T18:42:51Z
created_by: speed
updated_at: 2026-09-26T18:48:46Z
content_hash: "sha256:5aced447c1780662a7e74590571fc77236c7eb9b229b3da4c27ceb0009ed09dc"
blocks: [WD-fay0]
assignee: dev-WD-43tj
follows: [WD-9ymi, WD-f0vk]
---

## Description
WD-TAOMATE terminally dispositions all nine `minimax_h3/taomate_three_step` cells without a GPU render or model download. TaoMate is a named WanGP/Maestro preset, not a generic three-inference-step prompt; a generic H3 render cannot proxy for it.

Each cell must become `unsupported` only from live read-only host search evidence showing no TaoMate implementation, handler, preset, model identity, or settings path in the checked-out Wan2GP and Maestro trees. The story must preserve the existing accepted WD-2gyw search evidence, add current command/hash evidence, and update only the nine TaoMate cells in `docs/video-capabilities.md`.

Operator authorization is the 2026-09-26 text "Authorized and approved." followed by "continue", scoped to read-only host inventory. No GPU, inference, download, training, host mutation, paid provider, or accepted-artifact mutation is authorized.

## Acceptance Criteria
- [ ] A live read-only search of the checked-out Wan2GP and Maestro trees finds zero TaoMate implementation, handler, preset, settings, or model-identity matches and records the exact command, exit status, timestamp, and host.
- [ ] The boundary record preserves and cites the accepted WD-2gyw TaoMate search evidence without mutating it.
- [ ] All nine `minimax_h3/taomate_three_step` cells become `unsupported` with links to the new boundary evidence; no generic H3 render is relabelled.
- [ ] `docs/video-capabilities.md` changes only the TaoMate row and the supporting disposition narrative.
- [ ] Scoped capability/evidence tests, `pvg lint --backlog`, `git diff --check`, and clean release verification pass.
- [ ] Delivery evidence records that no GPU, inference, download, training, host mutation, paid provider, or accepted-artifact mutation occurred.

## MANDATORY SKILLS
None identified.

## Design


## Notes


## History
- 2026-09-26T18:43:28Z dep_added: blocks WD-fay0
- 2026-09-26T18:43:33Z status: open -> in_progress
- 2026-09-26T18:43:33Z auto-follows: linked to predecessor WD-9ymi
- 2026-09-26T18:43:33Z claimed by dev-WD-43tj
- 2026-09-26T18:48:46Z status: in_progress -> in_progress
- 2026-09-26T18:48:46Z auto-follows: linked to predecessor WD-f0vk

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-9ymi]], [[WD-f0vk]]

## Comments
