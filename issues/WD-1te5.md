---
id: WD-1te5
title: "Thin Talker-Reasoner bridge for governed film direction"
status: closed
priority: 1
type: epic
created_at: 2026-09-19T04:14:03Z
created_by: speed
updated_at: 2026-09-19T20:44:36Z
content_hash: "sha256:20284f64e7275aaab31ad63fda98d6e08067cc158d27cc77377dc45cbec635b7"
closed_at: 2026-09-19T20:44:36Z
close_reason: "Completion gate passed: capstone WD-dd81 is accepted and merged at main commit 6fc7c61; docs contract remained within 299 lines, all four source seams were independently verified, exact pipeline test passed 11/11, independent validation passed 24/24, and scoped backlog lint plus RTM passed."
---

## Description
## Description
Build a thin, evidence-governed Talker-Reasoner bridge for wangp-dspy without
replacing the existing governed film pipeline. The first stage is a design
contract derived from three operator-selected sources:

1. the dialogue-film gap-audit lineage and current Ref2VA acceptance stack;
2. the Talker-Reasoner research synthesis (PersonaPlex/Moshi, Voxtral, Jev,
   tool-calling reasoners, and memory tradeoffs);
3. the Paivot execution pattern demonstrated by the separate GAUNTLET lane
   (one dispatcher, atomic claims, typed evidence, PM acceptance).

## Epic Outcomes
- A typed design defines how spoken/typed input becomes a route decision and,
  only when required, a governed film-generation action.
- The talker layer never claims native tool calling; structured tool calls are
  isolated behind an explicit reasoner boundary.
- The first implementation remains thin: three route labels, no durable memory
  platform, no unrestricted tool execution, and no unconsented network calls.
- Every route/action decision is auditable with hashes and provenance while
  raw prompts and raw audio remain ephemeral by default.
- Existing `Pipeline.forward()` and acceptance-bundle behavior remain
  regression-protected.

## OUT OF SCOPE
- Letta, Mem0, Cognee, Zep, or any long-term memory platform: deferred until
  the thin route/action loop is measured.
- Live PersonaPlex/Voxtral/Jev credential setup or network inference: deferred
  until the local boundary contract is accepted.
- Automatic execution of arbitrary machine commands: never belongs in the
  talker; the reasoner receives a deliberately small validated tool surface.

## Acceptance Criteria
1. An accepted design contract identifies the first vertical slice, external
   seams, typed events, failure modes, and staged rollout gates.
2. Follow-up implementation stories are individually scoped and testable.
3. The design preserves the repo's fail-closed provenance and QC doctrine.

## Design
Start with a discovery/design story, not a model integration. Create the full
implementation backlog only after the operator can review the boundary.

## Skills To Use
- `pvg` for story transitions and shared backlog operations.
- `codebase-memory` plus direct source reads when structural coverage is
  available; graph absence is not treated as proof.

## nd_contract
status: new

### evidence
- Current wangp-dspy HEAD inspected at `35201a1` on 2026-09-19.
- Current active unrelated Skill Router loop identified as `WD-fehf` before
  this epic was created.
- No existing wangp-dspy issue or source path mentions PersonaPlex, Voxtral,
  Talker-Reasoner, Letta, Mem0, Cognee, or Jev.

### proof
- [ ] Epic outcome demonstrated by an accepted design contract and a derived
  implementation backlog.

## Description
Build a thin, evidence-governed Talker-Reasoner bridge for wangp-dspy without
replacing the existing governed film pipeline. The first stage is a design
contract derived from three operator-selected sources:

1. the dialogue-film gap-audit lineage and current Ref2VA acceptance stack;
2. the Talker-Reasoner research synthesis (PersonaPlex/Moshi, Voxtral, Jev,
   tool-calling reasoners, and memory tradeoffs);
3. the Paivot execution pattern demonstrated by the separate GAUNTLET lane
   (one dispatcher, atomic claims, typed evidence, PM acceptance).
4. the fifth operator-provided whole-system synthesis covering the audio bus,
   async reasoner, response renderer, policy preflight, observability, and
   staged Redis/Postgres/Mem0-or-Cognee architecture.

## Epic Outcomes
- A typed design defines how spoken/typed input becomes a route decision and,
  only when required, a governed film-generation action.
- The talker layer never claims native tool calling; structured tool calls are
  isolated behind an explicit reasoner boundary.
