---
id: WD-4wio
title: "Make LF003 fixture portability test primary-checkout safe"
status: open
priority: 1
type: task
created_at: 2026-09-20T02:09:52Z
created_by: speed
updated_at: 2026-09-20T02:09:52Z
content_hash: "sha256:c5c291277d3c98173c6482a2d238bb5026575f51b34f64d61d7bcbf04e93460a"
---

## Description
## USER INTENT

The LF003 fixture-portability suite must pass both in the canonical primary checkout and in a fresh temporary worktree.

## Root Cause

`tests/test_lf003_fixture_manifest.py::test_lf003_jobs_db_fixture_rebases_embedded_paths` assumes the manifest’s recorded source root always differs from the current repository root. In the canonical checkout they are the same, so staging is intentionally a no-op rebase, but the test still asserts that the source root is absent.

## Goal

Keep the strong rebase assertion for fresh worktrees while allowing the valid same-root no-op case in the canonical checkout.

## OUT OF SCOPE

- Changing production code.
- Changing fixture bytes or the evidence manifest.
- Weakening manifest hash/size validation.

## DIFF BUDGET

- 1 test file, under 10 changed LOC.

## Boundary Map

PRODUCES:
- tests/test_lf003_fixture_manifest.py -> primary-checkout-safe fixture portability assertion

CONSUMES:
- (existing): tests/lf003_fixtures.py
  spec: `stage_lf003_jobs_db(destination: Path, *, fixtures: LF003FixtureSet) -> dict`

## Acceptance Criteria

1. The test still asserts fresh-worktree rebase removes the recorded source root when it differs from `ROOT`.
2. The test accepts the valid case where the recorded source root equals `ROOT`.
3. The test still asserts the current `ROOT` appears in staged clips.
4. The targeted fixture test passes from the primary checkout.
5. The complete suite passes from the primary checkout.
6. `git diff --check` passes.

## Testing Requirements

- /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest -q tests/test_lf003_fixture_manifest.py
- /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest -q
- git diff --check

## MANDATORY SKILLS

- pvg: story governance and merge.

## nd_contract
status: new

### evidence
- Primary-checkout full suite failed one test after unrelated docs/ignore cleanup; investigation showed old root and current root were identical.

### proof
- [ ] Pending test repair.


## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments
