---
id: WD-wzbl
title: "Codex Skill Router natural-use calibration"
status: open
priority: 0
type: epic
created_at: 2026-09-19T03:13:39Z
created_by: speed
updated_at: 2026-09-19T03:13:39Z
content_hash: "sha256:7c2fac78add30a928fe6a5f1e7d7ac11cbe37e8cc7bf2199f605cf1df0395bb8"
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


## Links


## Comments
