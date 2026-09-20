---
id: WD-z46c
title: "E2e: prepare real LF004 no-GPU content-brief plan"
status: closed
priority: 0
type: task
labels: [e2e, writing-skeleton, delivered]
parent: WD-h73w
created_at: 2026-09-20T19:48:19Z
created_by: speed
updated_at: 2026-09-20T20:14:45Z
content_hash: "sha256:3f0ee3049c55348571af29f3bc2fa505ee692c9f99932de8e5b587e06adc20e9"
assignee: dev-WD-z46c
follows: [WD-rj6e, WD-rb1f]
closed_at: 2026-09-20T20:14:45Z
close_reason: "Accepted: real four-clip no-GPU LF004 plan has complete provenance and stable canonical replay; explicit operator render approval remains required."
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

## Acceptance Criteria


## Design


## Notes
## PM Decision
ACCEPTED [2026-09-20]: Independently reviewed the 10-file/149-line LF004 packet, reran the exact gateway command, stable canonical verifier, targeted gateway tests, scoped verifier, file-count/no-jobs checks, and whitespace checks. The packet remains operator_review_pending/no_render_started. PR 147 required CI passed with CLEAN merge state.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-20.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Commands run:

- `uv run --frozen --extra dev pytest -q tests/test_content_brief.py` - 11 passed.
- Exact Content Brief Gateway replay - 4 clips, typed brief hash `sha256:67202d3597affeab4e5edcf15a1acef2f5e88ed00950ce17ff3012f5bb0472cd`, and stable canonical plan `620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8`.
- `uv run --frozen --extra dev python datasets/content_briefs/lf004-operator-dogfood/run/verify.py --canonical-sha 620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8` - status verified, replay identical.
- `pvg verify datasets/content_briefs/lf004-operator-dogfood/run/verify.py datasets/content_briefs/lf004-operator-dogfood/review.md --include-tests --format=text` - 1 file scanned, 0 issues.
- `git diff --check` and `git diff --cached --check` - pass.

### CI/Test Results

- Gateway tests: 11/11 passed.
- LF004 packet files: exactly 10.
- Dialogue turns: exactly 4.
- Plan clips: exactly 4.
- Jobs databases: 0.
- GPU/model/SSH/queue/render/host work: none.
- Two clean out-of-repository gateway replays: identical canonical plan identity.
- In-place raw plan and run-ledger hashes may change because generated files embed dirty-repository identity; the review packet records packet-generation hashes and the verifier pins only stable canonical identity.

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Real typed brief/audio | PASS | Two-character LF004 brief and four exact repository-owned transcript matches. |
| 2. Exact plate set | PASS | Only anchor.png, Tess.png, Rho.png; source/staged hashes match. |
| 3. Repository-owned audio | PASS | Four accepted WAV paths and hashes verified. |
| 4. Four no-GPU clips | PASS | dry_run=true, gpu_work=false, queue_submitted=false. |
| 5. Planning-only run directory | PASS | script/guides/ledger/verifier only; no jobs.db. |
| 6. Review provenance/status | PASS | Hashes, commit, inputs, operator_review_pending, and no_render_started recorded. |
| 7. Deterministic canonical replay | PASS | Stable canonical identity reproduced twice by verifier plus one exact in-place rerun. |
| 8. Existing behavior | PASS | Gateway tests pass with no tracked source changes. |

Summary: created the first real LF004 operator dogfood review packet while leaving render explicitly unapproved and unstarted.

Commit SHA: a0fe446f772bc2f8be723eaf9541ea61b529a314

## nd_contract
status: delivered

### evidence
- Required command outputs above.
- Commit `a0fe446f772bc2f8be723eaf9541ea61b529a314`.

### proof
- [x] AC #1: Real typed brief and dialogue/audio match.
- [x] AC #2: Plate set is exact and hash-recorded.
- [x] AC #3: Audio set is repository-owned and hash-recorded.
- [x] AC #4: Four-clip no-GPU/no-queue plan is emitted.
- [x] AC #5: Run side effects are limited to planning artifacts.
- [x] AC #6: Review packet has complete provenance and no-render status.
- [x] AC #7: Canonical replay is deterministic.
- [x] AC #8: Existing behavior remains green.

## History
- 2026-09-20T19:48:19Z dep_added: blocks WD-42no
- 2026-09-20T19:51:05Z status: open -> in_progress
- 2026-09-20T19:51:05Z auto-follows: linked to predecessor WD-rj6e
- 2026-09-20T19:51:05Z claimed by dev-WD-z46c
- 2026-09-20T20:12:30Z status: in_progress -> in_progress
- 2026-09-20T20:12:30Z auto-follows: linked to predecessor WD-rb1f
- 2026-09-20T20:14:45Z status: in_progress -> closed
- 2026-09-20T20:14:46Z dep_removed: no_longer_blocks WD-42no

## Links
- Parent: [[WD-h73w]]
- Follows: [[WD-rj6e]], [[WD-rb1f]]

## Comments
