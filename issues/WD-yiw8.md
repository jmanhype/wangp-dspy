---
id: WD-yiw8
title: "Remove accidental Talker-Reasoner artifacts from wangp-dspy"
status: in_progress
priority: 1
type: task
created_at: 2026-09-20T01:58:29Z
created_by: speed
updated_at: 2026-09-20T01:59:54Z
content_hash: "sha256:77be4ef0bce1250004a175695b98c46336b77847cf5bbcbf20f4636688ad1ce1"
assignee: dev-WD-yiw8
labels: [delivered]
---

## Description
## USER INTENT

The operator clarified that Talker-Reasoner was accidentally added to wangp-dspy. This repository should remain focused on the governed film pipeline, while all Talker-Reasoner product work remains in talker-reasoner-system.

## Goal

Remove the accidental Talker-Reasoner boundary/plan documents from current wangp-dspy main without rewriting Git history.

## Context

Current affected files:

- docs/specs/talker-reasoner-bridge.md
- docs/plans/talker-reasoner-bridge.md

The canonical product repository is already established at:

https://github.com/jmanhype/talker-reasoner-system

## OUT OF SCOPE

- Rewriting Git history or deleting accepted tracker evidence: immutable history remains intact.
- Removing film-pipeline docs or findings.
- Adding a new replacement Talker-Reasoner document: none belongs in this repository.
- Importing or coupling either repository to the other.

## DIFF BUDGET

- 2 deleted files, 0 insertions.

## Boundary Map

PRODUCES:
- current main with no Talker-Reasoner implementation or planning artifacts

CONSUMES:
- (existing): docs/specs/talker-reasoner-bridge.md
  source: accidentally merged historical boundary document
- (existing): docs/plans/talker-reasoner-bridge.md
  source: accidentally merged historical plan fragment

## Acceptance Criteria

1. docs/specs/talker-reasoner-bridge.md is absent from current main.
2. docs/plans/talker-reasoner-bridge.md is absent from current main.
3. A case-insensitive repository scan finds no current Talker-Reasoner or talker-reasoner-system references.
4. The exact pipeline contract test still passes.
5. git diff --check passes.
6. Git history is not rewritten.

## Testing Requirements

- Static scan: grep for Talker-Reasoner/talker-reasoner-system/talk_reasoner.
- Regression: /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest -q tests/test_pipeline.py
- Diff hygiene: git diff --check

## MANDATORY SKILLS

- pvg: story governance and merge.

## nd_contract
status: new

### evidence
- Created after operator confirmed the Talker-Reasoner artifacts were accidental and wangp-dspy should remain film-only.

### proof
- [ ] Pending cleanup.


## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-yiw8
git grep -Ini -e 'talker-reasoner' -e 'talker_reasoner' -e 'talk_reasoner'
test ! -e docs/specs/talker-reasoner-bridge.md
test ! -e docs/plans/talker-reasoner-bridge.md
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest -q tests/test_pipeline.py
git diff --check
git diff --cached --check
git commit -m 'docs(WD-yiw8): remove accidental Talker-Reasoner artifacts'
```

### CI/Test Results

```text
current-tree Talker-Reasoner scan: PASS/no matches
targeted pipeline contract: 11 passed
git diff checks: PASS
story commit: 2 files deleted, 317 lines removed
```

Summary: the two accidentally merged Talker-Reasoner documents are removed from current wangp-dspy main. Git history was not rewritten, and the film pipeline contract remains green.

Commit SHA: e335526909595ba775d62ec662bebe1f43a3f2b6

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Spec absent | PASS | File deleted |
| 2. Plan absent | PASS | File deleted |
| 3. No current TR references | PASS | git grep returned no matches |
| 4. Pipeline contract | PASS | 11/11 passed |
| 5. Diff hygiene | PASS | Working/staged checks exit 0 |
| 6. History preserved | PASS | Ordinary deletion commit; no rewrite/rebase |

## nd_contract
status: delivered

### evidence
- Commit SHA: `e335526909595ba775d62ec662bebe1f43a3f2b6`.
- Talker-Reasoner current-tree scan: 0 matches.
- Pipeline test: 11 passed.

### proof
- [x] AC #1: spec absent.
- [x] AC #2: plan absent.
- [x] AC #3: no current references.
- [x] AC #4: pipeline test passed.
- [x] AC #5: diff checks passed.
- [x] AC #6: history not rewritten.


## History
- 2026-09-20T01:58:45Z status: open -> in_progress
- 2026-09-20T01:58:45Z claimed by dev-WD-yiw8
- 2026-09-20T01:59:53Z status: in_progress -> in_progress

## Links


## Comments
