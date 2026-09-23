---
id: WD-v6xp
title: "Emit the spend-gate decision row from the production QC seam (fail-open)"
status: open
priority: 1
type: task
parent: WD-as25
created_at: 2026-09-21T12:19:33Z
created_by: speed
updated_at: 2026-09-23T16:02:18Z
content_hash: "sha256:d68491e4a30b0939707a2ebf7c742b2a448ee79141dd36d4771279431756a6c7"
---

## Description

## Description
## Context (Embedded)
WD-l48s delivered the spend-gate outcome corpus, the leakage-safe replay harness, and a standalone post-run recorder (`training/spend_gate.py::write_live_row` / `write_completed_run_rows`). Its Required Outcome 9 also named a production QC-completion seam. That seam was deliberately NOT implemented there, and the story was amended accordingly: a recording hook inside the QC loop must not be able to fail a render attempt, and `services/` must not depend on `training/`.

## USER INTENT
Every future render should emit a decision-ready spend-gate row without a human remembering to run a post-processing step, while the render itself stays exactly as safe as it is today.

## Required properties
1. After QC completes for a clip, the production path emits the normalized decision row (same schema as the WD-l48s corpus rows) without changing any gate, retry, timing, or state decision.
2. The seam is strictly fail-open for the render: any recording failure is caught, counted in a typed way, and can never alter job state, failure_count, retry admission, or ordering. Recording must not raise into the QC path.
3. No import of `training/` from `services/` (layering): either the writer moves to a dependency-free services-side module that `training/` also consumes, or an equivalent design that keeps the dependency direction clean. State the choice and why.
4. The emitted row must be byte-identical (canonical JSON) to what `write_live_row` produces for the same evidence, proved against the existing LF004 recovery run.

## Required Outcomes
1. A simulated recording failure during QC leaves job state, failure_count, and retry admission identical to the same run without recording, and records the failure in a typed counter.
2. For the LF004 recovery run's clips, the production-emitted row equals the standalone recorder's row byte-for-byte.
3. No gate, retry, renderer, policy, or QC threshold source changes; `git diff --exit-code main -- services/director/renderers qc/` exits 0 and the only `services/` change is the emit path.
4. Tests: unit for the fail-open counter plus a real integration test that emits from the actual QC completion path against real evidence, with no mocks.

## OUT OF SCOPE
- Re-rendering or host work: this is a recording seam; lands never.
- Corpus/replay changes: owned by WD-l48s, already delivered.
- Gate or retry semantics: unchanged and unchangeable here.
- Backfilling historical rows: the WD-l48s corpus already covers the recorded runs.

## DIFF BUDGET
- ~3-5 files, under 300 changed LOC.

## Testing Requirements
- Unit: fail-open behavior on recording error; canonical-row equality against the standalone recorder.
- Integration: MANDATORY, no mocks; drive the real QC completion path over existing evidence and assert the row plus unchanged run state.
- Commands: `uv run --frozen --extra dev pytest -q` and `git diff --check`.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Created 2026-09-21 as the deferred half of WD-l48s Required Outcome 9, after independent review rejected implementing it in that story.

### proof
- [ ] Pending implementation

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-as25]]

## Comments

## Context (Embedded)
WD-l48s delivered the spend-gate outcome corpus, the leakage-safe replay harness, and a standalone post-run recorder (`training/spend_gate.py::write_live_row` / `write_completed_run_rows`). Its Required Outcome 9 also named a production QC-completion seam. That seam was deliberately NOT implemented there, and the story was amended accordingly: a recording hook inside the QC loop must not be able to fail a render attempt, and `services/` must not depend on `training/`.

## USER INTENT
Every future render should emit a decision-ready spend-gate row without a human remembering to run a post-processing step, while the render itself stays exactly as safe as it is today.

## Required properties
1. After QC completes for a clip, the production path emits the normalized decision row (same schema as the WD-l48s corpus rows) without changing any gate, retry, timing, or state decision.
2. The seam is strictly fail-open for the render: any recording failure is caught, counted in a typed way, and can never alter job state, failure_count, retry admission, or ordering. Recording must not raise into the QC path.
3. No import of `training/` from `services/` (layering): either the writer moves to a dependency-free services-side module that `training/` also consumes, or an equivalent design that keeps the dependency direction clean. State the choice and why.
4. The emitted row must be byte-identical (canonical JSON) to what `write_live_row` produces for the same evidence, proved against the existing LF004 recovery run.

## Acceptance Criteria
1. A simulated recording failure during QC leaves job state, failure_count, and retry admission identical to the same run without recording, and records the failure in a typed counter.
2. For the LF004 recovery run's clips, the production-emitted row equals the standalone recorder's row byte-for-byte.
3. No gate, retry, renderer, policy, or QC threshold source changes; `git diff --exit-code main -- services/director/renderers qc/` exits 0 and the only `services/` change is the emit path.
4. Tests: unit for the fail-open counter plus a real integration test that emits from the actual QC completion path against real evidence, with no mocks.

## OUT OF SCOPE
- Re-rendering or host work: this is a recording seam; lands never.
- Corpus/replay changes: owned by WD-l48s, already delivered.
- Gate or retry semantics: unchanged and unchangeable here.
- Backfilling historical rows: the WD-l48s corpus already covers the recorded runs.

## DIFF BUDGET
- ~3-5 files, under 300 changed LOC.

## Testing Requirements
- Unit: fail-open behavior on recording error; canonical-row equality against the standalone recorder.
- Integration: MANDATORY, no mocks; drive the real QC completion path over existing evidence and assert the row plus unchanged run state.
- Commands: `uv run --frozen --extra dev pytest -q` and `git diff --check`.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Created 2026-09-21 as the deferred half of WD-l48s Required Outcome 9, after independent review rejected implementing it in that story.

### proof
- [ ] Pending implementation

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-as25]]

## Comments
