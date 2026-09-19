---
id: WD-8r8a
title: "Run 50-prompt local Skill Router calibration"
status: in_progress
priority: 0
type: task
parent: WD-wzbl
created_at: 2026-09-19T03:13:39Z
created_by: speed
updated_at: 2026-09-19T03:13:39Z
content_hash: "sha256:8ca37d7c9240768fb8ee940a186e1e03b6ca5d53bb0244ed657be95d1c7ca07e"
assignee: dev-WD-8r8a
---

## Description
## Description
Process at least 50 recent unique natural Codex prompts through the local Skill Router and produce an observational calibration report.

## Acceptance Criteria
1. Select unique natural prompts from `/Users/speed/.codex/.codex-global-state.json` prompt history without sending them over the network.
2. Prefer the latest prompt from each history thread; deduplicate and exclude synthetic Skill Router verification prompts.
3. Process at least 50 unique prompts through the local router logic.
4. Create a persistent JSON and Markdown report under `/Users/speed/.codex/skill-router/`.
5. Reports contain prompt SHA-256 and never raw prompt text.
6. Report at least: suggestion/abstention counts, latency statistics, candidate distribution, explicit available-skill recall, obvious conversational false positives, and prompts needing manual review.
7. Do not modify `hook.py`, `config.json`, tests, or hook registration.
8. Record a recommendation: continue unchanged, collect more data, or file a follow-up tuning task.

## Design
This is an observational calibration, not a labeled accuracy benchmark. Explicit full skill-name mentions and obvious conversational prompts provide deterministic checks; other natural prompts are summarized for candidate distribution and review.

## OUT OF SCOPE
- Code or threshold changes.
- Network inference.
- Raw prompt persistence.
- External telemetry.

## nd_contract
status: new

### evidence
- Local prompt-history structure inspected: 64 thread histories and 472 stored prompt entries.

### proof
- [ ] AC #1: local-only source verified.
- [ ] AC #2: selection method recorded.
- [ ] AC #3: at least 50 unique prompts processed.
- [ ] AC #4: JSON and Markdown reports created.
- [ ] AC #5: raw-prompt absence verified.
- [ ] AC #6: required metrics reported.
- [ ] AC #7: router source/config hashes unchanged.
- [ ] AC #8: recommendation recorded.

## History

## Links
- Parent: [[WD-wzbl]]

## Comments


## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-19T03:13:39Z status: open -> in_progress
- 2026-09-19T03:13:39Z claimed by dev-WD-8r8a

## Links
- Parent: [[WD-wzbl]]

## Comments
