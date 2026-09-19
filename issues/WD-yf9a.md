---
id: WD-yf9a
title: "Add consent-gated Jev semantic reranking"
status: in_progress
priority: 1
type: task
parent: WD-fehf
created_at: 2026-09-19T03:49:43Z
created_by: speed
updated_at: 2026-09-19T05:59:31Z
content_hash: "sha256:35b574be0e7bae4833f792c43ae69341653c77c9e641b8d788314f69289a2fff"
assignee: dev-WD-yf9a
follows: [WD-8tkc, WD-ft6r]
labels: [delivered]
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
## Implementation Evidence

Commands run:

```bash
cd /Users/speed/.codex/skill-router
/usr/bin/python3 -m py_compile jev.py hook.py test_jev.py
/usr/bin/python3 -m unittest discover -s . -p 'test_*.py' -v
pvg verify /Users/speed/.codex/skill-router/jev.py /Users/speed/.codex/skill-router/hook.py /Users/speed/.codex/skill-router/test_jev.py --format=text
```

Independent coordinator rerun summary:

- Python compilation: exit 0.
- Full unit discovery: 27 tests, 27 passed, 0 failures, 0 errors, exit 0.
- `pvg verify`: `VERIFY: PASSED (3 files scanned, 0 issues)`.
- Production config has no Jev section, `TYPESAFE_API_KEY` is absent, ambiguous local candidates were returned unchanged, and the fail-transport probe made zero network calls.
- Static scan found real `urlopen` only in `jev.py`; tests use fake transport; `SkillRanker` occurrences: 0.
- Source review confirmed fixed HTTPS endpoint, prompt-summary cap 512, candidate-name cap 96, at most eight matched terms, response cap 64 KiB, timeout cap 0.25s, one retry, and no candidate paths/local-only fields in payloads.
- Coordination note: an accidental duplicate worker was interrupted before editing; final hashes match the single completed implementation and the other accepted router artifacts.

### CI/Test Results

```text
Ran 27 tests in 0.489s

OK
VERIFY: PASSED (3 files scanned, 0 issues)
Default/off production probe: local_candidate_count=2, unexpected_transport_calls=0
```

Summary: added consent-gated, off-by-default Jev semantic reranking for ambiguous local FTS results with bounded metadata, strict timeout/retry limits, malformed/missing/network fail-open behavior, candidate-shape preservation, fake-transport coverage, and no SkillRanker-derived code.

Commit SHA: e5ff9ccc4dd605f68d200d14f8621882d379d5db484f8890f25371e2314f64a1

This is the SHA-256 of the machine-global delivery manifest, not a Git commit; authorized artifacts live outside the wangp-dspy Git worktree.

Final hashes:

```text
eddc2f566847eb88be295b4150410b41e18d393a6609e2389e984a57d7c6ea3d  /Users/speed/.codex/skill-router/jev.py
d547a5e847958280627c8f03374ab48a71973e6124101b5127bd79af6ab4d0ca  /Users/speed/.codex/skill-router/hook.py
5d541649c91054af13543823ee3fe2ee94ad01b2b88607dad8a30199acea5164  /Users/speed/.codex/skill-router/test_jev.py
3149400147f1d2e81069030f7e2eaf6bda5aee372e188f1659f0166dac63b815  /Users/speed/.codex/skill-router/config.json
2c3cd4441badce6464c5039f7c16a0f24b6f7b3b28ac8c3b40b5db56f8e1fa16  /Users/speed/.codex/skill-router/index_skills.py
2bdf48910135eb1bbe33e2ea80e9af367bb9b92d8cfdc613175d072588c2bb9a  /Users/speed/.codex/skill-router/test_router.py
6536355d3c96ff8651a9176f6645cb54d73189b2e25c91ac3f1a3dd8fee8461f  /Users/speed/.codex/skill-router/feedback.py
300cc14fe27123c8ce6e2fbd2719955b95123964c88fda160eefb04bef830b33  /Users/speed/.codex/skill-router/test_feedback.py
02c459c9b9f037d316402343af2a0e46a76dcf32177304350c2cd377598e284a  /Users/speed/.codex/skill-router/report.py
a9b45bbc78f40f532e791e94712c179390791b67f3de9ee3a576e022860cf35b  /Users/speed/.codex/skill-router/test_report.py
```

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| 1. Disabled by default; requires config consent and TYPESAFE_API_KEY | PASS | Production probe and disabled/missing-key tests. |
| 2. Only bounded prompt summary and bounded candidate metadata transmitted | PASS | Payload cap tests and source review. |
| 3. Strict timeout, at most one retry | PASS | Timeout capped at 0.25s; retry test proves two attempts total. |
| 4. Missing key/disabled/network/timeout/malformed response returns local candidates unchanged | PASS | Fail-open unit tests and production probe. |
| 5. Valid ranking or none preserves candidate shape | PASS | Reorder and `none` tests. |
| 6. Fake transport unit/integration coverage; no credential required | PASS | `test_jev.py`; no live endpoint invoked. |
| 7. No SkillRanker-derived code | PASS | Static scan found zero occurrences. |
| 8. Existing routing tests remain green | PASS | Full discovery 27/27 OK. |


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-19T05:45:02Z status: open -> in_progress
- 2026-09-19T05:45:02Z auto-follows: linked to predecessor WD-8tkc
- 2026-09-19T05:45:02Z claimed by dev-WD-yf9a
- 2026-09-19T05:58:30Z status: in_progress -> in_progress
- 2026-09-19T05:58:30Z auto-follows: linked to predecessor WD-ft6r

## Links
- Parent: [[WD-fehf]]
- Follows: [[WD-8tkc]], [[WD-ft6r]]

## Comments
