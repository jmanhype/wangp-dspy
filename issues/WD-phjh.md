---
id: WD-phjh
title: "Hand off Talker-Reasoner implementation to canonical repository"
status: open
priority: 1
type: task
created_at: 2026-09-19T23:53:37Z
created_by: speed
updated_at: 2026-09-19T23:53:37Z
content_hash: "sha256:23c95f40650ab267c24c502fd8b131db2ff0f5d07a72cda09d7c12914b223e2b"
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


## History


## Links


## Comments
