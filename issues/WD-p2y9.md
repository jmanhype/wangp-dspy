---
id: WD-p2y9
title: "E2e: turn operator brief into validated run_film plan"
status: closed
priority: 1
type: task
parent: WD-qeh4
created_at: 2026-09-20T17:09:01Z
created_by: speed
updated_at: 2026-09-20T17:46:34Z
content_hash: "sha256:1e65dbcd7b55ae7f53a950e92d64120104a00f6b3f0d1d512046da5d02125f1e"
labels: [e2e, capstone, walking-skeleton, delivered, accepted]
was_blocked_by: [WD-073e]
assignee: dev-WD-p2y9
follows: [WD-073e]
closed_at: 2026-09-20T17:46:34Z
close_reason: "Accepted: independently verified typed brief validation, cast/plate/audio/duration checks, canonical provenance-bearing dry-run output, no queue database/GPU work, unchanged run_film behavior, and focused/full test evidence."
---

## Description
## USER INTENT
A content operator wants to describe a short dialogue piece, cast, duration policy, plates, and output destination, then receive a validated Wangp run plan without touching Python internals or spending GPU time.

## Context (Embedded)
Wangp already has deterministic `run_film` planning, typed character rosters, plate validation, Ref2VA job emission, repository identity, and dry-run behavior. The missing surface is a typed content-brief file and CLI that safely bridges into the existing planner.

## OUT OF SCOPE
- GPU rendering and queue draining: output must remain dry-run only.
- Voice generation: audio paths, when supplied, must already exist.
- UI: CLI and Python API only.
- Changing ranking, routing, prompts, or gates.

## DIFF BUDGET
- ~7 files, under 650 changed LOC.

## Boundary Map
PRODUCES:
- predict/content_brief.py -> ContentBrief, ContentBriefError, load_content_brief(path: Path) -> ContentBrief, build_run_film_inputs(brief: ContentBrief, plates_dir: Path) -> dict
- scripts/run_content_brief.py -> CLI: --brief PATH --plates PATH --output PATH [--run-dir PATH]
- scripts/run_content_brief.py -> writes a canonical JSON plan and summary without GPU/host work
- tests/test_content_brief.py -> typed schema, malformed-input, speaker, plate, dry-run, and provenance coverage
- docs/content-brief.md -> operator schema and usage documentation

CONSUMES:
- (existing): scripts/run_film.py -> run_film(script_file, plates_dir, characters, durations, audio_paths, db_path, dry_run)
- (existing): services/director/run_ledger.py -> repository_identity(repo_root=None) -> dict

## Acceptance Criteria
1. A versioned JSON brief validates required title, premise, characters, dialogue, plates, and duration policy.
2. Every dialogue speaker resolves to exactly one declared character.
3. Character names map to nonempty plate files in the provided plates directory.
4. Ordered audio paths, when present, match dialogue count and exist as files.
5. One duration per dialogue turn is either derived deterministically or supplied and validated positive.
6. The CLI invokes the existing run_film dry-run path and performs no SSH, queue, GPU, model, or network work.
7. The output plan contains the repository commit, brief hash, input paths, character roster, emitted clips, and operator summary.
8. Invalid briefs fail before creating output directories or media-guide files.
9. Existing run_film behavior remains unchanged.

## Testing Requirements
- Unit: JSON schema, normalization, hash stability, speaker/plate/audio/duration validation, output canonicalization.
- Integration: MUST invoke the real run_film dry-run function with fixture plates and temporary paths; no mocks around planning.
- E2e: a complete brief-to-plan CLI test must inspect the emitted plan and ensure no jobs database is created.
- Commands:
  - uv run --frozen --extra dev pytest -q tests/test_content_brief.py
  - uv run --frozen --extra dev pytest -q tests/test_content_brief.py tests/test_run_film_cli.py

## MANDATORY SKILLS
None identified.

## nd_contract
status: new

### evidence
- Goal requires the first operator-facing Wangp content-brief workflow.

### proof
- [ ] Pending implementation.

## Acceptance Criteria


## Design


## Notes
## PM Decision
ACCEPTED [2026-09-20]: Independently reviewed the five-file/591-line diff and reran focused gateway tests, gateway plus continuation CLI tests, the full suite, py_compile, scoped verifier, CLI help, and whitespace/static checks. The gateway invokes the existing dry-run path, emits repository-attributed canonical JSON, and creates no queue database or GPU/host work.

