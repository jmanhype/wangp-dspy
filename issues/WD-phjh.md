---
id: WD-phjh
title: "Hand off Talker-Reasoner implementation to canonical repository"
status: closed
priority: 1
type: task
created_at: 2026-09-19T23:53:37Z
created_by: speed
updated_at: 2026-09-19T23:55:18Z
content_hash: "sha256:320ca40789ecb47ab0c872d406c0cc4318c809281951ce1aad44a2fe098d862d"
assignee: dev-WD-phjh
labels: [delivered]
closed_at: 2026-09-19T23:55:18Z
close_reason: "Accepted: independently verified the canonical private repository, current M1 commit f7bc6e0, tags, and the 18-line documentation-only diff. Both accepted records now clearly preserve WD-dd81 governance while directing future implementation to talker-reasoner-system. Exact pipeline test passed 11/11; diff and scoped verify passed; PR #144 records the review."
---

## Description
## USER INTENT

Keep wangp-dspy as the historical governance record for the accepted Talker-Reasoner boundary while making future implementation work discoverable in its new canonical product repository.

## Context (Embedded)

- Canonical implementation repository: https://github.com/jmanhype/talker-reasoner-system
- Canonical local checkout: `/Users/Shared/HermesWorkspace/talker-reasoner-system`
- The repository is private and its current M1 state is pushed at commit `f7bc6e0` with tags `m0-complete` and `m1-complete`.
- The internal bare remote remains configured as `backup`.
- GitHub branch protection could not be enabled because private branch protection requires GitHub Pro or public visibility; this is an operator decision, not a code defect.
- The accepted historical contracts remain:
  - `docs/specs/talker-reasoner-bridge.md`
  - `docs/plans/talker-reasoner-bridge.md`

## Goal

Add a clearly visible status/handoff note to both accepted documents. Future readers must immediately understand that implementation moved to the canonical repository while these files remain WD-dd81 governance and requirements provenance.

## OUT OF SCOPE

- Moving or deleting the accepted documents: they are historical governance evidence.
- Importing either repository from the other: the repos must remain decoupled.
- Creating M2 stories in wangp-dspy: M2 belongs in talker-reasoner-system.
- Changing live voice/model behavior: this is documentation only.

## DIFF BUDGET

- 2 files, under 30 changed LOC.

## Boundary Map

PRODUCES:
- docs/specs/talker-reasoner-bridge.md -> canonical-repository handoff status block
- docs/plans/talker-reasoner-bridge.md -> canonical-repository handoff status block

CONSUMES:
- (existing): docs/specs/talker-reasoner-bridge.md
  source: accepted WD-dd81 boundary contract
- (existing): docs/plans/talker-reasoner-bridge.md
  source: accepted WD-dd81 follow-up sequencing record

## Acceptance Criteria

1. Both accepted documents contain a prominent handoff status block naming the canonical GitHub repository.
2. Both documents state that they remain historical governance/requirements records for WD-dd81.
3. Both documents state that future implementation changes belong in talker-reasoner-system.
4. No source import, pipeline behavior, model behavior, or tracker history is removed or rewritten.
5. `git diff --check` passes.
6. The exact primary interpreter command `/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest -q tests/test_pipeline.py` passes from the story worktree.

## Testing Requirements

- Static/diff: `git diff --check`
- Contract regression: `/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest -q tests/test_pipeline.py`
- Evidence review: independently confirm the canonical repository URL and current M1 commit/tag state.

## MANDATORY SKILLS

- pvg: story governance and merge transitions.

## Delivery Requirements

- Record both changed document hashes.
- Paste exact test and diff command results.
- Include an AC verification table.

## nd_contract
status: new

### evidence
- Created after promoting talker-reasoner-system to GitHub and verifying M1 at `f7bc6e0`.

### proof
- [ ] Pending documentation handoff.


## Acceptance Criteria


## Design


