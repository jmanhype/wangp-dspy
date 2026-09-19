---
id: WD-8r8a
title: "Run 50-prompt local Skill Router calibration"
status: closed
priority: 0
type: task
parent: WD-wzbl
created_at: 2026-09-19T03:13:39Z
created_by: speed
updated_at: 2026-09-19T03:26:33Z
content_hash: "sha256:42ac00bad6e2a04fd68e22f62e72d4148a5cb24075837bf52372dd6be786d0c2"
assignee: dev-WD-8r8a
labels: [accepted]
closed_at: 2026-09-19T03:26:33Z
close_reason: "Accepted: 50-prompt local calibration completed with hash-only reports, unchanged router implementation, zero network/raw-prompt leakage, and a focused explicit-invocation follow-up recommendation."
led_to: [WD-m6pq]
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


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-18.

### proof
- [x] Story closed after accepted label was applied.


## PM Decision
ACCEPTED [2026-09-19]: Calibration evidence reviewed and meets the bar. Report covers 50 unique local natural prompts, validates JSON, confirms zero network calls and raw-prompt leaks, leaves the event log unchanged, preserves router hashes, and records the explicit-invocation follow-up recommendation.

## nd_contract
status: accepted

### evidence
- Reviewed delivery proof and independently validated report structure, metrics, privacy fields, and artifact hashes.

### proof
- [x] AC-by-AC verified from recorded evidence.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-18.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

### CI/Test Results
Commands run:
 - Local prompt-history shape audit with /usr/bin/python3.
 - /usr/bin/python3 -m py_compile /tmp/sr_natural_calibration.py
 - /usr/bin/python3 /tmp/sr_natural_calibration.py
 - /usr/bin/python3 -m json.tool /Users/speed/.codex/skill-router/calibration-20260919-natural50.json
 - Event-log line-count before/after comparison.
 - Router source/config hash comparison.
Summary: calibration PASS for 50 unique natural prompts; JSON validation PASS; event log unchanged at 19 lines; zero network calls; zero raw prompt leaks; source/config hashes unchanged.
Coverage: 50 latest-per-thread natural prompts selected from 64 local histories containing 472 entries.
Commit SHA: d318d661ac3287b35aa5e77c7fda4c9efc410b37dccd8e76193e8e3527149e03
This is a deterministic machine-global artifact manifest SHA, not a wangp-dspy Git commit.

### Calibration Results
- Suggestions/abstentions: 35 suggest, 15 abstain.
- Latency: median 3.057 ms, p95 44.278 ms, maximum 72.310 ms.
- Obvious conversational prompts: 2, false-positive suggestions 0.
- Literal skill-name references: 7; top-1 1, top-3 1. This metric is caveated because common names such as github/agents can appear as ordinary language.
- Detected explicit skill invocations: 2; top-1 0, top-3 0.
- Natural prompts needing manual review: 41.
- Recommendation: file a focused follow-up to resolve explicit skill invocations locally before probabilistic ranking; do not globally change thresholds from this observational sample.

### AC Verification
| AC | Status | Evidence |
|---|---|---|
| 1 | PASS | Source was local .codex-global-state.json; privacy block records network_calls=0. |
| 2 | PASS | Latest non-empty prompt per thread, deduplicated; 64 histories and 472 entries summarized. |
| 3 | PASS | 50 unique natural prompts processed. |
| 4 | PASS | JSON and Markdown reports created under /Users/speed/.codex/skill-router. |
| 5 | PASS | Reports use SHA-256; fail-closed leak checks passed. |
| 6 | PASS | Decisions, latency, distributions, literal/explicit metrics, false positives, and review count reported. |
| 7 | PASS | hooks.json, config.json, and hook.py hashes remained unchanged. |
| 8 | PASS | Follow-up recommendation recorded: exact explicit-invocation resolver. |

### Artifacts
- JSON: /Users/speed/.codex/skill-router/calibration-20260919-natural50.json
- Markdown: /Users/speed/.codex/skill-router/calibration-20260919-natural50.md
- JSON SHA-256: e2ef842e5913dada6aa899307a26444a57f4dafea1a6b221fd0f36bdfe873972
- Markdown SHA-256: 4478f94cd90cd97bdef538675abc8991454daa53926b58fb5030663286991436

LEARNINGS:
- Literal substring matching is invalid for short skill names; contiguous token matching and a separate explicit-invocation detector are required.
- A raw-substring privacy check can falsely reject a two-character conversational prompt; exact JSON-value/line checks avoid that while preserving fail-closed behavior.
- Calibration latency is comfortably below the hook budget, but explicit invocation correctness is a separate failure mode from lexical ranking quality.

## nd_contract
status: delivered

### evidence
- Calibration artifacts, privacy checks, source/config hashes, event-log invariance, and report hashes recorded above.

### proof
- [x] AC #1: local-only source used.
- [x] AC #2: selection method and source counts recorded.
- [x] AC #3: 50 unique prompts processed.
- [x] AC #4: JSON and Markdown reports created.
- [x] AC #5: no raw prompt persisted.
- [x] AC #6: all required metrics reported.
- [x] AC #7: router source/config unchanged.
- [x] AC #8: focused follow-up recommendation recorded.

## nd_contract
status: in_progress

### evidence
- Claimed 2026-09-19 for local observational calibration under the machine-global infrastructure exception; no repository worktree applies.

### proof
- [ ] Calibration execution and report pending.

## History
- 2026-09-19T03:13:39Z status: open -> in_progress
- 2026-09-19T03:13:39Z claimed by dev-WD-8r8a
- 2026-09-19T03:25:28Z status: in_progress -> in_progress
- 2026-09-19T03:26:33Z status: in_progress -> closed

## Links
- Parent: [[WD-wzbl]]
- Led to: [[WD-m6pq]]

## Comments

### 2026-09-19T03:25:42Z speed
## Implementation Evidence (DELIVERED)

Commands run:
 - /usr/bin/python3 -m py_compile /tmp/sr_natural_calibration.py
 - /usr/bin/python3 /tmp/sr_natural_calibration.py
 - /usr/bin/python3 -m json.tool /Users/speed/.codex/skill-router/calibration-20260919-natural50.json
Summary: 50-prompt local calibration PASS; JSON validation PASS; zero network calls; zero raw prompt leaks; event log unchanged at 19 lines; router source/config hashes unchanged.
Commit SHA: d318d661ac3287b35aa5e77c7fda4c9efc410b37dccd8e76193e8e3527149e03

## nd_contract
status: delivered

### evidence
- Reports, metrics, privacy checks, hashes, and recommendation are recorded in Notes.

### proof
- [x] AC #1: local-only source used.
- [x] AC #2: latest-per-thread deduplication recorded.
- [x] AC #3: 50 unique prompts processed.
- [x] AC #4: JSON and Markdown reports created.
- [x] AC #5: no raw prompt persisted.
- [x] AC #6: required metrics reported.
- [x] AC #7: router source/config unchanged.
- [x] AC #8: explicit-invocation follow-up recommended.
