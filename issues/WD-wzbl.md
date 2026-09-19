---
id: WD-wzbl
title: "Codex Skill Router natural-use calibration"
status: closed
priority: 0
type: epic
created_at: 2026-09-19T03:13:39Z
created_by: speed
updated_at: 2026-09-19T03:36:27Z
content_hash: "sha256:cd6901e2b3a3753cf6b92fa2443d7595b0f9217d4694d8f6c669816a22860e56"
closed_at: 2026-09-19T03:36:27Z
close_reason: "All child stories accepted; natural-use calibration completed and its explicit-invocation follow-up fixed."
---

## Description
## Description
Run an observational natural-use calibration window for the accepted local Codex Skill Router using recent prompts already stored on this machine.

## Epic Outcomes
- A 50-prompt local calibration report is produced without network inference.
- Persistent calibration evidence excludes raw prompt text.
- Router behavior is summarized with latency, abstention, explicit-skill recall, and candidate distribution.
- Any material tuning recommendation is recorded without changing code in this task.

## OUT OF SCOPE
- Network calls or Jev inference.
- Automatically changing thresholds.
- Persisting raw prompts.
- Reopening previously accepted stories.

## nd_contract
status: new

### evidence
- Operator asked Codex to perform the 30-50 prompt calibration window and explicitly required Paivot.

### proof
- [ ] Calibration report exists and meets the task acceptance criteria.

## Acceptance Criteria
1. Calibration uses local prompt history only.
2. Report covers at least 50 unique natural prompts.
3. Persistent output contains prompt hashes, not raw prompt text.
4. Report includes suggestion/abstention counts, latency, candidate distribution, explicit-skill recall, and obvious false-positive count.
5. No router source or hook configuration changes.

## Design
Use the latest stored prompt per history thread, deduplicate prompts, exclude synthetic Skill Router verification prompts, and invoke the local hook payload path in-process.

## History

## Links

## Comments


## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-19T03:36:27Z status: open -> closed

## Links


## Comments
