---
id: WD-rb1f
title: "E2e: prepare real LF004 no-GPU content-brief plan"
status: closed
priority: 0
type: task
labels: [e2e, writing-skeleton]
parent: WD-h73w
created_at: 2026-09-20T19:46:39Z
created_by: speed
updated_at: 2026-09-20T19:48:18Z
content_hash: "sha256:c5dc6c91e9cbc755fc3b63d3e228b08c518d511af30d3705451d957ab81a93ef"
closed_at: 2026-09-20T19:48:18Z
close_reason: "Superseded: initial story body duplicated boundary sections during repair; replacement carries the corrected executable contract."
blocks: [WD-42no]
led_to: [WD-z46c]
---

## Description
## USER INTENT
A content operator wants a real brief, cast plates, and accepted voice tracks to pass through the no-GPU Content Brief Gateway and yield a reviewable run_film dry-run plan.

## Context (Embedded)
Use only repository-owned LF003 assets. Source plates are under `assets/acceptance/lf003-v3/`; accepted VibeVoice tracks are under `datasets/runs/provenance/lf003-*`. The four dialogue strings must exactly match the selected audio transcripts.

## OUT OF SCOPE
- GPU, model inference, SSH, queue submission, host preflight, or rendering.
- Changing Content Brief Gateway behavior.
- Creating a second content brief.
- Operator render approval in this story.

## DIFF BUDGET
- ~6 files, under 150 changed LOC.

## Boundary Map
PRODUCES:
- datasets/content_briefs/lf004-operator-dogfood/brief.json -> typed `wangp-dspy.content-brief/v1` input
- datasets/content_briefs/lf004-operator-dogfood/plates/ -> exactly `anchor.*`, `Tess.*`, and `Rho.*`
- datasets/content_briefs/lf004-operator-dogfood/plan.json -> canonical no-GPU content plan
- datasets/content_briefs/lf004-operator-dogfood/run/ -> script, audio guides, and run ledger
- datasets/content_briefs/lf004-operator-dogfood/review.md -> hashes, provenance, and explicit no-render status

CONSUMES:
- predict/content_brief.py -> load_content_brief(...) and build_run_film_inputs(...)
  spec: load_content_brief(path: str | Path) -> ContentBrief; build_run_film_inputs(brief: ContentBrief, plates_dir: Path, run_dir: Path) -> Mapping[str, object]
- scripts/run_content_brief.py -> main(...)
  spec: main(argv: list[str] | None = None) -> int