- The first implementation remains thin: three route labels, no durable memory
  platform, no unrestricted tool execution, and no unconsented network calls.
- Every route/action decision is auditable with hashes and provenance while
  raw prompts and raw audio remain ephemeral by default.
- Existing `Pipeline.forward()` and acceptance-bundle behavior remain
  regression-protected.

## OUT OF SCOPE
- Letta, Mem0, Cognee, Zep, or any long-term memory platform: deferred until
  the thin route/action loop is measured.
- Live PersonaPlex/Voxtral/Jev credential setup or network inference: deferred
  until the local boundary contract is accepted.
- Automatic execution of arbitrary machine commands: never belongs in the
  talker; the reasoner receives a deliberately small validated tool surface.

## Acceptance Criteria
1. An accepted design contract identifies the first vertical slice, external
   seams, typed events, failure modes, and staged rollout gates.
2. Follow-up implementation stories are individually scoped and testable.
3. The design preserves the repo's fail-closed provenance and QC doctrine.

## Design
Start with a discovery/design story, not a model integration. Create the full
implementation backlog only after the operator can review the boundary.

## Skills To Use
- `pvg` for story transitions and shared backlog operations.
- `codebase-memory` plus direct source reads when structural coverage is
  available; graph absence is not treated as proof.

## nd_contract
status: new

### evidence
- Current wangp-dspy HEAD inspected at `35201a1` on 2026-09-19.
- Current active unrelated Skill Router loop identified as `WD-fehf` before
  this epic was created.
- No existing wangp-dspy issue or source path mentions PersonaPlex, Voxtral,
  Talker-Reasoner, Letta, Mem0, Cognee, or Jev.

### proof
- [ ] Epic outcome demonstrated by an accepted design contract and a derived
  implementation backlog.

## Description
Build a thin, evidence-governed Talker-Reasoner bridge for wangp-dspy without
replacing the existing governed film pipeline. The first stage is a design
contract derived from three operator-selected sources:

1. the dialogue-film gap-audit lineage and current Ref2VA acceptance stack;
2. the Talker-Reasoner research synthesis (PersonaPlex/Moshi, Voxtral, Jev,
   tool-calling reasoners, and memory tradeoffs);
3. the Paivot execution pattern demonstrated by the separate GAUNTLET lane
   (one dispatcher, atomic claims, typed evidence, PM acceptance).

## Epic Outcomes
- A typed design defines how spoken/typed input becomes a route decision and,
  only when required, a governed film-generation action.
- The talker layer never claims native tool calling; structured tool calls are
  isolated behind an explicit reasoner boundary.
- The first implementation remains thin: three route labels, no durable memory
  platform, no unrestricted tool execution, and no unconsented network calls.
- Every route/action decision is auditable with hashes and provenance while
  raw prompts and raw audio remain ephemeral by default.
- Existing `Pipeline.forward()` and acceptance-bundle behavior remain
  regression-protected.

## OUT OF SCOPE
- Letta, Mem0, Cognee, Zep, or any long-term memory platform: deferred until
  the thin route/action loop is measured.
- Live PersonaPlex/Voxtral/Jev credential setup or network inference: deferred
  until the local boundary contract is accepted.
- Automatic execution of arbitrary machine commands: never belongs in the
  talker; the reasoner receives a deliberately small validated tool surface.

## Acceptance Criteria
1. An accepted design contract identifies the first vertical slice, external
   seams, typed events, failure modes, and staged rollout gates.
2. Follow-up implementation stories are individually scoped and testable.
3. The design preserves the repo's fail-closed provenance and QC doctrine.

## Design
Start with a discovery/design story, not a model integration. Create the full
implementation backlog only after the operator can review the boundary.

## Skills To Use
- `pvg` for story transitions and shared backlog operations.
- `codebase-memory` plus direct source reads when structural coverage is
  available; graph absence is not treated as proof.

## nd_contract
status: new

### evidence
- Current wangp-dspy HEAD inspected at `35201a1` on 2026-09-19.
- Current active unrelated Skill Router loop identified as `WD-fehf` before
  this epic was created.
- No existing wangp-dspy issue or source path mentions PersonaPlex, Voxtral,
  Talker-Reasoner, Letta, Mem0, Cognee, or Jev.

### proof
- [ ] Epic outcome demonstrated by an accepted design contract and a derived
  implementation backlog.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-19T20:44:36Z status: open -> closed

## Links


## Comments
