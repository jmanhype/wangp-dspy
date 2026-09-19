---
id: WD-mf14
title: "Codex local agent tooling reliability"
status: open
priority: 1
type: epic
created_at: 2026-09-19T01:54:10Z
created_by: speed
updated_at: 2026-09-19T01:54:10Z
content_hash: "sha256:61343f91a685eea96bbeeed15f4bbe84bc272e83c0d2653309afd3be753833f1"
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


## Links


## Comments
