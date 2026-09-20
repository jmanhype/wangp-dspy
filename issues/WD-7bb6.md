---
id: WD-7bb6
title: "Correct Satan's Mom final-film resolution metadata"
status: in_progress
priority: 2
type: task
created_at: 2026-09-20T02:00:53Z
created_by: speed
updated_at: 2026-09-20T02:01:04Z
content_hash: "sha256:8aa13b8e448ee31f777da63381b0997f324887bca7bb23734b8a9f45fc2e2a8c"
assignee: dev-WD-7bb6
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


## History
- 2026-09-20T02:01:04Z status: open -> in_progress
- 2026-09-20T02:01:04Z claimed by dev-WD-7bb6

## Links


## Comments