## Notes


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-phjh
git diff --check
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest -q tests/test_pipeline.py
pvg verify docs/specs/talker-reasoner-bridge.md docs/plans/talker-reasoner-bridge.md --format=text
shasum -a 256 docs/specs/talker-reasoner-bridge.md docs/plans/talker-reasoner-bridge.md
git add docs/specs/talker-reasoner-bridge.md docs/plans/talker-reasoner-bridge.md
git diff --cached --check
git commit -m 'docs: hand off Talker-Reasoner implementation'
cd /Users/Shared/HermesWorkspace/talker-reasoner-system
git status --short --branch
git remote -v
git rev-parse HEAD
git ls-remote --tags origin m0-complete m1-complete
```

Material state:

- Documentation commit: `3fe976b`
- Base: `6fc7c61`
- Changed files:
  - `docs/specs/talker-reasoner-bridge.md` (+9 lines)
  - `docs/plans/talker-reasoner-bridge.md` (+9 lines)
- Total change: 18 inserted lines, within the under-30 budget.
- Spec SHA-256: `7957f12c0ab67798a98063d75e46126cdf7d5cc6aca28dc734df5725dfa95fd8`
- Plan SHA-256: `bbf262ad0d48768c9cfb98fdb8d9264169e3626b2b518738605688b5eea1026b`
- Canonical repository verified as private `jmanhype/talker-reasoner-system`, default branch `main`, URL `https://github.com/jmanhype/talker-reasoner-system`.
- Canonical M1 commit verified at `f7bc6e076dfaff20f7389c84f8077da3dd5756ab`.
- No imports, source code, model behavior, pipeline behavior, or accepted tracker history were removed.

### CI/Test Results

```text
git diff --check: PASS
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest -q tests/test_pipeline.py:
...........                                                              [100%]
11 passed
1 pre-existing host/wangp_adapter.py SyntaxWarning

pvg verify docs/specs/talker-reasoner-bridge.md docs/plans/talker-reasoner-bridge.md:
VERIFY: PASSED (0 files scanned, 0 issues)

git diff --cached --check: PASS
```

Summary: the accepted WD-dd81 contract and plan now carry a prominent canonical-repository handoff status while remaining historical governance records in wangp-dspy. Future implementation work is directed to talker-reasoner-system without coupling the repositories.

Commit SHA: 3fe976b

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Both documents name canonical repo | PASS | Spec and plan both link `https://github.com/jmanhype/talker-reasoner-system` |
| 2. Historical governance status explicit | PASS | Spec: accepted boundary contract; plan: accepted historical planning record |
| 3. Future implementation directed correctly | PASS | Both status blocks say future implementation belongs in Talker-Reasoner repository |
| 4. No source/history rewrite | PASS | Only 18 documentation status lines changed |
| 5. Diff check | PASS | Working and staged checks exited 0 |
| 6. Pipeline contract test | PASS | Exact command passed 11/11 |

## nd_contract
status: delivered

### evidence
- Commit SHA: `3fe976b`.
- Spec SHA-256: `7957f12c0ab67798a98063d75e46126cdf7d5cc6aca28dc734df5725dfa95fd8`.
- Plan SHA-256: `bbf262ad0d48768c9cfb98fdb8d9264169e3626b2b518738605688b5eea1026b`.
- Exact pipeline test: 11 passed.

### proof
- [x] AC #1: Canonical repository named in both documents.
- [x] AC #2: Historical governance role stated in both documents.
- [x] AC #3: Future implementation ownership stated in both documents.
- [x] AC #4: No source, behavior, or history removed.
- [x] AC #5: Diff checks passed.
- [x] AC #6: Exact pipeline command passed.


## History
- 2026-09-19T23:53:45Z status: open -> in_progress
- 2026-09-19T23:53:45Z claimed by dev-WD-phjh
- 2026-09-19T23:54:33Z status: in_progress -> in_progress
- 2026-09-19T23:55:18Z status: in_progress -> closed

## Links


## Comments
