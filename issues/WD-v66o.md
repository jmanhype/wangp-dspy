---
id: WD-v66o
title: "Recover exact three-frame LF003 mouth localization"
status: closed
priority: 0
type: bug
parent: WD-j9nx
created_at: 2026-09-19T15:36:38Z
created_by: speed
updated_at: 2026-09-19T16:18:32Z
content_hash: "sha256:245abb834b2b01e941f5c89d45904038ee84abd625ac01009e7dfd015fc39508"
assignee: dev-WD-v66o
follows: [WD-sf9i, WD-ice0]
labels: [accepted]
closed_at: 2026-09-19T16:18:31Z
close_reason: "Accepted: independently reran compilation, 87 targeted tests, git diff --check, diagnostic/hash inspection, and forbidden-material scan. Per-frame localization is bounded and evidence-complete; unchanged integrated consensus correctly failed closed, while diagnostic SyncNet passed. No threshold was weakened."
led_to: [WD-8l2f, WD-2p52, WD-rij6]
---

## Description
## Context (Embedded)

Accepted `WD-sf9i` at main commit `cfcd5e4` now preserves malformed
mouth-localizer evidence. Its offline diagnostic on the preserved LF003 cut 3
found strong identity scores:

```text
mouth_activity: 0.95
action_match: 0.9
speaker_attribution: 0.95
```

But the current three-frame localizer prompt returned only two boxes:

```json
{
  "speaker_mouth_bboxes": [
    [0.31, 0.19, 0.03, 0.03],
    [0.31, 0.20, 0.03, 0.02]
  ]
}
```

Diagnostic evidence:

- `datasets/diagnostics/WD-sf9i/lf003-cut3-local-judge-diagnostic.json`
- SHA-256:
  `698b2c16106e8262fe3a56b070d6eed9665d8803b5d8ad7be214832bbdff3771`
- Preserved video SHA-256:
  `08acf7d3601b3489e15ddf76e6f50d741a9d6550b04cc784f29cb952fbe9b47d`

This is a localizer-request/evidence contract failure, not proof of identity
drift and not justification for latent carry.

## USER INTENT

Recover a trustworthy three-frame mouth location for the already preserved
cut-3 artifact without weakening any gate or rendering a new cut.

## Goal

Change the local Qwen locator from one ambiguous three-frame response to
bounded per-frame localization requests, preserve every raw response, and
validate an exact three-box result. Then run an offline diagnostic on the
preserved cut-3 artifact.

## Proposed design

For each generated start/middle/end frame, make one dedicated locator request
requiring:

```json
{"speaker_mouth_bbox": [x, y, width, height]}
```

If a per-frame response is malformed, one bounded retry is allowed for that
frame. Collect exactly three successful boxes in frame order. Every attempt,
including malformed retries, must be represented in `mouth_bbox_raw_response`
as a structured, canonical JSON object containing per-frame status, raw
response, and SHA-256. The integrated `run_vision_judge()` contract remains
unchanged and still rejects anything other than exactly three normalized,
consensus boxes.

## OUT OF SCOPE

- Re-rendering cut 3.
- Rendering cut 4 or assembling a film.
- Weakening mouth-box, vision, Whisper, or SyncNet thresholds.
- Treating two boxes as consensus or deriving a third box synthetically.
- Latent carry or first-frame preservation.
- Changing ModelScope behavior except for shared test fixtures if strictly
  required.

## DIFF BUDGET

- ~4 files, under 300 changed LOC.

## Boundary Map

PRODUCES:
- `qc/audio_critic/local_qwen_vision_judge.py` -> bounded per-frame locator
  with exact three-box output and structured raw-response evidence.
- tests -> model-free per-frame success, malformed first response/retry,
  exhausted retry, wrong count, non-numeric/out-of-range box, and preserved
  raw-response evidence.
- `datasets/diagnostics/<story>/lf003-cut3-per-frame-localizer-diagnostic.json`
  -> offline preserved-artifact result.

CONSUMES:
- existing: `ModelScopeVisionJudge._extract_frames`, `_data_url`, and
  `_response_object`.
- existing: `run_vision_judge(...)` strict three-box consensus contract.
- preserved cut-3 artifact at SHA-256
  `08acf7d3601b3489e15ddf76e6f50d741a9d6550b04cc784f29cb952fbe9b47d`.

## Acceptance Criteria

1. Production localizer issues bounded per-frame requests rather than one
   three-frame request.
2. Each frame yields exactly one normalized `[x,y,w,h]` box; no synthetic
   third box is invented.
3. A malformed per-frame response may be retried at most once; exhaustion,
   transport failure, malformed JSON, wrong field, wrong shape, non-numeric
   values, or out-of-range values fail closed.
4. `mouth_bbox_raw_response` is structured, canonical JSON with per-frame
   attempt/status/raw response/hash evidence and remains safe for durable
   storage (no credentials, base64 frames, or image URLs).
5. Successful output feeds the existing strict `speaker_mouth_bboxes`
   integrated validator unchanged.
6. Model-free tests cover success, retry success, retry exhaustion, malformed
   shape/value, exact output order, and raw-attempt preservation.
