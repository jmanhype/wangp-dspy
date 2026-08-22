---
id: WD-c4uh
title: "MultiShotAssembler: shot chain with continuity lock and mistake-lock"
status: open
priority: 2
type: feature
created_at: 2026-08-22T15:11:01Z
created_by: speed
updated_at: 2026-08-22T15:11:01Z
content_hash: "sha256:8218988477b8aebc85a80f9df0626c9e4e4800dcac90ba54f939d61d3eae430b"
---

## Description
Story 4 of WD-j9nx. DSPy module assembling a sequence of shots (each a RenderBrief+ProfileDecision from stories 1-2) into a continuous chain: continuity lock (subject/style descriptors carried verbatim between shots), end-state chaining (shot N+1 opens from shot N's terminal state — terminal_state field on each shot), mistake-lock (declared intentional deviations from canon/expected pinned so QC does not flag them). Dataclasses: ShotPlan (brief, decision, terminal_state, declared_deviations), AssembledChain (ordered shots + continuity digest). Validation: continuity violations typed-rejected (style flip mid-chain), undeclared deviation vs declared, empty/single-shot handling, chain length bounds. Tests: DummyLM, no GPU. Pure logic — no rendering here (WanGP adapter is story 5).

## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments
