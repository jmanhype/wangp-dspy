---
id: WD-7bb6
title: "Correct Satan's Mom final-film resolution metadata"
status: in_progress
priority: 2
type: task
created_at: 2026-09-20T02:00:53Z
created_by: speed
updated_at: 2026-09-20T02:02:42Z
content_hash: "sha256:5b6183e16e92d12088945aa5096f741fc8369438a2e1f39a55ea8347c8681a55"
assignee: dev-WD-7bb6
labels: [delivered]
---

## Description
## USER INTENT

The Satan's Mom delivery evidence should accurately describe the dimensions of the preserved final artifact.

## Goal

Correct the S4 delivery resolution text from the incorrect portrait orientation to the actual measured landscape orientation.

## Context

Measured final artifact:

- path: s4/films/satans-mom/final/satans_mom.mp4
- ffprobe video dimensions: 832x480
- SHA-256: f1efca116edf17adcdb4279faec14e2e27bc0557c3ac97855037c385bdd78aac

Current documentation incorrectly says:

```text
480x832
```

## OUT OF SCOPE

- Re-encoding, cropping, rotating, or otherwise modifying the final film.
- Changing run records, QC evidence, or accepted tracker history.
- Updating any other film metadata.

## DIFF BUDGET

- 1 file, 1 changed line.

## Boundary Map

PRODUCES:
- s4/S4_DELIVERY.md -> corrected final-film resolution metadata

CONSUMES:
- (existing): s4/films/satans-mom/final/satans_mom.mp4
  source: preserved final artifact measured with ffprobe

## Acceptance Criteria

1. s4/S4_DELIVERY.md says 832x480.
2. ffprobe independently measures the final artifact as 832x480.
3. The final film SHA-256 remains f1efca116edf17adcdb4279faec14e2e27bc0557c3ac97855037c385bdd78aac.
4. The exact pipeline contract test passes.
5. git diff --check passes.

## Testing Requirements

- ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 s4/films/satans-mom/final/satans_mom.mp4
- shasum -a 256 s4/films/satans-mom/final/satans_mom.mp4
- /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest -q tests/test_pipeline.py
- git diff --check

## MANDATORY SKILLS

- pvg: story governance and merge.

## nd_contract
status: new

### evidence
- Discrepancy independently measured during WD-h25b closeout.

### proof
- [ ] Pending documentation correction.


## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

Commands run:

```bash
cd /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-7bb6
grep -n '832x480' s4/S4_DELIVERY.md
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 s4/films/satans-mom/final/satans_mom.mp4
shasum -a 256 s4/films/satans-mom/final/satans_mom.mp4
/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/pytest -q tests/test_pipeline.py
git diff --check
git diff --cached --check
```

### CI/Test Results

```text
documented resolution: 832x480
ffprobe resolution: 832,480
final SHA-256: f1efca116edf17adcdb4279faec14e2e27bc0557c3ac97855037c385bdd78aac
pipeline contract: 11 passed
diff checks: PASS
```

Summary: the one-line S4 delivery metadata now matches the preserved final artifact. The film was not modified.

Commit SHA: 2aa264d87bca13e725dbb3d7e81e10aa70a2841d

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Document says 832x480 | PASS | s4/S4_DELIVERY.md line 9 |
| 2. ffprobe matches | PASS | 832,480 |
| 3. Film hash unchanged | PASS | f1efca116edf17adcdb4279faec14e2e27bc0557c3ac97855037c385bdd78aac |
| 4. Pipeline contract | PASS | 11/11 |
| 5. Diff hygiene | PASS | exit 0 |

## nd_contract
status: delivered

### evidence
- Commit SHA: `2aa264d87bca13e725dbb3d7e81e10aa70a2841d`.
- ffprobe: `832,480`.
- Final film SHA unchanged.

### proof
- [x] AC #1 through #5 verified.


## History
- 2026-09-20T02:01:04Z status: open -> in_progress
- 2026-09-20T02:01:04Z claimed by dev-WD-7bb6
- 2026-09-20T02:02:42Z status: in_progress -> in_progress

## Links


## Comments
