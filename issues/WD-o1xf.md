---
id: WD-o1xf
title: "Tune Skill Router symptom specificity"
status: in_progress
priority: 0
type: task
parent: WD-dic4
created_at: 2026-09-19T02:48:59Z
created_by: speed
updated_at: 2026-09-19T02:49:20Z
content_hash: "sha256:68b263e7093fb1a1fb82b29305865754e3e671b7de9a8ae31cfb3b2fa1c4b2ad"
assignee: dev-WD-o1xf
---

## Description
## Description
Tune the local Skill Router ranking so detailed symptom descriptions outweigh broad one-token domain-name matches when a prompt also contains hook-test/meta language.

## Context
The accepted router was live-verified in a fresh Codex process. The exact injected ranking was:
1. supabase — 0.82
2. supabase-rls-frontend-debugging — 0.7407

The technical prompt contained detailed Supabase RLS symptoms, but also asked the fresh session to quote router context. Those meta terms inflated broad-body overlap and the one-token exact-name boost.

## Acceptance Criteria
1. Add a regression test using the live-style prompt: `Live hook verification: Why does my Supabase frontend show empty rows when the API returns data? First quote the exact Skill Router advisory context injected into this turn, or say NO_SKILL_ROUTER_CONTEXT if none was injected. Then answer the technical question in two sentences.`
2. On the current local index, `supabase-rls-frontend-debugging` must rank above `supabase`.
3. A short domain-focused prompt must still return a Supabase candidate.
4. All existing tests continue to pass.
5. `pvg verify` on changed source/test files reports zero issues.
6. No network calls, prompt persistence, hook registration changes, or skill execution behavior are added.

## Design
Inspect score components, then apply the smallest deterministic scoring change that favors symptom/meta overlap over a broad one-token exact-name boost. Prefer general scoring logic over hard-coding the word Supabase.

## OUT OF SCOPE
- Jev reranking.
- Embeddings.
- Automatic index refresh.
- Reopening the accepted MVP story.

## nd_contract
status: new

### evidence
- Live fresh-process output and event log recorded in WD-59q6 post-acceptance comment.

### proof
- [ ] AC #1: regression test added.
- [ ] AC #2: specific skill ranks above broad skill.
- [ ] AC #3: short prompt still suggests Supabase.
- [ ] AC #4: full router suite passes.
- [ ] AC #5: pvg verify zero issues.
- [ ] AC #6: diff contains no network/persistence/registration behavior.

## History

## Links
- Parent: [[WD-dic4]]

## Comments


## Acceptance Criteria


## Design


## Notes
## nd_contract
status: in_progress

### evidence
- Claimed 2026-09-19 under the same machine-global infrastructure exception as WD-59q6: changes are confined to /Users/speed/.codex/skill-router and no repository story worktree applies.
- Do not poll pvg loop next during implementation because the orphan-worktree heuristic resets this global-config task.

### proof
- [ ] Ranking regression and verification pending.

## History
- 2026-09-19T02:49:20Z status: open -> in_progress
- 2026-09-19T02:49:20Z claimed by dev-WD-o1xf

## Links
- Parent: [[WD-dic4]]

## Comments
