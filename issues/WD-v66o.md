---
id: WD-v66o
title: "Recover exact three-frame LF003 mouth localization"
status: in_progress
priority: 0
type: bug
parent: WD-j9nx
created_at: 2026-09-19T15:36:38Z
created_by: speed
updated_at: 2026-09-19T16:17:24Z
content_hash: "sha256:46844e806e1ed7ad3790b7219240f365f9960af394dd8e5a9573c18439b70347"
assignee: dev-WD-v66o
follows: [WD-sf9i, WD-ice0]
labels: [delivered]
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


## History
- 2026-09-19T15:36:51Z status: open -> in_progress
- 2026-09-19T15:36:51Z auto-follows: linked to predecessor WD-sf9i
- 2026-09-19T15:36:51Z claimed by dev-WD-v66o
- 2026-09-19T16:17:24Z status: in_progress -> in_progress
- 2026-09-19T16:17:24Z auto-follows: linked to predecessor WD-ice0

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-sf9i]], [[WD-ice0]]

## Comments
