---
id: WD-mf14
title: "Codex local agent tooling reliability"
status: closed
priority: 1
type: epic
created_at: 2026-09-19T01:54:10Z
created_by: speed
updated_at: 2026-09-19T02:24:39Z
content_hash: "sha256:6ab554e8bfbe18e4ee57e3ebbaf64481ddfd194fde5dded0f9b5426165a3b3fc"
closed_at: 2026-09-19T02:24:39Z
close_reason: "All child stories accepted; automatic local Codex skill router met the epic outcomes."
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


## History
- 2026-09-19T02:24:39Z status: open -> closed

## Links


## Comments