- assets/acceptance/lf003-v3/* -> repository-owned plates
  schema: image/png source files with accepted LF003 provenance
- datasets/runs/provenance/lf003-*/audio/*.prepared.wav -> accepted voice tracks
  schema: audio/wav files with accepted VibeVoice provenance

## Story Contract
The user can inspect one complete LF004 review packet and verify that the gateway stores a deterministic four-clip no-GPU plan.

1. Exactly one real brief uses `wangp-dspy.content-brief/v1`, two named characters, a non-placeholder premise, and four dialogue turns exactly matching selected repository-owned audio transcripts.
2. The plates directory contains exactly one `anchor.*`, one `Tess.*`, and one `Rho.*`; source and staged SHA-256 hashes are recorded.
3. Every audio path resolves inside the repository to an existing accepted WAV and each source SHA-256 is recorded.
4. The gateway emits exactly four clips with `dry_run=true`, `gpu_work=false`, and `queue_submitted=false`.
5. The run directory contains planning artifacts and a run ledger but no jobs database.
6. The review packet records brief hash, canonical plan SHA-256, run-ledger SHA-256, input hashes, repository commit, and explicit operator-review-pending/no-render status.
7. Re-running the gateway on the same inputs and repository state reproduces the canonical plan identity.
8. Existing gateway tests remain green and no pipeline source behavior changes.

## Testing Requirements
- `uv run --frozen --extra dev pytest -q tests/test_content_brief.py`
- `uv run --frozen --extra dev python scripts/run_content_brief.py --brief datasets/content_briefs/lf004-operator-dogfood/brief.json --plates datasets/content_briefs/lf004-operator-dogfood/plates --output datasets/content_briefs/lf004-operator-dogfood/plan.json --run-dir datasets/content_briefs/lf004-operator-dogfood/run`
- A recorded hash/provenance verification command covering every artifact in Story Contract #6.
- `git diff --check`

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Derived from the operator-selected one-real-render dogfood goal.

### proof
- [ ] Story #1: Real typed brief and dialogue/audio match.
- [ ] Story #2: Plate set is exact and hash-recorded.
- [ ] Story #3: Audio set is repository-owned and hash-recorded.
- [ ] Story #4: Four-clip no-GPU/no-queue plan is emitted.
- [ ] Story #5: Run side effects are limited to planning artifacts.
- [ ] Story #6: Review packet has complete provenance and no-render status.
- [ ] Story #7: Canonical replay is deterministic.
- [ ] Story #8: Existing behavior remains green.

## USER INTENT
A content operator wants a real brief, cast plates, and accepted voice tracks to pass through the no-GPU Content Brief Gateway and yield a reviewable run_film dry-run plan.

## Context (Embedded)
Use only repository-owned LF003 assets. Source plates are under `assets/acceptance/lf003-v3/`; accepted VibeVoice tracks are under `datasets/runs/provenance/lf003-*`. The four dialogue strings must exactly match the selected audio transcripts.

## OUT OF SCOPE
- GPU, model inference, SSH, queue submission, host preflight, or rendering.
- Changing Content Brief Gateway behavior.
- Creating a second content brief.
- Operator render approval in this story.

## DIFF BUDGET
- ~6 files, under 150 changed LOC.

## Boundary Map
PRODUCES:
- datasets/content_briefs/lf004-operator-dogfood/brief.json -> typed `wangp-dspy.content-brief/v1` input
- datasets/content_briefs/lf004-operator-dogfood/plates/ -> exactly `anchor.*`, `Tess.*`, and `Rho.*`
- datasets/content_briefs/lf004-operator-dogfood/plan.json -> canonical no-GPU content plan
- datasets/content_briefs/lf004-operator-dogfood/run/ -> script, audio guides, and run ledger
- datasets/content_briefs/lf004-operator-dogfood/review.md -> hashes, provenance, and explicit no-render status

CONSUMES:
- predict/content_brief.py -> load_content_brief(...) and build_run_film_inputs(...)
  spec: load_content_brief(path: str | Path) -> ContentBrief; build_run_film_inputs(brief: ContentBrief, plates_dir: Path, run_dir: Path) -> Mapping[str, object]
- scripts/run_content_brief.py -> main(...)
  spec: main(argv: list[str] | None = None) -> int
- assets/acceptance/lf003-v3/* -> repository-owned plates
  schema: image/png source files with accepted LF003 provenance
- datasets/runs/provenance/lf003-*/audio/*.prepared.wav -> accepted voice tracks
  schema: audio/wav files with accepted VibeVoice provenance

## Story Contract
The user can inspect one complete LF004 review packet and verify that the gateway stores a deterministic four-clip no-GPU plan.

1. Exactly one real brief uses `wangp-dspy.content-brief/v1`, two named characters, a non-placeholder premise, and four dialogue turns exactly matching selected repository-owned audio transcripts.
2. The plates directory contains exactly one `anchor.*`, one `Tess.*`, and one `Rho.*`; source and staged SHA-256 hashes are recorded.
3. Every audio path resolves inside the repository to an existing accepted WAV and each source SHA-256 is recorded.
4. The gateway emits exactly four clips with `dry_run=true`, `gpu_work=false`, and `queue_submitted=false`.
5. The run directory contains planning artifacts and a run ledger but no jobs database.
6. The review packet records brief hash, canonical plan SHA-256, run-ledger SHA-256, input hashes, repository commit, and explicit operator-review-pending/no-render status.
7. Re-running the gateway on the same inputs and repository state reproduces the canonical plan identity.
8. Existing gateway tests remain green and no pipeline source behavior changes.

## Testing Requirements
- `uv run --frozen --extra dev pytest -q tests/test_content_brief.py`
- `uv run --frozen --extra dev python scripts/run_content_brief.py --brief datasets/content_briefs/lf004-operator-dogfood/brief.json --plates datasets/content_briefs/lf004-operator-dogfood/plates --output datasets/content_briefs/lf004-operator-dogfood/plan.json --run-dir datasets/content_briefs/lf004-operator-dogfood/run`
- A recorded hash/provenance verification command covering every artifact in Story Contract #6.
- `git diff --check`

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Derived from the operator-selected one-real-render dogfood goal.

### proof
- [ ] Story #1: Real typed brief and dialogue/audio match.
- [ ] Story #2: Plate set is exact and hash-recorded.
- [ ] Story #3: Audio set is repository-owned and hash-recorded.
- [ ] Story #4: Four-clip no-GPU/no-queue plan is emitted.
- [ ] Story #5: Run side effects are limited to planning artifacts.
- [ ] Story #6: Review packet has complete provenance and no-render status.
- [ ] Story #7: Canonical replay is deterministic.
- [ ] Story #8: Existing behavior remains green.

## USER INTENT
A content operator wants a real brief, cast plates, and accepted voice tracks to pass through the no-GPU Content Brief Gateway and yield a reviewable run_film dry-run plan.

## Context (Embedded)
Use only repository-owned LF003 assets. Source plates are under `assets/acceptance/lf003-v3/`; accepted VibeVoice tracks are under `datasets/runs/provenance/lf003-*`. The four dialogue strings must exactly match the selected audio transcripts.

## OUT OF SCOPE
- GPU, model inference, SSH, queue submission, host preflight, or rendering.
- Changing Content Brief Gateway behavior.
- Creating a second content brief.
- Operator render approval in this story.

## DIFF BUDGET
- ~6 files, under 150 changed LOC.

## Boundary Map
PRODUCES:
- datasets/content_briefs/lf004-operator-dogfood/brief.json -> typed `wangp-dspy.content-brief/v1` input
- datasets/content_briefs/lf004-operator-dogfood/plates/ -> exactly `anchor.*`, `Tess.*`, and `Rho.*`
- datasets/content_briefs/lf004-operator-dogfood/plan.json -> canonical no-GPU content plan
- datasets/content_briefs/lf004-operator-dogfood/run/ -> script, audio guides, and run ledger
- datasets/content_briefs/lf004-operator-dogfood/review.md -> hashes, provenance, and explicit no-render status

CONSUMES:
- predict/content_brief.py -> load_content_brief(...) and build_run_film_inputs(...)
- scripts/run_content_brief.py -> main(...)
- assets/acceptance/lf003-v3/* -> repository-owned plates
- datasets/runs/provenance/lf003-*/audio/*.prepared.wav -> accepted voice tracks

## Acceptance Criteria
1. Exactly one real brief uses `wangp-dspy.content-brief/v1`, two named characters, a non-placeholder premise, and four dialogue turns exactly matching selected repository-owned audio transcripts.
2. The plates directory contains exactly one `anchor.*`, one `Tess.*`, and one `Rho.*`; source and staged SHA-256 hashes are recorded.
3. Every audio path resolves inside the repository to an existing accepted WAV and each source SHA-256 is recorded.
4. The gateway emits exactly four clips with `dry_run=true`, `gpu_work=false`, and `queue_submitted=false`.
5. The run directory contains planning artifacts and a run ledger but no jobs database.
6. The review packet records brief hash, canonical plan SHA-256, run-ledger SHA-256, input hashes, repository commit, and explicit operator-review-pending/no-render status.
7. Re-running the gateway on the same inputs and repository state reproduces the canonical plan identity.
8. Existing gateway tests remain green and no pipeline source behavior changes.

## Testing Requirements
- `uv run --frozen --extra dev pytest -q tests/test_content_brief.py`
- `uv run --frozen --extra dev python scripts/run_content_brief.py --brief datasets/content_briefs/lf004-operator-dogfood/brief.json --plates datasets/content_briefs/lf004-operator-dogfood/plates --output datasets/content_briefs/lf004-operator-dogfood/plan.json --run-dir datasets/content_briefs/lf004-operator-dogfood/run`
- A recorded hash/provenance verification command covering every artifact in AC #6.
- `git diff --check`

## nd_contract
status: new

### evidence
- Derived from the operator-selected one-real-render dogfood goal.

### proof
- [ ] AC #1: Real typed brief and dialogue/audio match.
- [ ] AC #2: Plate set is exact and hash-recorded.
- [ ] AC #3: Audio set is repository-owned and hash-recorded.
- [ ] AC #4: Four-clip no-GPU/no-queue plan is emitted.
- [ ] AC #5: Run side effects are limited to planning artifacts.
- [ ] AC #6: Review packet has complete provenance and no-render status.
- [ ] AC #7: Canonical replay is deterministic.
- [ ] AC #8: Existing behavior remains green.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-20T19:46:39Z dep_added: blocks WD-rj6e
- 2026-09-20T19:48:18Z status: open -> closed
- 2026-09-20T19:48:18Z dep_removed: no_longer_blocks WD-rj6e
- 2026-09-20T19:48:47Z dep_added: blocks WD-42no

## Links
- Parent: [[WD-h73w]]
- Blocks: [[WD-42no]]
- Led to: [[WD-z46c]]

## Comments
