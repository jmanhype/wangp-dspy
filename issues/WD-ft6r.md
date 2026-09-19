---
id: WD-ft6r
title: "Add hash-scoped feedback and evaluation for Skill Router"
status: in_progress
priority: 1
type: task
parent: WD-fehf
created_at: 2026-09-19T03:49:42Z
created_by: speed
updated_at: 2026-09-19T05:34:17Z
content_hash: "sha256:e7958cb76a3bb0a425169528e17844c8c40a8eec946ac38a958cde7921e7024e"
assignee: dev-WD-ft6r
follows: [WD-v4ou]
labels: [delivered]
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
## Implementation Evidence

Commands run:

```bash
cd /Users/speed/.codex/skill-router
/usr/bin/python3 -m py_compile feedback.py test_feedback.py
/usr/bin/python3 -m unittest discover -s . -p 'test_*.py' -v
pvg verify /Users/speed/.codex/skill-router/feedback.py /Users/speed/.codex/skill-router/test_feedback.py --format=text
```

Independent coordinator rerun summary:

- Python compilation: exit 0.
- Full unit discovery: 20 tests, 20 passed, 0 failures, 0 errors, exit 0.
- `pvg verify`: `VERIFY: PASSED (2 files scanned, 0 issues)`.
- `feedback.jsonl` was not pre-created; tests use isolated temporary stores, and the first real record will create the production file with mode 0600.
- WD-v4ou protected implementation hashes remained unchanged.

### CI/Test Results

```text
Ran 20 tests in 0.501s

OK
VERIFY: PASSED (2 files scanned, 0 issues)
```

Summary: added local hash-scoped feedback recording and evaluation with stable privacy-safe event IDs, append-only mode-0600 JSONL storage, symlink rejection, malformed-store fail-closed behavior, latest-verdict joins, and useful/correction/latency/abstention reporting without raw prompt persistence.

Commit SHA: 7b4b38775852e3231e9d15902c800c7fadab256862e38349c7f22f0a5c827dea

This is the SHA-256 of the machine-global delivery manifest, not a Git commit; authorized artifacts live outside the wangp-dspy Git worktree.

Final hashes:

```text
6536355d3c96ff8651a9176f6645cb54d73189b2e25c91ac3f1a3dd8fee8461f  /Users/speed/.codex/skill-router/feedback.py
300cc14fe27123c8ce6e2fbd2719955b95123964c88fda160eefb04bef830b33  /Users/speed/.codex/skill-router/test_feedback.py
2c3cd4441badce6464c5039f7c16a0f24b6f7b3b28ac8c3b40b5db56f8e1fa16  /Users/speed/.codex/skill-router/index_skills.py
273165774b1e636aa0045b402644dd05c4e8dacd218431f338d0156215776c59  /Users/speed/.codex/skill-router/hook.py
2bdf48910135eb1bbe33e2ea80e9af367bb9b92d8cfdc613175d072588c2bb9a  /Users/speed/.codex/skill-router/test_router.py
e252122986d63574fdbc91a7b5d867997946827a62a54e6e641e481f7c4729ae  /Users/speed/.codex/skill-router/events.jsonl
```

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Feedback command records verdict, optional better skill, notes, timestamp, and prompt/event hash | PASS | `record_feedback` and CLI `record`; validation/join tests. |
| 2. Storage is mode-0600 append-only JSONL | PASS | `O_APPEND`, `O_NOFOLLOW`, `fchmod(0600)`, symlink rejection, append tests. |
| 3. Evaluation joins feedback to event hashes and reports usefulness, corrections, candidate frequency, latency, abstentions | PASS | `evaluate` plus real-events fixture integration test. |
| 4. Raw prompts never appear in persistent feedback/evaluation output | PASS | only hashes; raw prompt fields rejected; report omits prompt hashes. |
| 5. Malformed feedback fails loudly without corrupting existing JSONL | PASS | full pre-append validation and unchanged-byte test. |
| 6. Existing router tests remain green | PASS | independent full discovery: 20/20 OK. |

## nd_contract
status: delivered

### evidence
- Independent coordinator reran compilation, full unittest discovery, pvg verify, privacy/mode source checks, and hash verification.
- Delivery manifest SHA-256: 7b4b38775852e3231e9d15902c800c7fadab256862e38349c7f22f0a5c827dea.

### proof
- [x] AC #1: Feedback record contains verdict/correction/notes/time and event/prompt hashes.
- [x] AC #2: Append-only mode-0600 JSONL behavior is tested.
- [x] AC #3: Event join and all required report metrics are tested.
- [x] AC #4: Raw prompts are rejected/omitted and only hashes persist.
- [x] AC #5: Malformed input fails without changing existing bytes.
- [x] AC #6: Full 20-test router+feedback discovery passes.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


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
- 2026-09-19T04:54:55Z status: open -> in_progress
- 2026-09-19T04:54:55Z auto-follows: linked to predecessor WD-v4ou
- 2026-09-19T04:54:55Z claimed by dev-WD-ft6r
- 2026-09-19T05:33:20Z status: in_progress -> in_progress

## Links
- Parent: [[WD-fehf]]
- Follows: [[WD-v4ou]]

## Comments

### 2026-09-19T03:50:51Z speed
loop: reset orphaned in_progress to open (no developer worktree found; prior session presumed dead)
