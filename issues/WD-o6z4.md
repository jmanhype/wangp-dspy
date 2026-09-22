---
id: WD-o6z4
title: "Cut v0.1.0: verify in the primary checkout and publish the release"
status: closed
priority: 1
type: task
labels: [release, hygiene, accepted]
created_at: 2026-09-22T21:16:11Z
created_by: speed
updated_at: 2026-09-22T21:42:39Z
content_hash: "sha256:75cb947d8ec532023bfd19d18bfc80522d435b7df94dd2289edf72f9f90cf68e"
assignee: dev-WD-o6z4
closed_at: 2026-09-22T21:42:39Z
close_reason: "Accepted: story SHA 32de795 has the exact two-file scoped diff; .claude/ ignore mechanism and fail-closed opaque-tree regression passed; focused/full suites and CI passed; primary checkout is restored to main 91f4f8e."
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


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-22.

### proof
- [x] Story closed after accepted label was applied.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-22.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence
Summary: Ignore only local dispatcher/worktree tooling under `.claude/`, prove primary-checkout release readiness at the story commit, and preserve opaque-tree fail-closed behaviour; PR #161. The annotated tag push and GitHub release remain dispatcher actions after acceptance.
Commands run:
- `uv run --frozen --extra dev pytest tests/test_release.py -q` -> exit 0; 6 passed.
- `uv run --frozen --extra dev pytest -q` -> exit 0; 1,676 passed, 0 failed, 1 live-3090 probe skipped because GPU/SSH was out of scope.
- Primary checkout before change: `uv run --frozen --extra dev wgp release verify` -> exit 2; version/changelog/recipe_schema pass, tree failed on `.claude/worktrees/dev-WD-3nwm`, `release=not_ready`.
- Primary checkout at story commit: `uv run --frozen --extra dev wgp release verify` -> exit 0; all four checks pass, `tag_created=false`, `release=ready`.
- `git diff main..HEAD --name-only` -> `.gitignore`, `tests/test_release.py`.
- `git push origin story/WD-o6z4` -> pushed `32de79578d428f6d014dfc8e518932404d652fbf`.
- `gh pr create --base main --head story/WD-o6z4 ...` -> https://github.com/jmanhype/wangp-dspy/pull/161.
- `gh api repos/jmanhype/wangp-dspy/commits/32de79578d428f6d014dfc8e518932404d652fbf/check-runs` -> 1/1 completed; `test=success`.
- `pvg verify .gitignore tests/test_release.py --format=text` -> PASSED, 0 issues.
SHA: 32de79578d428f6d014dfc8e518932404d652fbf

### CI/Test Results
- Focused release suite: 6/6 passed; exit 0.
- Full suite: 1,677 collected, 1,676 passed, 0 failed, 1 skipped; exit 0. The skip is `tests/test_jobs_integration_3090.py:20`, gated on `WANGP_3090=1`, and was not enabled because this story forbids GPU/SSH.
- GitHub check-run: `test` completed with `success`.
- BEFORE in `/Users/Shared/HermesWorkspace/wangp-dspy`: `check=tree status=failed`; opaque `.claude/worktrees/dev-WD-3nwm`; `release=not_ready`; exit 2.
- AFTER in the same primary path at story SHA `32de79578d428f6d014dfc8e518932404d652fbf`: version/changelog/recipe_schema/tree all `pass`; `tag_created=false`; `release=ready`; exit 0. For this read-only proof, primary was transiently detached at the story commit and restored to `main` at `91f4f8ebb202f1b5f8dab6b6503b8f9d767b8894`; final primary status returned to `?? .claude/`.

### AC Verification
| AC | Result | Evidence |
| 1 | PASS | `.gitignore` adds only the commented `.claude/` local agent-tooling rule; `git diff main..HEAD --name-only` shows exactly `.gitignore` and `tests/test_release.py`. |
| 2 | PASS | Primary verifier before: tree failed/not ready; after at story SHA: all four checks pass, `tag_created=false`, `release=ready`. |
| 3 | PASS | `tests/test_release.py::test_ignored_agent_tooling_does_not_weaken_opaque_tree_failure` proves ignored `.claude/` remains ready while a non-ignored embedded repository fails closed; focused suite 6/6 passed. |
| 4 | PASS | No version, dependency, release implementation, tag, or GitHub release change; `tag_created=false`, and tag/release remain dispatcher actions. |

## nd_contract
status: delivered

### evidence
- PR: https://github.com/jmanhype/wangp-dspy/pull/161
- Commit: 32de79578d428f6d014dfc8e518932404d652fbf
- Tests: focused 6/6 PASS; full suite exit 0 with 1,676 PASS, 0 FAIL, 1 out-of-scope GPU/SSH-gated skip.
- CI: `test` check-run completed `success`.
- Primary release verify before/after recorded above; primary was restored to main after the proof.

### proof
- [x] AC #1: Only `.claude/` is ignored, with a local-agent-tooling comment and exactly two changed files.
- [x] AC #2: Primary verification changes from tree-failed/not-ready to all-checks-pass/release-ready with no tag created.
- [x] AC #3: Regression proves ignored tooling does not block verification while another untracked embedded repository still fails closed.
- [x] AC #4: Scope remains two files with no version bump, dependency, tag creation, or release publication.

## History
- 2026-09-22T21:21:39Z status: open -> in_progress
- 2026-09-22T21:21:39Z claimed by dev-WD-o6z4
- 2026-09-22T21:36:30Z status: in_progress -> in_progress
- 2026-09-22T21:42:39Z status: in_progress -> closed

## Links


## Comments
