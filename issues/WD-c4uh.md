---
id: WD-c4uh
title: "MultiShotAssembler: shot chain with continuity lock and mistake-lock"
status: closed
priority: 2
type: feature
created_at: 2026-08-22T15:11:01Z
created_by: speed
updated_at: 2026-08-22T16:42:23Z
content_hash: "sha256:a4a91656a0d9670c8b93840f341ddf285efc41954181da205cb797b808ccdd98"
assignee: dev-WD-c4uh
---

## Description
Story 4 of WD-j9nx. DSPy module assembling a sequence of shots (each a RenderBrief+ProfileDecision from stories 1-2) into a continuous chain: continuity lock (subject/style descriptors carried verbatim between shots), end-state chaining (shot N+1 opens from shot N's terminal state — terminal_state field on each shot), mistake-lock (declared intentional deviations from canon/expected pinned so QC does not flag them). Dataclasses: ShotPlan (brief, decision, terminal_state, declared_deviations), AssembledChain (ordered shots + continuity digest). Validation: continuity violations typed-rejected (style flip mid-chain), undeclared deviation vs declared, empty/single-shot handling, chain length bounds. Tests: DummyLM, no GPU. Pure logic — no rendering here (WanGP adapter is story 5).

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-22T15:47:08Z status: open -> in_progress
- 2026-08-22T15:47:08Z claimed by dev-WD-c4uh
- 2026-08-22T15:47:08Z status: in_progress -> in_progress
- 2026-08-22T16:42:23Z status: in_progress -> closed

## Links


## Comments
