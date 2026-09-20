---
id: WD-vlj5
title: "Ignore Paivot and Obsidian runtime state in wangp-dspy"
status: open
priority: 2
type: task
created_at: 2026-09-20T02:04:36Z
created_by: speed
updated_at: 2026-09-20T02:04:36Z
content_hash: "sha256:776318866b209e8dc5399c39f0461d41849c62b65e0aca961c78f0789e43c6a7"
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


## History


## Links


## Comments
