---
id: WD-ft6r
title: "Add hash-scoped feedback and evaluation for Skill Router"
status: open
priority: 1
type: task
parent: WD-fehf
created_at: 2026-09-19T03:49:42Z
created_by: speed
updated_at: 2026-09-19T03:50:51Z
content_hash: "sha256:b6f532ee25074d0e11969a52cfcce1ec22e9ae74e5422b4ad2b9909a543a919f"
assignee: dev-WD-ft6r
---

## Description
## Description
Add local feedback/evaluation commands that use prompt hashes and event identities, never raw prompts, so routing quality can improve from real usage.

## USER INTENT
The operator should mark a suggestion useful, wrong, or superseded and later evaluate recurring failure patterns without exposing prompt text.

## Acceptance Criteria
1. A feedback command records verdict, optional better skill, notes, timestamp, and prompt/event hash.
2. Feedback storage is mode 0600 append-only JSONL.
3. An evaluation command joins feedback to event hashes and reports top-1 usefulness, corrections, candidate frequency, latency, and abstentions.
4. Raw prompts are never read from or written to persistent feedback/evaluation output.
5. Malformed feedback input fails loudly without corrupting existing JSONL.
6. Existing tests remain green.

## Testing Requirements
- Unit: verdict validation, append-only behavior, malformed input, join correctness.
- Integration: real events.jsonl fixture plus feedback entries produces an evaluation JSON report.

## OUT OF SCOPE
- Automatic inference of feedback.
- Changing ranking thresholds automatically.

## DIFF BUDGET
- ~3 files, under 300 changed LOC.

## Boundary Map
PRODUCES:
- /Users/speed/.codex/skill-router/feedback.py -> record_feedback(...) and evaluate(...)
- /Users/speed/.codex/skill-router/feedback.jsonl -> append-only local store

CONSUMES:
- WD-59q6: /Users/speed/.codex/skill-router/events.jsonl -> prompt_sha256, decision, duration_ms, candidates

## Skills To Use
- factory-first applies; direct implementation is allowed under the machine-global infrastructure exception.

## Delivery Requirements
- Exact commands, outputs, hashes, and AC table.

## nd_contract
status: new

### evidence
- events.jsonl exists but no feedback or evaluation command does.

### proof
- [ ] Pending implementation

## History

## Links
- Parent: [[WD-fehf]]

## Comments


## Acceptance Criteria


## Design


## Notes
## nd_contract
status: in_progress

### evidence
- Claimed 2026-09-19 from pvg loop next under the machine-global infrastructure exception; no repository worktree applies.

### proof
- [ ] Feedback implementation and tests pending.

## History
- 2026-09-19T03:50:31Z status: open -> in_progress
- 2026-09-19T03:50:31Z claimed by dev-WD-ft6r
- 2026-09-19T03:50:51Z status: in_progress -> open

## Links
- Parent: [[WD-fehf]]

## Comments
