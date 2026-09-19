---
id: WD-o1xf
title: "Tune Skill Router symptom specificity"
status: closed
priority: 0
type: task
parent: WD-dic4
created_at: 2026-09-19T02:48:59Z
created_by: speed
updated_at: 2026-09-19T02:53:56Z
content_hash: "sha256:1b86af760a169fa3ae901037dff95ce725f1d4de94e28fe9da62f5e2c4f6c8b8"
assignee: dev-WD-o1xf
labels: [delivered, accepted]
closed_at: 2026-09-19T02:53:56Z
close_reason: "Accepted: symptom-specific Supabase RLS debugging now outranks the broad Supabase skill under meta-language prompts, with 9/9 tests, clean pvg verify, fresh-process confirmation, and unchanged hook registration."
---

## Description
## Description
Tune the local Skill Router ranking so detailed symptom descriptions outweigh broad one-token domain-name matches when a prompt also contains hook-test/meta language.

## Context
The accepted router was live-verified in a fresh Codex process. The exact injected ranking was:
1. supabase — 0.82
2. supabase-rls-frontend-debugging — 0.7407

The technical prompt contained detailed Supabase RLS symptoms, but also asked the fresh session to quote router context. Those meta terms inflated broad-body overlap and the one-token exact-name boost.

## Acceptance Criteria
1. Add a regression test using the live-style prompt: `Live hook verification: Why does my Supabase frontend show empty rows when the API returns data? First quote the exact Skill Router advisory context injected into this turn, or say NO_SKILL_ROUTER_CONTEXT if none was injected. Then answer the technical question in two sentences.`
2. On the current local index, `supabase-rls-frontend-debugging` must rank above `supabase`.
3. A short domain-focused prompt must still return a Supabase candidate.
4. All existing tests continue to pass.
5. `pvg verify` on changed source/test files reports zero issues.
6. No network calls, prompt persistence, hook registration changes, or skill execution behavior are added.

## Design
Inspect score components, then apply the smallest deterministic scoring change that favors symptom/meta overlap over a broad one-token exact-name boost. Prefer general scoring logic over hard-coding the word Supabase.

## OUT OF SCOPE
- Jev reranking.
- Embeddings.
- Automatic index refresh.
- Reopening the accepted MVP story.

## nd_contract
status: new

### evidence
- Live fresh-process output and event log recorded in WD-59q6 post-acceptance comment.

### proof
- [ ] AC #1: regression test added.
- [ ] AC #2: specific skill ranks above broad skill.
- [ ] AC #3: short prompt still suggests Supabase.
- [ ] AC #4: full router suite passes.
- [ ] AC #5: pvg verify zero issues.
- [ ] AC #6: diff contains no network/persistence/registration behavior.

## History

## Links
- Parent: [[WD-dic4]]

## Comments


## Acceptance Criteria


## Design


## Notes
## PM Decision
ACCEPTED [2026-09-19]: Evidence reviewed and meets the bar. The RED regression reproduced the live ranking defect; the scoring change passed 9/9 tests, zero pvg verify findings, local and fresh-process ordering checks, short-domain behavior, unchanged hook registration, and no prohibited network/persistence behavior.

## nd_contract
status: accepted

### evidence
- Reviewed delivery proof, test counts, fresh-process evidence, hashes, and scope checks.

### proof
- [x] AC-by-AC verified from recorded and independently spot-checked evidence.

## Implementation Evidence

### CI/Test Results
- Commands run:
  - /usr/bin/python3 -m py_compile /Users/speed/.codex/skill-router/hook.py /Users/speed/.codex/skill-router/test_router.py
  - /usr/bin/python3 -m unittest discover -s /Users/speed/.codex/skill-router -p 'test_router.py' -v
  - pvg verify /Users/speed/.codex/skill-router/hook.py /Users/speed/.codex/skill-router/test_router.py --format=text
  - Fresh Codex app-bundle exec verification.
- Summary: compile PASS; unit/integration/current-index tests PASS 9/9, 0 failures, 0 errors, 0 skipped; pvg verify PASS 0 issues; fresh Codex process PASS with top candidate supabase-rls-frontend-debugging and one automatic event added.
- Coverage: 9 targeted tests plus fresh-process integration proof.
- Commit SHA: b53f655eb88f67c11dbef361349bf8fb7d40d7a885126bc1c3bb66d30967ec96

### AC Verification
| AC | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Live-style regression test | PASS | test_live_meta_language_prefers_specific_current_index_skill initially failed, then passed. |
| 2 | Specific skill outranks broad skill | PASS | Fresh process and local probe ranked supabase-rls-frontend-debugging first. |
| 3 | Short domain prompt still works | PASS | Use Supabase database query returned supabase first at 0.9621. |
| 4 | Existing suite passes | PASS | 9/9 tests, 0 failures/errors/skips. |
| 5 | pvg verify clean | PASS | VERIFY PASSED, 2 files, 0 issues. |
| 6 | No prohibited behavior added | PASS | Only hook.py scoring and test_router.py changed; registration hash unchanged. |

LEARNINGS:
- Keep validator-facing proof sections literal and explicit.

## nd_contract
status: delivered

### evidence
- Exact test, verify, live-process, and hash evidence recorded above.

### proof
- [x] AC #1: regression added and reproduced.
- [x] AC #2: specific skill ranks above broad skill.
- [x] AC #3: short prompt still returns Supabase.
- [x] AC #4: 9/9 tests pass.
- [x] AC #5: pvg verify zero issues.
- [x] AC #6: no network/persistence/registration/execution behavior added.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-18.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence
Commands run:
 - /usr/bin/python3 -m py_compile /Users/speed/.codex/skill-router/hook.py /Users/speed/.codex/skill-router/test_router.py
 - /usr/bin/python3 -m unittest discover -s /Users/speed/.codex/skill-router -p 'test_router.py' -v
 - /Applications/Codex.app/Contents/Resources/codex exec --dangerously-bypass-hook-trust --sandbox read-only --config approval_policy=never --output-last-message /tmp/skill-router-calibrated-output.txt <live-style verification prompt>
 - pvg verify /Users/speed/.codex/skill-router/hook.py /Users/speed/.codex/skill-router/test_router.py --format=text
Summary: RED regression reproduced broad supabase ranked above supabase-rls-frontend-debugging; scoring update passed 9/9 tests, pvg verify 0 issues, local live-style probe ranked the specific skill first, and a fresh Codex process also ranked it first with one automatic event added in 16 ms.
Commit SHA: b53f655eb88f67c11dbef361349bf8fb7d40d7a885126bc1c3bb66d30967ec96
The SHA is the deterministic machine-global artifact-manifest snapshot, not a wangp-dspy Git commit. Only hook.py and test_router.py were intentionally changed; hooks.json registration remained byte-for-byte unchanged at 6f9154a47f5f8433a43b07128b1c613254351bb29fc6cc00366db0d6644ae506.
Coverage: 9 targeted tests including the new live-meta regression and short-domain behavior, plus a fresh-session end-to-end probe.
PROOF:
- RED: test_live_meta_language_prefers_specific_current_index_skill failed with broad index 0 and specific index 1.
- GREEN: all 9 tests passed in 0.032s; pvg verify passed with 0 issues.
- Local live-style output: supabase-rls-frontend-debugging 0.7407, design-taste-frontend 0.7251, supabase 0.7000.
- Fresh Codex process output: top candidate supabase-rls-frontend-debugging; event count 18 -> 19; duration_ms 16.
- Short prompt output: supabase 0.9621, mcp-supabase 0.9598, supabase-postgres-best-practices 0.9167.
- Changed hashes: hook.py 0ab241c78f0df5c4f6486d21582117b2493c0256b02d01a3d33b51e2fa11f494; test_router.py 28f1725a9ec63aef2a172566d18ffc241e23824ce1043b5731f16e46783d2157.
- No network, prompt persistence, hook-registration, or skill-execution code was added.

LEARNINGS:
- A one-token exact-domain-name boost can override superior symptom coverage in longer instrumentation prompts.
- Capping the one-token exact-name boost at 0.70 preserves useful short-domain suggestions while allowing detailed candidates to win.
- Fresh-session verification is necessary because score behavior can differ when diagnostic prompts include router-test meta-language.

## nd_contract
status: delivered

### evidence
- RED/GREEN test output, pvg verify, local hook probes, fresh Codex process output, event log delta, and hashes recorded above.

### proof
- [x] AC #1: live-style regression test added and first observed failing.
- [x] AC #2: supabase-rls-frontend-debugging ranks above supabase.
- [x] AC #3: short domain prompt still returns Supabase candidates.
- [x] AC #4: full suite passes 9/9.
- [x] AC #5: pvg verify reports zero issues.
- [x] AC #6: only scoring and tests changed; no network/persistence/registration/execution behavior added.

## nd_contract
status: in_progress

### evidence
- Claimed 2026-09-19 under the same machine-global infrastructure exception as WD-59q6: changes are confined to /Users/speed/.codex/skill-router and no repository story worktree applies.
- Do not poll pvg loop next during implementation because the orphan-worktree heuristic resets this global-config task.

### proof
- [ ] Ranking regression and verification pending.

## History
- 2026-09-19T02:49:20Z status: open -> in_progress
- 2026-09-19T02:49:20Z claimed by dev-WD-o1xf
- 2026-09-19T02:53:23Z status: in_progress -> in_progress
- 2026-09-19T02:53:56Z status: in_progress -> closed

## Links
- Parent: [[WD-dic4]]

## Comments

### 2026-09-19T02:53:23Z speed
## Implementation Evidence (DELIVERED)

Commands run:
 - /usr/bin/python3 -m unittest discover -s /Users/speed/.codex/skill-router -p 'test_router.py' -v
 - pvg verify /Users/speed/.codex/skill-router/hook.py /Users/speed/.codex/skill-router/test_router.py --format=text
 - Fresh Codex app-bundle exec verification with one-time reviewed hook-trust bypass
Summary: 9/9 tests PASS, 0 failures, 0 errors, 0 skipped; pvg verify PASS with 0 issues; fresh-session top candidate supabase-rls-frontend-debugging; automatic event added; duration 16 ms; short-domain behavior preserved.
Commit SHA: b53f655eb88f67c11dbef361349bf8fb7d40d7a885126bc1c3bb66d30967ec96

## nd_contract
status: delivered

### evidence
- Deterministic local scoring change capped one-token exact-name boosts at 0.70; regression and short-domain tests added.

### proof
- [x] AC #1: live-style regression test added and reproduced the defect before the fix.
- [x] AC #2: specific Supabase RLS skill now outranks broad Supabase skill.
- [x] AC #3: short domain prompt still returns Supabase.
- [x] AC #4: 9/9 tests pass.
- [x] AC #5: pvg verify zero issues.
- [x] AC #6: no network, persistence, registration, or skill-execution behavior added.
