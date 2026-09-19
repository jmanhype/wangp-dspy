---
id: WD-8tkc
title: "Add local Skill Router health and quality reports"
status: in_progress
priority: 1
type: task
parent: WD-fehf
created_at: 2026-09-19T03:49:43Z
created_by: speed
updated_at: 2026-09-19T05:44:02Z
content_hash: "sha256:9cdbc56413f3c52ec20ca28ec9ac4dd6463a0abeea249a5f88ebe4e5a165b87a"
assignee: dev-WD-8tkc
follows: [WD-ft6r, WD-v4ou]
labels: [delivered]
---

## Description
## Description
Add a report CLI that summarizes router operation, latency, decisions, candidates, feedback, freshness, and configuration without network access.

## USER INTENT
The operator should diagnose router health and quality with one local command.

## Acceptance Criteria
1. Report command emits human Markdown and machine JSON.
2. Report includes event counts, decision counts, latency statistics, top candidates, explicit invocation counts, feedback counts, freshness state, database integrity, and privacy/network mode.
3. Missing artifacts are reported as degraded rather than crashing.
4. Report does not include raw prompts or secrets.
5. Existing tests remain green.

## Testing Requirements
- Unit: aggregate calculations and degraded paths.
- Integration: report over current real artifacts produces both formats.

## OUT OF SCOPE
- Dashboard server.
- Remote telemetry.

## DIFF BUDGET
- ~2 files, under 250 changed LOC.

## Boundary Map
PRODUCES:
- /Users/speed/.codex/skill-router/report.py -> build_report(...)

CONSUMES:
- WD-59q6: events.jsonl and skills.sqlite3
- Feedback task: feedback.jsonl and evaluation API

## Skills To Use
- factory-first applies; direct implementation is allowed under the machine-global infrastructure exception.

## Delivery Requirements
- Exact outputs and hashes.

## nd_contract
status: new

### evidence
- Current README has no report command.

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
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-19T05:35:15Z status: open -> in_progress
- 2026-09-19T05:35:15Z auto-follows: linked to predecessor WD-ft6r
- 2026-09-19T05:35:15Z claimed by dev-WD-8tkc
- 2026-09-19T05:44:02Z status: in_progress -> in_progress
- 2026-09-19T05:44:02Z auto-follows: linked to predecessor WD-v4ou

## Links
- Parent: [[WD-fehf]]
- Follows: [[WD-ft6r]], [[WD-v4ou]]

## Comments
