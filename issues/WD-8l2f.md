---
id: WD-8l2f
title: "Allow valid per-frame mouth motion before SyncNet"
status: closed
priority: 0
type: bug
parent: WD-j9nx
created_at: 2026-09-19T16:32:57Z
created_by: speed
updated_at: 2026-09-19T16:52:14Z
content_hash: "sha256:ee16e3e79a9bbee42048a7e0f695cee448c9664e714eb45770935cf4080a05b6"
assignee: dev-WD-8l2f
follows: [WD-v66o, WD-sf9i]
labels: [accepted]
closed_at: 2026-09-19T16:52:13Z
close_reason: "Accepted: independently reran core targeted suites, focused moving/diagnostic tests, compilation, pvg verify, git diff check, semantic scan, and hash inspection. Valid per-frame motion is descriptive evidence; malformed boxes, identity/speaker gates, median SyncNet input, and blocking SyncNet behavior remain enforced."
led_to: [WD-2p52, WD-rij6]
---

## Description
## Context (Embedded)

Accepted `WD-v66o` at main commit `0c409d3` recovered exact per-frame mouth
locations for preserved LF003 cut 3.

### Diagnostic facts

Artifact:

`datasets/diagnostics/WD-v66o/lf003-cut3-per-frame-localizer-diagnostic.json`

SHA-256:

`bb6f0c97ed24cbada1a19c7e352d2ccd1bbc07bbb2594765d802d6cce19e8664`

Preserved cut-3 video SHA-256:

`08acf7d3601b3489e15ddf76e6f50d741a9d6550b04cc784f29cb952fbe9b47d`

Identity scores:

```text
mouth_activity: 0.95
action_match: 0.9
speaker_attribution: 0.95
```

Frame-ordered localizer boxes:

```text
start   [0.315, 0.205, 0.025, 0.015]
middle  [0.310, 0.190, 0.020, 0.030]
end     [0.270, 0.190, 0.020, 0.010]
```

Each box came from a separate per-frame request and every per-frame attempt
succeeded once.

The current integrated still-frame gate rejects those valid boxes because
their x-centers spread `0.0475`, exceeding the historical `0.03` consensus
limit. The y-center spread is only `0.0175`.

The existing SyncNet diagnostic using the per-coordinate median box
`[0.310, 0.190, 0.020, 0.015]` passed:

```text
confidence: 3.166184
offset: -1 frame at 25 fps / -0.04 seconds
model SHA-256: 961e8696f888fce4f3f3a6c3d5b3267cf5b343100b238e79b2659bff2c605442
```

## Failure boundary

The historical center-spread rule predates the accepted per-frame localizer.
It treats frame-to-frame mouth/head movement as if three boxes were repeated
measurements of one static frame. With true per-frame localization, motion is
expected. The still-frame vision gate should validate each box and preserve
the median for SyncNet; it should no longer block solely because distinct
frames show distinct mouth positions.

This is not a request to relax SyncNet or hide disagreement. Temporal
audiovisual alignment remains a blocking SyncNet responsibility. Identity and
speaker attribution also remain blocking still-frame responsibilities.

## USER INTENT

Allow natural per-frame mouth motion while still rejecting malformed boxes,
wrong identity/speaker attribution, and temporally unsynchronized speech.

## Goal

Update `run_vision_judge()` so exact three valid per-frame boxes produce a
median SyncNet input even when their centers move. Record center spread as
descriptive evidence rather than using it as a static-frame pass/fail rule.
Validate the change against the preserved LF003 cut-3 diagnostic.

## Proposed semantics

Keep blocking:

1. missing/not-exactly-three boxes;
2. malformed or non-numeric boxes;
3. non-finite, negative, zero-area, or out-of-frame boxes;
4. `action_match` or `speaker_attribution` below the existing pass bar.

Stop blocking solely on:

```text
max center spread > 0.03
```

Compute and persist the x/y center spreads and the median box so reviewers can
still inspect motion. Then pass the median box to the unchanged blocking
SyncNet gate.

## OUT OF SCOPE

- Re-rendering cut 3.
- Rendering cut 4 or assembling a film.
- Weakening identity, speaker-attribution, Whisper, SyncNet confidence, or
  SyncNet offset thresholds.
- Adding a larger static center-spread threshold.
- Deriving or synthesizing a fourth box.
- Latent carry or first-frame preservation.
- Changing the per-frame localizer implementation.

## DIFF BUDGET

- ~3 files, under 220 changed LOC.

## Boundary Map

PRODUCES:
- `qc/audio_critic/vision_judge.py` -> valid per-frame boxes are accepted with
  motion recorded descriptively; malformed boxes still fail closed.
- `qc/audio_critic/vision_judge.py` -> `VisionJudgeEvidence` preserves center
  spreads and median box for SyncNet.
- tests -> moving valid boxes pass shape validation; malformed values still
  fail; SyncNet remains the temporal authority.

CONSUMES:
- accepted `WD-v66o` diagnostic at main `0c409d3`.
- existing unchanged `run_av_sync_gate(...)` contract.

## Acceptance Criteria

1. Exactly three finite, normalized, positive-area, in-frame boxes remain
   mandatory.
2. Malformed, wrong-count, non-numeric, non-finite, out-of-range, zero-area,
   or frame-escaping boxes still fail closed.
3. Valid moving boxes from the LF003 diagnostic no longer fail the still-frame
   consensus check.
