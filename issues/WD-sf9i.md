---
id: WD-sf9i
title: "Preserve malformed LF003 cut3 mouth-localizer evidence"
status: closed
priority: 0
type: bug
parent: WD-j9nx
created_at: 2026-09-19T15:00:51Z
created_by: speed
updated_at: 2026-09-19T15:35:08Z
content_hash: "sha256:fcadc44b786c4d12a337bbebfd8bc5d1e68e649ddb1d92634d64976b03e7b99b"
assignee: dev-WD-sf9i
follows: [WD-ice0, WD-clms]
labels: [delivered, accepted]
closed_at: 2026-09-19T15:35:08Z
close_reason: "Accepted: independently reran compilation, 34 vision/executor tests, 27 adapter/ref2va runtime tests, preserved LF003 evidence tests, git diff --check, diagnostic/hash inspection, and forbidden-material scan. Malformed mouth-box evidence remains blocking and is now replayable through every durable evidence boundary."
---

## Description
## Context (Embedded)

Finding 84 is authoritative:
`docs/findings/84-lf003-cut3-mouth-box-gate.md` at story commit `8db5339`.

WD-rij6 freshly rendered LF003 cuts 1 and 2 through every gate. Cut 3 passed
pre/post Whisper at `1.000/1.000`, but the local Qwen vision judge returned a
result that failed the integrated three-box contract:

```text
vision result must include three speaker_mouth_bboxes [x,y,w,h]
```

The local adapter makes two requests:

1. identity/composition scoring; and
2. dedicated mouth localization.

It stores the second response under `mouth_bbox_raw_response`, but the current
integrated rejection path preserves only the generic identity `raw_response`.
Consequently, the exact malformed localizer output that rejected cut 3 was not
available in `qc-evidence.json` or the durable visual-rejection record. That
prevents a honest offline distinction between:

- malformed/truncated localizer JSON;
- a judge refusal;
- missing boxes;
- wrong box count;
- non-numeric/out-of-range boxes; or
- a true visual continuity failure.

Preserved current artifacts:

- cut 3 remux SHA-256:
  `08acf7d3601b3489e15ddf76e6f50d741a9d6550b04cc784f29cb952fbe9b47d`
- cut 3 chain input SHA-256:
  `045a28a664b718c4edc1833a68b32882073f7afdddf4b5367c375b9e5e7fd72a`
- queue SHA-256:
  `3f0aa16b384f6c3e0f043d3d9bbc451f34b0af22853a1eece341d4aae5112e0b`
- ledger SHA-256:
  `04f8ff1568d10e50cdd02a27c5cfe294605448805e49feca79de19990d651b38`

## USER INTENT

When a blocking mouth-localizer response is malformed, preserve exactly what
the judge said and fail closed. Never force the pipeline to guess whether a
render is bad when the evidence contract itself failed.

## Goal

Make malformed mouth-localizer evidence replayable and durable, then exercise
the preserved cut-3 artifact offline through the corrected evidence path.

## OUT OF SCOPE

- Re-rendering cut 3.
- Rendering cut 4 or assembling a film.
- Weakening any Whisper, vision, mouth-box consensus, or SyncNet threshold.
- Implementing latent carry or first-frame preservation.
- Changing the accepted cuts 1–2 artifacts.
- Replacing the local Qwen judge.

## DIFF BUDGET

- ~5 files, under 300 changed LOC.

## Boundary Map

PRODUCES:
- `qc/audio_critic/vision_judge.py` -> `VisionJudgeError` carries both
  identity raw response and mouth-localizer raw response separately.
- `qc/audio_critic/ref2va_stage.py` -> vision rejection evidence is persisted
  in `qc-evidence.json`, including both raw responses and partial scores.
- `services/jobs/executor.py` -> `_vision_rejection_evidence(...)` serializes
  identity and mouth-localizer evidence without dropping either field.
- tests -> model-free malformed locator coverage and durable evidence checks.

CONSUMES:
- existing: `qc/audio_critic/local_qwen_vision_judge.py` -> judge result may
  contain `raw_response` and `mouth_bbox_raw_response`.
- existing: Finding 84 artifacts on `story/WD-rij6` commit `8db5339`.

## Acceptance Criteria

1. A malformed/missing `speaker_mouth_bboxes` result raises the same blocking
   `VisionJudgeError`; no threshold is weakened.
2. The error preserves:
   - all numeric identity scores parsed before rejection;
   - the identity raw response; and
   - the dedicated mouth-localizer raw response.
3. `run_ref2va_qc_stage()` writes a `vision_rejection` object into
   `qc-evidence.json` on this failure, while retaining already-passed Whisper
   evidence.
4. The executor’s durable visual-rejection history contains both raw responses
   and partial scores, with no raw prompt or credential material.
5. Model-free tests reproduce at least:
   - missing bbox array;
   - wrong box count;
   - non-numeric box values;
   - out-of-range box values; and
   - a valid three-box response still passes shape validation.
