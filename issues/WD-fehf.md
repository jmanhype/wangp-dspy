---
id: WD-fehf
title: "Complete Codex Skill Router production roadmap"
status: open
priority: 0
type: epic
created_at: 2026-09-19T03:49:42Z
created_by: speed
updated_at: 2026-09-19T03:49:42Z
content_hash: "sha256:534284593ba0b9d8fa8f750cedc3d2a93f945336d75477728d405e83e3d67eb1"
---

## Description
## Description
Complete the remaining production capabilities for the accepted local Codex Skill Router: automatic index freshness, feedback/calibration, observability, and optional Jev semantic reranking.

## Epic Outcomes
- Newly installed or edited skills become available without manual index rebuilds.
- Operators can record usefulness feedback and evaluate routing quality without storing raw prompts.
- Router health and candidate quality are inspectable locally.
- Semantic reranking is available only through explicit network consent and fails closed/off by default.
- The existing fail-open, privacy-preserving, explicit-invocation behavior remains regression-tested.

## OUT OF SCOPE
- Making network reranking enabled by default.
- Persisting raw prompts.
- Automatically executing skills.
- Using SkillRanker source code or contracts.

## MANDATORY SKILLS
- None identified at epic level; story bodies name required skills.

## nd_contract
status: new

### evidence
- Accepted router state inspected 2026-09-19: 13/13 tests pass, all prior router epics accepted, no automatic refresh/feedback/report/Jev capability present.

### proof
- [ ] Epic outcome demonstrated by accepted completion tasks and a final integration gate.

## Acceptance Criteria
1. Automatic or bounded incremental index freshness is installed and tested.
2. Feedback and evaluation artifacts are local, hash-scoped, and tested.
3. A report command summarizes events, feedback, latency, decisions, and candidates.
4. Optional Jev reranking is consent-gated, disabled without configuration/credential, timeout-bounded, and fail-open.
5. Final integration test proves ordinary routing remains unaffected when completion features are disabled.

## Design
Keep local lexical routing as the default fast path. Add infrastructure around it rather than replacing it.

## History

## Links

## Comments


## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments
