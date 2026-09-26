---
id: WD-43tj
title: "Maestro parity: TaoMate host boundary"
status: open
priority: 1
type: task
labels: [capability, evidence]
parent: WD-3nod
created_at: 2026-09-26T18:42:51Z
created_by: speed
updated_at: 2026-09-26T18:43:27Z
content_hash: "sha256:c6dc955e9263f9a74e36eef584f33a97088889cca15bb9703b0280452ce6c71f"
blocks: [WD-fay0]
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

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]

## Comments