6. An offline local-judge call against the preserved cut-3 artifact records
   its actual locator response using the corrected path. The call may pass or
   fail, but it must not be reported as a new render or film acceptance.
7. Existing vision, local-judge, executor, and LF003 evidence tests remain
   green.
8. `git diff --check` passes.

## Testing Requirements

- Unit tests: all malformed bbox families and raw-response propagation.
- Integration tests: real local in-memory/ref2va-stage persistence through
  executor evidence structures; no network.
- Offline live diagnostic: invoke the local judge on preserved cut 3 without
  rendering; persist exact response/hash. This is diagnostic evidence, not
  film acceptance.
- Commands: targeted vision/ref2va/executor tests, LF003 evidence test, and
  `git diff --check`.

## Skills To Use

- `pvg` for story governance.
- `tool-systematic-debugging` before changing behavior.

## Delivery Requirements
- Exact test output.
- Cut-3 diagnostic response hash and disposition.
- AC table.
- Story commit SHA.

## nd_contract
status: new

### evidence
- Derived from Finding 84 and rejected WD-rij6 evidence at commit `8db5339`.

### proof
- [ ] Pending implementation

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-sf9i
git diff --check
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m py_compile qc/audio_critic/vision_judge.py qc/audio_critic/ref2va_stage.py services/jobs/executor.py tests/test_vision_judge.py tests/test_jobs_executor.py
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest -q tests/test_vision_judge.py tests/test_jobs_executor.py
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest -q tests/test_local_qwen_vision_judge.py tests/test_modelscope_vision_judge.py tests/test_ref2va_runtime.py
cd /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-rij6
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest -q tests/test_lf003_fourcut_gate_failure.py
```

Independent coordinator results:

- `git diff --check`: exit 0.
- Compilation: exit 0.
- Vision/executor tests: 34/34 passed.
- Vision adapter/ref2va runtime tests: 27/27 passed.
- Preserved LF003 evidence test: 4/4 passed.
- Diagnostic JSON parsed successfully and contains both identity and mouth-localizer raw responses plus SHA-256 hashes.
- Forbidden-material scan found no API keys, bearer tokens, passwords, private keys, base64 frames, or image URLs.
- Offline diagnostic used preserved cut-3 video hash `08acf7d3601b3489e15ddf76e6f50d741a9d6550b04cc784f29cb952fbe9b47d`; no render, cut 4, assembly, or queue mutation occurred.

### CI/Test Results

```text
34 vision/executor tests passed
27 vision adapter/ref2va runtime tests passed
4 preserved LF003 evidence tests passed
git diff --check: PASS
```

Summary: malformed or missing three-box mouth-localizer output remains blocking, while VisionJudgeError, Ref2VA QC evidence, and executor rejection history now preserve parsed scores plus separate identity and locator raw responses. The preserved cut-3 diagnostic proves the local judge currently returns two boxes despite strong identity scores.

Commit SHA: f30a8b5

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Malformed boxes remain blocking; thresholds unchanged | PASS | `VisionJudgeError` path and tests. |
| 2. Error preserves scores and both raw responses | PASS | Parameterized vision tests. |
| 3. Ref2VA persists `vision_rejection` with Whisper evidence | PASS | `test_qc_stage_preserves_vision_rejection_evidence`. |
| 4. Executor history preserves evidence without prompts/credentials | PASS | `test_malformed_vision_contract_failure_is_terminal_and_evidence_preserved`. |
| 5. Missing/wrong-count/non-numeric/out-of-range/valid cases covered | PASS | Parameterized malformed locator tests. |
| 6. Offline cut-3 diagnostic persisted with hashes | PASS | Diagnostic JSON SHA-256 `698b2c16106e8262fe3a56b070d6eed9665d8803b5d8ad7be214832bbdff3771`. |
| 7. Existing tests remain green | PASS | 34 + 27 + 4 targeted tests passed. |
| 8. `git diff --check` passes | PASS | Exit 0. |

Non-AC note: `pvg verify services/jobs/executor.py ...` reports a pre-existing bare `pass` at executor line 603 from commit `3d98d331`. It is unrelated to this change and was not hidden or altered.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-19T15:01:07Z status: open -> in_progress
- 2026-09-19T15:01:07Z auto-follows: linked to predecessor WD-ice0
- 2026-09-19T15:01:07Z claimed by dev-WD-sf9i
- 2026-09-19T15:01:26Z dep_added: blocks WD-rij6
- 2026-09-19T15:33:17Z status: in_progress -> in_progress
- 2026-09-19T15:33:17Z auto-follows: linked to predecessor WD-clms
- 2026-09-19T15:35:08Z status: in_progress -> closed
- 2026-09-19T15:35:08Z dep_removed: no_longer_blocks WD-rij6

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-ice0]], [[WD-clms]]

## Comments