4. x/y center spreads and the median box are recorded in evidence.
5. `action_match` and `speaker_attribution` pass bars are unchanged.
6. A model-free moving-box fixture passes vision shape validation and supplies
   the exact median `[0.310, 0.190, 0.020, 0.015]` to a fake SyncNet judge.
7. A fake SyncNet failure still blocks the integrated path even when moving
   vision boxes are valid.
8. Existing vision, local-judge, ref2va, executor, and LF003 evidence tests
   remain green after updating the stale static-consensus expectation.
9. A diagnostic replay from the accepted WD-v66o artifact proves current-source
   vision accepts the three recorded boxes and reports the recorded spreads.
10. `git diff --check` passes.

## Testing Requirements

- Unit: valid motion, every malformed family, median derivation, spread
  evidence, and unchanged pass bars.
- Integration: vision result feeding a fake SyncNet judge, both pass and fail.
- Diagnostic replay: use recorded WD-v66o responses/boxes; no model call,
  render, queue mutation, cut 4, or assembly.
- Commands: targeted vision/local-judge/ref2va/executor/LF003 tests and
  `git diff --check`.

## Skills To Use

- `pvg` for story governance.
- `tool-systematic-debugging` before changing gate semantics.

## Delivery Requirements

- Exact test output.
- Diagnostic replay hashes and spread values.
- AC table.
- Story commit SHA.

## nd_contract
status: new

### evidence
- Derived from accepted WD-v66o diagnostic at main `0c409d3`.

### proof
- [ ] Pending implementation

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-19.

### proof
- [x] Story closed after accepted label was applied.


## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-8l2f
git diff --check
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m py_compile qc/audio_critic/vision_judge.py tests/test_vision_judge.py
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest -q tests/test_vision_judge.py tests/test_local_qwen_vision_judge.py tests/test_modelscope_vision_judge.py tests/test_ref2va_runtime.py tests/test_jobs_executor.py
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest -q tests/test_av_sync_gate.py -k 'not live_calibration'
pvg verify qc/audio_critic/vision_judge.py tests/test_vision_judge.py --include-tests --format=text
```

Independent coordinator results:

- `git diff --check`: exit 0.
- Compilation: exit 0.
- Independent core targeted suite: 93 tests passed.
- Focused moving/diagnostic/SyncNet tests: 3/3 passed.
- `pvg verify`: passed with 2 files scanned and zero issues.
- Worker’s expanded checkout-local evidence suite: 176/176 passed, zero skipped, using temporarily copied untracked fixtures that were removed afterward.
- Diagnostic replay used accepted WD-v66o artifact SHA-256 `bb6f0c97ed24cbada1a19c7e352d2ccd1bbc07bbb2594765d802d6cce19e8664` and preserved video SHA-256 `08acf7d3601b3489e15ddf76e6f50d741a9d6550b04cc784f29cb952fbe9b47d`.
- Replay result: vision passed with center spreads `[0.0475, 0.0175]`; median SyncNet box remains `[0.310, 0.190, 0.020, 0.015]`; `av_sync_verified=false`.

### CI/Test Results

```text
independent core targeted suite: 93 passed
focused moving/diagnostic/SyncNet tests: 3 passed
worker expanded evidence suite: 176 passed
pvg verify: PASSED (2 files scanned, 0 issues)
```

Summary: valid per-frame mouth movement no longer fails the still-frame gate solely on center spread. Exact three-box shape/range validation, identity/speaker pass bars, median-box derivation, and blocking SyncNet authority remain unchanged; x/y motion is preserved as evidence.

Commit SHA: 794fdcb

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Exact three valid boxes mandatory | PASS | Validation tests retained. |
| 2. Malformed/out-of-range/zero-area/frame-escaping boxes fail | PASS | Expanded parameterization. |
| 3. Valid LF003 moving boxes pass still-frame validation | PASS | Moving-box and diagnostic replay tests. |
| 4. Center spreads and median box recorded | PASS | `speaker_mouth_center_spread` evidence assertions. |
| 5. Action/speaker pass bars unchanged | PASS | Semantic scan and low-alignment test. |
| 6. Moving fixture supplies exact median to fake SyncNet | PASS | Captured fake SyncNet kwargs test. |
| 7. Fake SyncNet failure still blocks | PASS | Integrated QC failure test. |
| 8. Existing targeted suites green | PASS | 93 independent and 176 worker evidence tests. |
| 9. WD-v66o diagnostic replay uses recorded hashes/spreads | PASS | Replay test and hashes above. |
| 10. `git diff --check` passes | PASS | Exit 0. |

Non-AC discovery: fresh story worktrees cannot run the full LF003/SyncNet evidence suites because required preserved media/fixtures are untracked in the primary checkout. This is filed separately and does not alter WD-8l2f.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-19T16:33:08Z status: open -> in_progress
- 2026-09-19T16:33:08Z auto-follows: linked to predecessor WD-v66o
- 2026-09-19T16:33:08Z claimed by dev-WD-8l2f
- 2026-09-19T16:33:09Z dep_added: blocks WD-rij6
- 2026-09-19T16:50:49Z status: in_progress -> in_progress
- 2026-09-19T16:50:49Z auto-follows: linked to predecessor WD-sf9i
- 2026-09-19T16:52:14Z status: in_progress -> closed
- 2026-09-19T16:52:14Z dep_removed: no_longer_blocks WD-rij6

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-v66o]], [[WD-sf9i]]
- Led to: [[WD-2p52]], [[WD-rij6]]

## Comments
