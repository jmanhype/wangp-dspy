---
id: WD-o6z4
title: "Cut v0.1.0: verify in the primary checkout and publish the release"
status: in_progress
priority: 1
type: task
labels: [release, hygiene]
created_at: 2026-09-22T21:16:11Z
created_by: speed
updated_at: 2026-09-22T21:21:39Z
content_hash: "sha256:f4456061dbe1ab663d9863b849911958fc0aae0f4452f154e39b7da22cf1c14b"
assignee: dev-WD-o6z4
---

## Description
## USER INTENT
Observable outcome: v0.1.0 is a real, verifiable release: `wgp release verify` reports `release=ready` in the primary checkout (not only in a throwaway clone), an annotated `v0.1.0` tag exists on the released commit with written release notes, and a GitHub release publishes those notes. Today the tag is still merely "tag-ready".

## Context (Embedded)
- Verified today at main 5a8f4d4: a clean clone reports all four checks `pass`, `tag-ready=v0.1.0`, `tag_created=false`, `release=ready`. The primary checkout at the same commit reports `check=tree status=failed` with `untracked embedded repository or opaque directory changes are not safely hashable: <repo>/.claude/worktrees/dev-WD-3nwm`.
- Cause: `.gitignore` lists `.paivot/` but not `.claude/`, so the dispatcher's story worktrees under `.claude/worktrees/` are untracked embedded repositories. Repository identity fails closed on them by design, which is correct behaviour for opaque directories and must not be weakened.
- `.claude/` is local agent/dispatcher tooling, not harness source, and is already excluded from release inputs in spirit; ignoring it lets the release check run where developers actually work without touching the fail-closed rule for anything else.
- `docs/RELEASE_NOTES_v0.1.0.md` and the `## [0.1.0]` changelog entry already exist; the release notes cover install, the no-GPU lane, the content front door, the capability report, recipes and release verification.

## OUT OF SCOPE
- Weakening `repository_identity` or its refusal to hash opaque untracked directories: only the tooling directory is ignored.
- Publishing to PyPI or any registry, and any credential use.
- Rewriting release notes for an already published version, or any renderer/queue/provenance/QC/gate/recipe semantics change.

## DIFF BUDGET
- Roughly 2 files, under 30 authored changed LOC.

## Boundary Map
PRODUCES:
- .gitignore -> an entry that ignores the local `.claude/` dispatcher/worktree tooling directory, with a comment explaining why.
- tests/test_release.py -> a regression assertion that the primary checkout's release verification is not blocked by that tooling directory (for example by asserting the ignore rule exists and that a tree containing an ignored `.claude/` path still reports a clean tree), without weakening the fail-closed rule for non-ignored opaque directories.
CONSUMES:
- wangp/release.py -> `_tree_check` and `repository_identity` semantics stay unchanged.
- docs/RELEASE_NOTES_v0.1.0.md -> the notes published with the tag.

## Required Outcomes
1. `wgp release verify` in the primary checkout reports `version`, `changelog`, `recipe_schema` and `tree` all `pass` with `release=ready` and `tag_created=false`.
2. The fail-closed behaviour is preserved: any other untracked opaque directory (not the ignored tooling path) still fails the tree check, proven by a test.
3. An annotated tag `v0.1.0` is created on the released main commit and pushed, and a GitHub release publishes `docs/RELEASE_NOTES_v0.1.0.md`.
4. Nothing else changes: no version bump, no new dependency, no publication to a registry, no credential.

## Testing Requirements
- Real-process, no mocks: `uv run --frozen --extra dev pytest tests/test_release.py -q` and the full `uv run --frozen --extra dev pytest -q`.
- Evidence must include `wgp release verify` output from the primary checkout at the released commit.
- The tag and release creation is performed by the dispatcher after acceptance and must be recorded in the story notes.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must paste the primary-checkout release verification before and after, the regression test output, and the full-suite result into notes, plus an AC verification table.
- Developer must use `pvg story deliver`.
- No GPU, SSH, model inference, registry publication, or credential use is authorized; the story branch and its PR are the only push target. The tag push and GitHub release are dispatcher actions after acceptance.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-22T21:21:39Z status: open -> in_progress
- 2026-09-22T21:21:39Z claimed by dev-WD-o6z4

## Links


## Comments
