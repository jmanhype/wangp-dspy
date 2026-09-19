---
id: WD-8tkc
title: "Add local Skill Router health and quality reports"
status: closed
priority: 1
type: task
parent: WD-fehf
created_at: 2026-09-19T03:49:43Z
created_by: speed
updated_at: 2026-09-19T05:44:51Z
content_hash: "sha256:4c7b8bc0498a471bd5be4d55068eaea62fc75f5e210d5f5f8f74f9533295a1c9"
assignee: dev-WD-8tkc
follows: [WD-ft6r, WD-v4ou]
labels: [delivered, accepted]
closed_at: 2026-09-19T05:44:51Z
close_reason: "Accepted: independently reran compilation, full 23-test discovery, pvg verify, both report CLI formats, real-artifact aggregation, JSON privacy probe, and hash verification. Missing feedback is honestly degraded; no raw prompts/secrets are emitted; prior accepted router artifacts remain unchanged."
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
## Implementation Evidence

Commands run:

```bash
cd /Users/speed/.codex/skill-router
/usr/bin/python3 -m py_compile report.py test_report.py
/usr/bin/python3 -m unittest discover -s . -p 'test_*.py' -v
pvg verify /Users/speed/.codex/skill-router/report.py /Users/speed/.codex/skill-router/test_report.py --format=text
/usr/bin/python3 report.py
/usr/bin/python3 report.py --format json
```

Independent coordinator rerun summary:

- Python compilation: exit 0.
- Full unit discovery: 23 tests, 23 passed, 0 failures, 0 errors, exit 0.
- `pvg verify`: `VERIFY: PASSED (2 files scanned, 0 issues)`.
- Real report status is honestly `degraded` because feedback.jsonl is absent.
- Real report covers 24 events, 18 suggestions, 6 abstentions, latency statistics, candidate frequency, 4 explicit invocations, zero feedback records, current freshness, SQLite quick-check `ok`, 394 indexed skills / 410 manifest rows, hash-only privacy, and local-only disabled network mode.
- JSON parsed successfully and exposed no raw prompt or prompt-hash fields.
- All five previously accepted router/feedback implementation hashes remained unchanged.

### CI/Test Results

```text
Ran 23 tests in 0.617s

OK
VERIFY: PASSED (2 files scanned, 0 issues)
```

Summary: added a local Skill Router health/quality report CLI with human Markdown and machine JSON output, aggregate latency/decision/candidate/explicit/feedback/freshness/database/privacy/network sections, and honest degraded handling for missing artifacts without raw prompt or secret exposure.

Commit SHA: ee1cebc1a85f01ce15cc93ec4f17853d5f7e289346ee830d7f9eb8a96b800809

This is the SHA-256 of the machine-global delivery manifest, not a Git commit; authorized artifacts live outside the wangp-dspy Git worktree.

Final hashes:

```text
02c459c9b9f037d316402343af2a0e46a76dcf32177304350c2cd377598e284a  /Users/speed/.codex/skill-router/report.py
a9b45bbc78f40f532e791e94712c179390791b67f3de9ee3a576e022860cf35b  /Users/speed/.codex/skill-router/test_report.py
2c3cd4441badce6464c5039f7c16a0f24b6f7b3b28ac8c3b40b5db56f8e1fa16  /Users/speed/.codex/skill-router/index_skills.py
273165774b1e636aa0045b402644dd05c4e8dacd218431f338d0156215776c59  /Users/speed/.codex/skill-router/hook.py
2bdf48910135eb1bbe33e2ea80e9af367bb9b92d8cfdc613175d072588c2bb9a  /Users/speed/.codex/skill-router/test_router.py
6536355d3c96ff8651a9176f6645cb54d73189b2e25c91ac3f1a3dd8fee8461f  /Users/speed/.codex/skill-router/feedback.py
300cc14fe27123c8ce6e2fbd2719955b95123964c88fda160eefb04bef830b33  /Users/speed/.codex/skill-router/test_feedback.py
```

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Report command emits human Markdown and machine JSON | PASS | Real CLI rerun in both formats; JSON parse passed. |
| 2. Report includes events, decisions, latency, candidates, explicit invocations, feedback, freshness, database integrity, privacy/network mode | PASS | Real report output above. |
| 3. Missing artifacts degrade rather than crash | PASS | `test_missing_and_malformed_artifacts_degrade_without_crashing`; real missing feedback yields `degraded`. |
| 4. Report contains no raw prompts or secrets | PASS | Real JSON privacy probe and full test suite. |
| 5. Existing tests remain green | PASS | Independent full discovery: 23/23 OK. |


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
- 2026-09-19T05:44:51Z status: in_progress -> closed

## Links
- Parent: [[WD-fehf]]
- Follows: [[WD-ft6r]], [[WD-v4ou]]

## Comments
