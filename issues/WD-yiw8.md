---
id: WD-yiw8
title: "Remove accidental Talker-Reasoner artifacts from wangp-dspy"
status: in_progress
priority: 1
type: task
created_at: 2026-09-20T01:58:29Z
created_by: speed
updated_at: 2026-09-20T01:58:45Z
content_hash: "sha256:402ce579b7d2d27eca2e1d7bce8d683c807e25ed83ec0d7d1b947a3e96af84c0"
assignee: dev-WD-yiw8
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


## History
- 2026-09-20T01:58:45Z status: open -> in_progress
- 2026-09-20T01:58:45Z claimed by dev-WD-yiw8

## Links


## Comments