## nd_contract
status: accepted

### evidence
- Gateway suite: 11/11 passed.
- Gateway + CLI suite: 19/19 passed.
- Full suite: 0 errors/failures, 1 existing skip.
- Scoped verifier: 3 files, 0 issues.
- Story commit: d61e4ac0329d69c34e689bdf6fa4b366f7257317.

### proof
- [x] AC-by-AC independently verified from implementation, tests, CLI output, and Git state.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-20.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-p2y9
uv run --frozen --extra dev pytest -q tests/test_content_brief.py
uv run --frozen --extra dev pytest -q tests/test_content_brief.py tests/test_run_film_cli.py
uv run --frozen --extra dev pytest -q
pvg verify predict/content_brief.py scripts/run_content_brief.py tests/test_content_brief.py --format=text
python3 -m py_compile predict/content_brief.py scripts/run_content_brief.py tests/test_content_brief.py
uv run --frozen --extra dev python scripts/run_content_brief.py --help
git diff --check
git diff --cached --check
```

### CI/Test Results

```text
tests/test_content_brief.py: 11 passed, 0 failed, 0 skipped
content brief + continuation CLI: 19 passed, 0 failed, 0 skipped
full suite: 1,546 collected tests, 0 errors, 0 failures, 1 existing skip
pvg verify: PASSED, 3 files scanned, 0 issues
py_compile: PASS
CLI help: PASS
whitespace checks: PASS
story diff: 5 files, 591 insertions
```

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Versioned typed brief | PASS | `wangp-dspy.content-brief/v1` validates title, premise, cast, dialogue, durations, and audio shape. |
| 2. Speakers resolve exactly once | PASS | Roster uniqueness and speaker membership checks. |
| 3. Character plates resolve | PASS | Exactly one `Character.*` file is required per cast member. |
| 4. Audio paths match and exist | PASS | Relative-path resolution, count validation, and file existence tests. |
| 5. Duration policy validated | PASS | Deterministic 56-frame default or one positive finite value per turn. |
| 6. CLI invokes existing dry-run path | PASS | `run_content_brief.py` calls `run_film(..., dry_run=True)`; integration test emits four clips. |
| 7. Plan provenance/summary | PASS | Output records brief hash, repository identity, inputs, roster, dialogue, clips, duration, and explicit no-GPU/no-queue flags. |
| 8. Invalid briefs fail before side effects | PASS | Missing plate/audio tests assert run directory is not created. |
| 9. Existing run_film unchanged | PASS | Existing suite and new gateway tests pass; no run_film source changed in this story. |

Summary: added the first operator-facing typed content-brief gateway, including canonical no-GPU plan output, deterministic duration defaults, plate/audio validation, and repository provenance.

Commit SHA: d61e4ac0329d69c34e689bdf6fa4b366f7257317

## nd_contract
status: delivered

### evidence
- Focused gateway suite: 11/11 passed.
- Gateway + CLI suite: 19/19 passed.
- Full suite: 0 errors/failures, 1 existing skip.
- Scoped verifier: 3 files, 0 issues.
- Story commit: `d61e4ac0329d69c34e689bdf6fa4b366f7257317`.

### proof
- [x] AC #1: Versioned brief schema validated.
- [x] AC #2: Cast and speaker resolution validated.
- [x] AC #3: Plates resolved uniquely.
- [x] AC #4: Audio paths validated.
- [x] AC #5: Duration policy validated.
- [x] AC #6: Existing run_film dry-run path invoked without GPU/host work.
- [x] AC #7: Canonical provenance-bearing plan emitted.
- [x] AC #8: Invalid inputs fail before output side effects.
- [x] AC #9: Existing behavior preserved.

## History
- 2026-09-20T17:09:02Z dep_added: blocked_by WD-073e
- 2026-09-20T17:17:32Z dep_removed: was_blocked_by WD-073e
- 2026-09-20T17:20:19Z status: open -> in_progress
- 2026-09-20T17:20:19Z auto-follows: linked to predecessor WD-073e
- 2026-09-20T17:20:19Z claimed by dev-WD-p2y9
- 2026-09-20T17:46:15Z status: in_progress -> in_progress
- 2026-09-20T17:46:34Z status: in_progress -> closed

## Links
- Parent: [[WD-qeh4]]
- Was blocked by: [[WD-073e]]
- Follows: [[WD-073e]]

## Comments