7. One offline invocation on preserved cut 3 records either:
   - a valid three-box consensus result; or
   - a fail-closed per-frame diagnostic.
   No new render, cut 4, assembly, or operator acceptance is claimed.
8. If valid boxes are recovered, run the existing SyncNet offline diagnostic
   on the preserved cut-3 video and record its evidence. A SyncNet failure is
   a legitimate gate result, not a reason to weaken thresholds.
9. Existing local-judge, integrated vision, ref2va, executor, and LF003
   evidence tests remain green.
10. `git diff --check` passes.

## Testing Requirements

- Unit/model-free: fake transport for all per-frame paths.
- Integration: local judge result through `run_vision_judge()`.
- Offline live diagnostic: preserved cut-3 artifact only.
- Commands: targeted local-judge/vision/ref2va/executor tests, preserved LF003
  evidence test, and `git diff --check`.

## Skills To Use

- `pvg` for governance.
- `tool-systematic-debugging` before modifying the locator.

## Delivery Requirements

- Exact test output.
- Diagnostic hashes and disposition.
- AC table.
- Story commit SHA.

## nd_contract
status: new

### evidence
- Derived from accepted WD-sf9i diagnostic at main `cfcd5e4`.

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
cd /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-v66o
git diff --check
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m py_compile qc/audio_critic/local_qwen_vision_judge.py tests/test_local_qwen_vision_judge.py
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest -q tests/test_local_qwen_vision_judge.py tests/test_modelscope_vision_judge.py tests/test_vision_judge.py tests/test_ref2va_runtime.py tests/test_completed_ref2va_recovery.py tests/test_jobs_executor.py tests/test_lf003_rhostrong_film_evidence.py
```

Independent coordinator results:

- `git diff --check`: exit 0.
- Compilation: exit 0.
- Targeted suite: 87/87 passed.
- Diagnostic SHA-256:
  `bb6f0c97ed24cbada1a19c7e352d2ccd1bbc07bbb2594765d802d6cce19e8664`.
- Preserved cut-3 video SHA-256 remained:
  `08acf7d3601b3489e15ddf76e6f50d741a9d6550b04cc784f29cb952fbe9b47d`.
- Per-frame localizer recovered exactly three frame-ordered boxes:
  - start `[0.315, 0.205, 0.025, 0.015]`
  - middle `[0.310, 0.190, 0.020, 0.030]`
  - end `[0.270, 0.190, 0.020, 0.010]`
- Integrated `run_vision_judge()` remained unchanged and correctly failed closed on x-center spread `0.0475` versus the existing `0.03` consensus limit.
- Diagnostic-only SyncNet passed using the median box `[0.310, 0.190, 0.020, 0.015]`:
  confidence `3.166184`, offset `-1` frame at 25 fps.
- The diagnostic explicitly records `integrated_vision_consensus_passed=false`; the SyncNet diagnostic did not override the blocking integrated vision gate.
- Forbidden-material scan found no credentials, bearer tokens, passwords, private keys, base64 frames, or image URLs.

### CI/Test Results

```text
87 targeted tests passed
git diff --check: PASS
python compilation: PASS
```

Summary: replaced the ambiguous combined three-frame mouth request with bounded per-frame requests, strict singular-box validation, at-most-one malformed-response retry per frame, canonical per-attempt raw evidence, exact frame-order output, and no synthetic/carry-over box. The preserved cut-3 diagnostic recovered three real boxes; unchanged integrated vision correctly rejected their spatial-consensus spread, and diagnostic SyncNet passed.

Commit SHA: 43a0fab

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Production uses bounded per-frame requests | PASS | Source and model-free payload tests. |
| 2. Exactly three normalized frame-order boxes, no synthetic box | PASS | Tests and live diagnostic. |
| 3. Malformed responses retry once and all invalid families fail closed | PASS | Local-judge test suite. |
| 4. Structured canonical per-attempt raw evidence is safe | PASS | Canonical localizer evidence plus forbidden-material scan. |
| 5. Existing integrated validator remains unchanged | PASS | Integrated result failed closed on spatial consensus with unchanged `0.03` threshold. |
| 6. Model-free paths fully covered | PASS | Included in 87/87 targeted tests. |
| 7. Preserved-artifact diagnostic records real per-frame disposition | PASS | Diagnostic hash `bb6f0c97ed24cbada1a19c7e352d2ccd1bbc07bbb2594765d802d6cce19e8664`. |
| 8. SyncNet run when valid boxes recovered | PASS | Diagnostic-only pass: confidence `3.166184`, offset `-1`; integrated consensus remained failed. |
| 9. Existing targeted tests remain green | PASS | 87/87. |
| 10. `git diff --check` passes | PASS | Exit 0. |


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-19T15:36:51Z status: open -> in_progress
- 2026-09-19T15:36:51Z auto-follows: linked to predecessor WD-sf9i
- 2026-09-19T15:36:51Z claimed by dev-WD-v66o
- 2026-09-19T16:17:24Z status: in_progress -> in_progress
- 2026-09-19T16:17:24Z auto-follows: linked to predecessor WD-ice0
- 2026-09-19T16:18:31Z status: in_progress -> closed

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-sf9i]], [[WD-ice0]]
- Led to: [[WD-8l2f]], [[WD-2p52]], [[WD-rij6]]

## Comments
