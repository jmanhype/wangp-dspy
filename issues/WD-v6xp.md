---
id: WD-v6xp
title: "Emit the spend-gate decision row from the production QC seam (fail-open)"
status: closed
priority: 1
type: task
parent: WD-as25
created_at: 2026-09-21T12:19:33Z
created_by: speed
updated_at: 2026-09-23T17:43:30Z
content_hash: "sha256:5eeeeba4b72ef8a98e0e70724b1b262a4110211c0320fb1991e3d824dee9333a"
assignee: dev-WD-v6xp
follows: [WD-l48s]
labels: [delivered]
closed_at: 2026-09-23T17:43:30Z
close_reason: "Accepted: exact-head f813fc1 passes CI; 21/21 targeted and 1993/1993 full tests; four LF004 digests match standalone; forced write failure preserves queue outcome and increments spend_gate_recording_write_error."
---

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


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence
Summary: Moved the canonical spend-gate writer from `training/spend_gate.py` to `services/jobs/spend_gate.py` (Git rename similarity 94%), kept `training/spend_gate_replay.py` as the training-side consumer, and added a default fail-open `SpendGateRecorder` call immediately after QC accepts a clip in `JobExecutor._qc_clips`. This is the preferred layering option: production owns its dependency-free row writer while training consumes that service; there is no `services/` -> `training/` import (asserted by AST test). The canonical normalization/writer code is shared rather than duplicated, so bytes remain identical. No gate, retry, renderer, policy, QC threshold, or protected engine semantics changed.

