---
id: WD-yf9a
title: "Add consent-gated Jev semantic reranking"
status: open
priority: 1
type: task
parent: WD-fehf
created_at: 2026-09-19T03:49:43Z
created_by: speed
updated_at: 2026-09-19T03:49:43Z
content_hash: "sha256:c19c359eb82a6234316babd847642bed5cbf040066f9664d95b0e0716c0880b1"
---

## Description
## Description
Add optional Jev reranking for ambiguous local FTS results. It must remain disabled unless explicitly configured and a TypeSafe credential is present.

## USER INTENT
When lexical ranking cannot distinguish similar skills, an explicitly authorized semantic reranker may improve candidate quality without changing the default private/offline path.

## Acceptance Criteria
1. Jev reranking is disabled by default and requires both local configuration consent and TYPESAFE_API_KEY.
2. Only a bounded prompt summary and bounded local candidate metadata are sent when explicitly enabled.
3. Requests have a strict sub-hook timeout and retry at most once.
4. Network, timeout, malformed response, missing key, or disabled mode returns local candidates unchanged.
5. A successful rerank can promote none/specific candidates and preserves candidate shape.
6. Unit/integration tests use a local fake transport; no live credential is required.
7. The implementation contains no SkillRanker-derived code.
8. Existing routing tests remain green.

## Testing Requirements
- Unit: disabled mode, missing key, timeout, malformed response, successful reorder, none option.
- Integration: fake transport end-to-end through ambiguous ranking path.

## OUT OF SCOPE
- Enabling network inference by default.
- Sending full conversation, repo contents, or raw persistent logs.
- Live API test.

## DIFF BUDGET
- ~3 files, under 350 changed LOC.

## Boundary Map
PRODUCES:
- /Users/speed/.codex/skill-router/jev.py -> rerank(...) -> List[Dict[str, Any]]
- /Users/speed/.codex/skill-router/hook.py -> optional post-FTS reranking call

CONSUMES:
- WD-59q6: local candidate dictionaries from query_candidates(...)

## Skills To Use
- factory-first applies; direct implementation is allowed under the machine-global security-sensitive infrastructure exception.

## Delivery Requirements
- Exact tests, static network scan, hashes, and AC table.

## nd_contract
status: new

### evidence
- TYPESAFE_API_KEY is absent in the current environment, so live testing cannot be required.

### proof
- [ ] Pending implementation

## History

## Links
- Parent: [[WD-fehf]]

## Comments


## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-fehf]]

## Comments
