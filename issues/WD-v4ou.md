---
id: WD-v4ou
title: "Keep the Skill Router index automatically fresh"
status: open
priority: 1
type: task
parent: WD-fehf
created_at: 2026-09-19T03:49:42Z
created_by: speed
updated_at: 2026-09-19T04:53:12Z
content_hash: "sha256:e7b4ed2184f36416e58be9950fe5119349cee4ff4ef64986787c4a37b6086df4"
assignee: dev-WD-v4ou
---

## Description
## Description
Ensure installed or edited SKILL.md files are reflected without a manual indexer invocation, while keeping every UserPromptSubmit invocation fast and fail-open.

## USER INTENT
The operator should never remember to rebuild the local skill index after installing or changing skills.

## Acceptance Criteria
1. Index freshness is checked without sending the user prompt over the network.
2. A changed or newly added SKILL.md becomes searchable by the next hook invocation or a bounded background/session-start refresh.
3. Unchanged skills are not reindexed on every prompt.
4. A corrupt or missing database is rebuilt safely or the hook fails open.
5. Index-refresh errors never block or delay ordinary prompting beyond the existing 2-second hook budget.
6. Automatic refresh preserves database mode 0600 and deduplication behavior.
7. Existing router tests continue to pass with new freshness tests.

## Testing Requirements
- Unit: mtime/hash freshness detection, changed/new skill reindex, unchanged no-op, corrupt database behavior.
- Integration: alter a temporary skill file, invoke hook, verify new content is searchable.
- Commands: full unittest discovery and pvg verify on changed files.

## OUT OF SCOPE
- Watching filesystem continuously.
- Network calls.
- Reindexing on every prompt.

## DIFF BUDGET
- ~3 files, under 250 changed LOC.

## Boundary Map
PRODUCES:
- /Users/speed/.codex/skill-router/index_skills.py -> freshness/manifest API used by hook
- /Users/speed/.codex/skill-router/hook.py -> bounded automatic refresh before ranking

CONSUMES:
- WD-59q6: /Users/speed/.codex/skill-router/index_skills.py -> skill_records(...) and build_database(...)

## Skills To Use
- factory-first applies to implementation routing; direct implementation is allowed under the machine-global security-sensitive infrastructure exception.

## Delivery Requirements
- Exact test/verify outputs, hashes, and AC table in nd.

## nd_contract
status: new

### evidence
- Current index was manually built at 2026-09-18; no freshness mechanism exists.

### proof
- [ ] Pending implementation

## History

## Links
- Parent: [[WD-fehf]]

## Comments


## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-19T04:41:33Z status: open -> in_progress
- 2026-09-19T04:41:33Z claimed by dev-WD-v4ou
- 2026-09-19T04:53:12Z status: in_progress -> open

## Links
- Parent: [[WD-fehf]]

## Comments
