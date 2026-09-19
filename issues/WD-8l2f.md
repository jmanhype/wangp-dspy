---
id: WD-8l2f
title: "Allow valid per-frame mouth motion before SyncNet"
status: in_progress
priority: 0
type: bug
parent: WD-j9nx
created_at: 2026-09-19T16:32:57Z
created_by: speed
updated_at: 2026-09-19T16:50:49Z
content_hash: "sha256:cc0ec80f9f045c3bd4a7e3f876d6238c6d4397ad1cc969a3db71eb1a18591db6"
assignee: dev-WD-8l2f
follows: [WD-v66o, WD-sf9i]
blocks: [WD-rij6]
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


## History
- 2026-09-19T16:33:08Z status: open -> in_progress
- 2026-09-19T16:33:08Z auto-follows: linked to predecessor WD-v66o
- 2026-09-19T16:33:08Z claimed by dev-WD-8l2f
- 2026-09-19T16:33:09Z dep_added: blocks WD-rij6
- 2026-09-19T16:50:49Z status: in_progress -> in_progress
- 2026-09-19T16:50:49Z auto-follows: linked to predecessor WD-sf9i

## Links
- Parent: [[WD-j9nx]]
- Blocks: [[WD-rij6]]
- Follows: [[WD-v66o]], [[WD-sf9i]]

## Comments
