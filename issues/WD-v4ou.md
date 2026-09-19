---
id: WD-v4ou
title: "Keep the Skill Router index automatically fresh"
status: in_progress
priority: 1
type: task
parent: WD-fehf
created_at: 2026-09-19T03:49:42Z
created_by: speed
updated_at: 2026-09-19T04:54:26Z
content_hash: "sha256:692b6453a2c3dce5ac70a15a5eaa5760de58b785891aea32e8f1a835874823d9"
assignee: dev-WD-v4ou
labels: [delivered]
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
## Implementation Evidence

Commands run:

```bash
cd /Users/speed/.codex/skill-router
/usr/bin/python3 -m py_compile index_skills.py hook.py test_router.py
/usr/bin/python3 -m unittest discover -s . -p 'test_*.py' -v
pvg verify /Users/speed/.codex/skill-router/index_skills.py /Users/speed/.codex/skill-router/hook.py /Users/speed/.codex/skill-router/test_router.py --format=text
stat -f '%Sp %N' skills.sqlite3
```

Independent coordinator rerun summary:

- Python compilation: exit 0.
- Unit discovery: 17 tests, 17 passed, 0 failures, 0 errors, exit 0.
- `pvg verify`: `VERIFY: PASSED (3 files scanned, 0 issues)`.
- SQLite permissions: `-rw------- skills.sqlite3` (mode 0600).
- SQLite quick check: `ok`.
- Metadata schema version: `2`.
- Indexed skills: 394; manifest sources: 410; included sources: 394.

## CI/Test Results

```text
Ran 17 tests in 0.542s

OK
VERIFY: PASSED (3 files scanned, 0 issues)
```

Summary: implemented bounded local automatic index freshness with stat-first
change detection, hash verification only after stat changes, atomic rebuild for
changed/new/deleted/corrupt/missing/legacy databases, fail-open errors, a 1.25s
internal freshness budget, preserved explicit invocation and privacy behavior,
and regression coverage for all four freshness failure/refresh classes.

Commit SHA: 4440262f1268f13789e35f8dc5c06e24e125795cb849bb37315dd3565ab318d1

This is the SHA-256 of the machine-global delivery manifest, not a Git commit;
the authorized story artifacts live outside the wangp-dspy Git worktree.

Final artifact hashes:

```text
2c3cd4441badce6464c5039f7c16a0f24b6f7b3b28ac8c3b40b5db56f8e1fa16  /Users/speed/.codex/skill-router/index_skills.py
273165774b1e636aa0045b402644dd05c4e8dacd218431f338d0156215776c59  /Users/speed/.codex/skill-router/hook.py
2bdf48910135eb1bbe33e2ea80e9af367bb9b92d8cfdc613175d072588c2bb9a  /Users/speed/.codex/skill-router/test_router.py
794f81a71abfb8c079cd3e3231612d58e9fded8d6c1347ebaf907a35f022a1df  /Users/speed/.codex/skill-router/skills.sqlite3
e252122986d63574fdbc91a7b5d867997946827a62a54e6e641e481f7c4729ae  /Users/speed/.codex/skill-router/events.jsonl
6f9154a47f5f8433a43b07128b1c613254351bb29fc6cc00366db0d6644ae506  /Users/speed/.codex/hooks.json
3149400147f1d2e81069030f7e2eaf6bda5aee372e188f1659f0166dac63b815  /Users/speed/.codex/skill-router/config.json
```

## AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Freshness check sends no user prompt over the network | PASS | Freshness API receives config/index paths, not prompt text; network-denial test passes. |
| 2. Changed/new skill searchable by next hook | PASS | `test_automatic_refresh_reindexes_changed_and_new_skills`. |
| 3. Unchanged skills not reindexed every prompt | PASS | `test_unchanged_sources_do_not_rebuild_or_rehash`; stat-only current check. |
| 4. Corrupt/missing DB rebuilt safely or hook fails open | PASS | `test_corrupt_and_missing_database_are_rebuilt_safely`; quick check `ok`. |
| 5. Errors stay within hook budget and fail open | PASS | Internal 1.25s budget; error test; prior measured full hook 0.4138s. |
| 6. Mode 0600 and deduplication preserved | PASS | Mode `-rw-------`; 410 manifest sources, 394 included after deduplication. |
| 7. Existing and new router tests pass | PASS | Independent rerun: 17/17 OK. |


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-18.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-19T04:41:33Z status: open -> in_progress
- 2026-09-19T04:41:33Z claimed by dev-WD-v4ou
- 2026-09-19T04:53:12Z status: in_progress -> open
- 2026-09-19T04:53:42Z status: open -> in_progress

## Links
- Parent: [[WD-fehf]]

## Comments

### 2026-09-19T04:53:12Z speed
loop: reset orphaned in_progress to open (no developer worktree found; prior session presumed dead)