Commands run:
- `uv run --frozen --extra dev pytest tests/test_spend_gate.py tests/test_spend_gate_production_seam.py -q --junitxml=/tmp/wd-v6xp-targeted.xml` -> exit 0; JUnit parsed: tests=21 failures=0 errors=0 skipped=0 time=6.341s.
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-v6xp-full.xml` -> exit 0; JUnit parsed: tests=1993 failures=0 errors=0 skipped=1 time=697.652s. The only skip is pre-existing `tests.test_jobs_integration_3090::test_live_preflight_against_3090`, explicitly gated on `WANGP_3090=1`; it was not enabled because this story forbids host/GPU work.
- `uv run --frozen --extra dev python /tmp/wd_v6xp_proof.py` -> exit 0; all four LF004 production/standalone digest pairs matched exactly:
  - clip 1: production=b42ec90923da982bc027d0411d78bc2047bef32d26693f06c8ff5d06abcc45c5, standalone=b42ec90923da982bc027d0411d78bc2047bef32d26693f06c8ff5d06abcc45c5
  - clip 2: production=68a731eec9d483e3163c2b3662ce0cf54bf94f6eb9a19c2ce35f9c9f09fcd7e6, standalone=68a731eec9d483e3163c2b3662ce0cf54bf94f6eb9a19c2ce35f9c9f09fcd7e6
  - clip 3: production=4c5288724065500b1ffe1ed8e6a2546417d298054caa93ef3a826b8ba12c009a, standalone=4c5288724065500b1ffe1ed8e6a2546417d298054caa93ef3a826b8ba12c009a
  - clip 4: production=b68ae4d8782d396be6b22ecadfd986d28d515aea75441a008bd12b0a09588ac8, standalone=b68ae4d8782d396be6b22ecadfd986d28d515aea75441a008bd12b0a09588ac8
- Fail-open proof at the same two-clip QC completion path: successful recording and forced recording failure both produced `state=done`, `failure_count=0`, `failure_class=null`, `retryable=true`, `dead_letter=false`, clip order `[1,2]`, and clip states `[done,done]`. Forced writer failure produced typed counter `spend_gate_recording_write_error=2` and no spend-gate row.
- `git diff --exit-code main -- services/director/renderers qc/` -> exit 0.
- `git diff --exit-code main -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py` -> exit 0.
- `git diff --check` -> exit 0.
- `pvg verify scripts/build_spend_gate_corpus.py services/jobs/executor.py services/jobs/spend_gate.py training/spend_gate_replay.py tests/test_spend_gate.py tests/test_spend_gate_production_seam.py --format=text` -> exit 0; `VERIFY: PASSED (6 files scanned, 0 issues)`.
- `uv build --out-dir /tmp/wd-v6xp-build.i9fln6` -> exit 0; exactly one wheel (`wangp_dspy-0.1.0-py3-none-any.whl`) and one sdist (`wangp_dspy-0.1.0.tar.gz`).
- Changed-file numstat: `scripts/build_spend_gate_corpus.py` 1+/1-; `services/jobs/executor.py` 17+/6-; `training => services/jobs/spend_gate.py` 43+/2-; `tests/test_spend_gate.py` 2+/2-; `tests/test_spend_gate_production_seam.py` 200+/0-; `training/spend_gate_replay.py` 1+/1-.
- PR: https://github.com/jmanhype/wangp-dspy/pull/179
SHA: f813fc1adbfffdc327d7471255e47c43c156ebd6

### CI/Test Results
- GitHub check run `test` at exact head `f813fc1adbfffdc327d7471255e47c43c156ebd6`: status=completed, conclusion=success; run 35892843617 / job 107289311485, 2026-09-23T17:02:05Z -> 2026-09-23T17:22:11Z.
- Local full suite retained the pre-existing FastAPI/Starlette `StarletteDeprecationWarning` already disclosed on WD-l48s; no new warning was introduced. The only skip is the pre-existing host-gated 3090 probe and was not enabled under this no-host story.

### AC Verification
| AC | Result | Evidence |
|---|---|---|
| 1: simulated recording failure is typed, fail-open, and leaves state/failure/retry admission/order unchanged | PASS | `tests/test_spend_gate_production_seam.py::test_recording_failure_is_typed_and_fail_open`; `...::test_forced_recording_failure_preserves_queue_and_retry_admission`; measured identical outcomes and `spend_gate_recording_write_error=2` |
| 2: LF004 production rows equal standalone recorder rows byte-for-byte | PASS | `...::test_production_qc_rows_match_standalone_lf004_recorder`; all four SHA-256 pairs listed above are equal |
| 3: no gate/retry/renderer/policy/QC threshold changes; renderer/QC and protected files unchanged | PASS | both required `git diff --exit-code` commands exited 0; services changes are limited to moved writer and executor emit seam |
| 4: unit fail-open counter plus real integration from actual QC completion path over real evidence, no mocks | PASS | real `JobExecutor._qc_clips`, real `JobQueue`, real LF004 sidecars/media metadata, and the real canonical writer; only the required failure simulation injects the designed recorder dependency |

## nd_contract
status: delivered

### evidence
- Implementation, tests, build, LF004 byte digests, fail-open comparison, protected-path checks, PR #179, and successful exact-head CI recorded above.

### proof
- [x] AC #1: recording failure is caught and counted as `SpendGateRecordingFailure.WRITE` without changing queue state, failure count, retry admission, clip order, or clip status.
- [x] AC #2: all four LF004 recovery-row production/standalone digest pairs are byte-identical.
- [x] AC #3: renderer/QC-path and five protected engine-file diffs against main are clean.
- [x] AC #4: unit fail-open coverage and real no-mock QC-completion integration coverage pass with the full suite.

## History


- 2026-09-23T16:02:19Z dep_added: blocks WD-l48s
- 2026-09-23T16:33:59Z status: open -> in_progress
- 2026-09-23T16:33:59Z auto-follows: linked to predecessor WD-l48s
- 2026-09-23T16:33:59Z claimed by dev-WD-v6xp
- 2026-09-23T17:23:47Z status: in_progress -> in_progress
- 2026-09-23T17:43:30Z status: in_progress -> closed
- 2026-09-23T17:43:30Z dep_removed: no_longer_blocks WD-l48s

## Links
- Parent: [[WD-as25]]
- Follows: [[WD-l48s]]

## Comments
