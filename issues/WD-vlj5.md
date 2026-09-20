---
id: WD-vlj5
title: "Ignore Paivot and Obsidian runtime state in wangp-dspy"
status: in_progress
priority: 2
type: task
created_at: 2026-09-20T02:04:36Z
created_by: speed
updated_at: 2026-09-20T02:06:54Z
content_hash: "sha256:1582c6d84a0ae207c1e797085d3d2466bc176b5a338bace070c80ec303a2568e"
assignee: dev-WD-vlj5
labels: [delivered]
---

## Description
## USER INTENT

Keep wangp-dspy main clean while Paivot and Obsidian maintain local runtime state during multi-session work.

## Goal

Ignore generated Paivot runtime files and volatile Obsidian UI state, while preserving repository-owned project content and the shared live nd vault.

## Current Findings

Local dirt:

```text
 M .gitignore
 M .vault/.obsidian/workspace.json
?? .vault/knowledge/
```

`.gitignore` changes identify generated Paivot runtime paths:

```text
.vault/issues/
.vault/.nd.yaml
.vault/.piv-loop-state.json
.vault/.piv-loop-snapshot.json
.vault/.dispatcher-state.json
.vault/.vlt.lock
.vault/.guard/
```

`.vault/.obsidian/workspace.json` changes only record UI `lastOpenFiles`.

`.vault/knowledge/.settings.yaml` currently contains generated default project-vault settings.

## OUT OF SCOPE

- Moving or changing the shared live nd vault under `.git/paivot/nd-vault`.
- Deleting local knowledge notes.
- Changing Paivot behavior.
- Committing volatile UI state.

## DIFF BUDGET

- About 2 files changed: .gitignore additions and removal of workspace.json from the tracked tree.

## Boundary Map

PRODUCES:
- .gitignore -> generated Paivot/vault runtime exclusions
- repository tree without volatile .vault/.obsidian/workspace.json

CONSUMES:
- (existing): .gitignore
  source: repository ignore policy
- (existing): .vault/.obsidian/workspace.json
  source: accidentally tracked volatile Obsidian UI state

## Acceptance Criteria

1. Generated Paivot runtime paths are ignored.
2. Volatile `.vault/.obsidian/workspace.json` is ignored and absent from the current Git tree.
3. Generated `.vault/knowledge/.settings.yaml` is ignored.
4. Durable vault knowledge files remain eligible for explicit tracking.
5. `git check-ignore` proves the intended paths.
6. After checkout/merge, `git status --short` is clean.
7. `git diff --check` passes.

## Testing Requirements

- git check-ignore -v for all runtime paths
- git status --short
- git diff --check

## MANDATORY SKILLS

- pvg: story governance and merge.

## nd_contract
status: new

### evidence
- Local runtime dirt observed after story merges and audited before cleanup.

### proof
- [ ] Pending hygiene implementation.


## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-vlj5
git rm --cached .vault/.obsidian/workspace.json
git check-ignore -v .vault/issues/issue.md
git check-ignore -v .vault/.nd.yaml
git check-ignore -v .vault/.piv-loop-state.json
git check-ignore -v .vault/.piv-loop-snapshot.json
git check-ignore -v .vault/.dispatcher-state.json
git check-ignore -v .vault/.vlt.lock
git check-ignore -v .vault/.guard/guard.json
git check-ignore -v .vault/.obsidian/workspace.json
git check-ignore -v .vault/knowledge/.settings.yaml
git check-ignore -q .vault/knowledge/durable-note.md
git status --short
git diff --check
git diff --cached --check
```

### CI/Test Results

```text
runtime ignore checks: all 9 paths matched expected rules in .vault/.gitignore
durable knowledge example: not ignored / eligible for explicit tracking
story worktree after commit: clean
git diff checks: PASS
```

Summary: generated Paivot runtime exclusions already live in `.vault/.gitignore`; this story adds volatile Obsidian workspace and generated project-vault settings exclusions there, removes the workspace file from the tracked tree, and preserves explicit tracking eligibility for durable knowledge notes.

Commit SHA: 3bbc31d3f8d7556b2096927947847961f77a9c4e

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Paivot runtime paths ignored | PASS | Existing `.vault/.gitignore` rules verified for all 7 generated paths |
| 2. Volatile workspace ignored/untracked | PASS | File removed from index; ignore rule added |
| 3. Generated settings ignored | PASS | `.vault/knowledge/.settings.yaml` rule added |
| 4. Durable knowledge remains trackable | PASS | Example durable note not ignored |
| 5. check-ignore proof | PASS | All expected rules reported |
| 6. Story checkout clean | PASS | `git status --short` empty after commit |
| 7. Diff hygiene | PASS | `git diff --check` exit 0 |

## nd_contract
status: delivered

### evidence
- Commit SHA: `3bbc31d3f8d7556b2096927947847961f77a9c4e`.
- 9 runtime ignore checks passed.
- Durable knowledge remains eligible.

### proof
- [x] AC #1 through #7 verified.


## History
- 2026-09-20T02:04:55Z status: open -> in_progress
- 2026-09-20T02:04:55Z claimed by dev-WD-vlj5
- 2026-09-20T02:06:54Z status: in_progress -> in_progress

## Links


## Comments
