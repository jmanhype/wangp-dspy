---
id: WD-p2y9
title: "E2e: turn operator brief into validated run_film plan"
status: open
priority: 1
type: task
parent: WD-qeh4
created_at: 2026-09-20T17:09:01Z
created_by: speed
updated_at: 2026-09-20T17:09:01Z
content_hash: "sha256:7caa1e68eaa302a120746dc7e856fe7ea4658025f9354fa66b2034b17ac79a6c"
labels: [e2e, capstone, walking-skeleton]
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


## History


## Links
- Parent: [[WD-qeh4]]

## Comments
