---
id: WD-mf14
title: "Codex local agent tooling reliability"
status: closed
priority: 1
type: epic
created_at: 2026-09-19T01:54:10Z
created_by: speed
updated_at: 2026-09-19T02:24:39Z
content_hash: "sha256:98c40b7c5ab28e3682fdc0bfa132b012ff311fbed4bf4dab92929e11487a9f91"
closed_at: 2026-09-19T02:24:39Z
close_reason: "All child stories accepted; automatic local Codex skill router met the epic outcomes."
labels: [accepted]
---

## Description
## Description
Operator-facing reliability tooling for the local Codex environment. This epic keeps global agent infrastructure changes auditable through Paivot even when the runtime artifacts live under ~/.codex rather than the repository.

## Epic Outcomes
- Codex lifecycle integrations are automatic, fail-open, and measurable.
- Global hook/configuration changes preserve prior behavior and have rollback artifacts.
- Local routing remains offline by default and does not transmit prompt content.

## OUT OF SCOPE
- Jev or any network inference in the MVP router.
- Automatic execution or modification of skills.
- Importing or deriving from SkillRanker source code.

## nd_contract
status: new

### evidence
- Operator requested an automatic Codex skill router and explicitly required Paivot workflow on 2026-09-18.

### proof
- [ ] Epic outcome demonstrated by the automatic local skill-router story.

## Acceptance Criteria
1. Every global Codex tooling change in this epic is represented by a Paivot story with command evidence.
2. Hook failures never block or degrade normal Codex prompts.
3. Prompt text is never persisted by routing telemetry.

## Design
Use the native Codex UserPromptSubmit lifecycle hook, a local SQLite FTS5 index, compact advisory additionalContext, and fail-open behavior.

## Notes
Infrastructure exception: artifacts under /Users/speed/.codex are machine-global and are not carried by a wangp-dspy story branch. Rollback backups and command output are authoritative delivery evidence.

## History

## Links

## Comments


## Acceptance Criteria


## Design


## Notes
## nd_contract
status: accepted

### evidence
- Child WD-59q6 accepted and closed on 2026-09-19.
- Epic outcome demonstrated by a fail-open automatic UserPromptSubmit router, preserved existing hooks with rollback, local-only ranking, and telemetry that does not persist raw prompt text.

### proof
- [x] Every global Codex tooling change in this epic is represented by accepted Paivot story WD-59q6 with command evidence.
- [x] Hook failures fail open and do not block normal prompts.
- [x] Prompt text is not persisted by routing telemetry.

## History
- 2026-09-19T02:24:39Z status: open -> closed

## Links


## Comments
