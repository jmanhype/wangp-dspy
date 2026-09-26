---
id: WD-9ymi
title: "Story workflow accepts a delivered story with a blank formal AC section"
status: open
priority: 0
type: bug
labels: [discovered-by-pm, delivered]
parent: WD-3nod
created_at: 2026-09-26T17:07:01Z
created_by: speed
updated_at: 2026-09-26T18:30:19Z
closed_at: ""
close_reason: ""
content_hash: "sha256:d278a2461e294ed4040e0e33c62002e09b155219477cc6ea0f845b6fd2b13a61"
blocks: [WD-fay0]
follows: [WD-9t9o, WD-isg9]
---
## Description
## Context

The shared tracker's accepted WD-9t9o record has a detailed Description but its formal `## Acceptance Criteria` section is blank. Nevertheless, WD-9t9o was delivered and accepted on 2026-09-26, and its delivery notes contain an informal seven-row AC verification table derived from Description text.

Measured current behavior:

- `pvg issues show WD-9t9o --json` shows status `closed`, labels `capability`, `evidence`, `accepted`, parent `WD-3nod`, and a body whose formal `## Acceptance Criteria` section has no criteria.
- Before this bug was created, `pvg lint --backlog` scanned 132 issues and passed with 0 errors and 0 review findings.
- Current post-acceptance `pvg story verify-delivery WD-9t9o` reports 8 checks passed and 1 failed. The only failure is `label:delivered -- missing 'delivered' label`, which is expected after acceptance closeout. The command reports `proof:ac_items` as OK even though the formal story AC section is blank, because the delivered contract/evidence table contains AC-like items.

This means acceptance can proceed from delivery evidence and an expressive Description while the formal story contract remains empty. That undermines reproducible review: a future reader cannot tell which criteria were authoritative at story creation, which were reconstructed during delivery, and whether PM acceptance evaluated the formal contract or only the delivered table.

## Root Cause

The exact implementation defect is not yet localized. The observed contract gap is that delivery verification validates AC-like proof items in the authoritative delivered contract, while backlog lint does not require a nonempty formal `## Acceptance Criteria` section in the story body. Story acceptance then trusts that delivered shape. This story must identify the relevant pvg/nd validation and transition paths and close the gap without rewriting accepted history.

## Affected Components

- Shared nd story record WD-9t9o, served through `pvg nd`/`pvg issues`.
- `pvg story verify-delivery` delivery-proof validation.
- `pvg lint --backlog` story-body structural validation.
- `pvg story deliver` and `pvg story accept` transition semantics.
- Paivot SrPM/developer/PM-acceptance contract discipline.

## Acceptance Criteria

- [ ] A story body with a blank formal `## Acceptance Criteria` section fails delivery verification or backlog lint before PM acceptance, even when Description text and a delivered AC verification table are present.
- [ ] A story with at least one concrete, testable formal AC item passes the new validation; blank, placeholder-only, and duplicate malformed AC sections fail with typed diagnostics.
- [ ] PM acceptance refuses to close a delivered story whose formal AC section is blank, and the failure names the story, section, and required repair rather than silently relying on delivery notes.
- [ ] Existing accepted/closed historical records, including WD-9t9o, are not retroactively rewritten; the fix applies to future create/deliver/accept transitions.
- [ ] Real-command tests cover the create-or-fixture, deliver, failed acceptance, repaired AC, and successful acceptance path using an isolated temporary shared nd vault; no test edits issue files directly.
- [ ] The existing backlog lint suite and targeted pvg/nd tests pass, and `pvg lint --backlog` reports 0 errors and 0 review findings after the change.

## Testing Requirements

- Unit tests: formal AC-section extraction, whitespace/placeholder rejection, nonempty testable-item detection, and backward-compatible parsing of legacy bodies.
- Integration tests: MANDATORY (no mocks). Drive the real `pvg issues`, `pvg story verify-delivery`, and acceptance transition commands against an isolated real nd vault fixture.
- Negative tests: detailed Description plus blank formal AC must fail; delivery-note AC items must not substitute for the formal section; malformed headings must not bypass validation.
- Historical-record test: an accepted fixture remains byte/content stable and is reported as legacy rather than mutated.
- Standing gates: targeted pvg/nd tests, full relevant pvg test suite if available, and `pvg lint --backlog`.

## Discovered During

Story WD-9t9o: PM triage found the tracker-visible formal Acceptance Criteria section blank after the story had passed delivery checks and been accepted.

## Capstone Impact

This bug blocks WD-fay0 at the governance gate. WD-fay0 requires a clean backlog lint gate and reliable future story acceptance; an open P0 sibling without the required capstone edge makes that gate fail, and the guard must be in place before remaining epic work is accepted. The consolidated evidence contract can still consume already accepted lane artifacts, so this blocker corrects governance rather than invalidating prior evidence.

## MANDATORY SKILLS

- pvg — reproduce story transitions, locate tool behavior, and update governance gates.
- nd — understand issue body/dependency semantics without directly editing vault files.

## Skills To Use

- pvg and nd for implementation and isolated-vault testing.
- tool-systematic-debugging before changing acceptance or lint semantics.

## nd_contract
status: new

### evidence
- Created: 2026-09-26 from the PM-supplied DISCOVERED_BUG report after directly inspecting WD-9t9o, running current backlog lint, and running post-acceptance delivery verification.

### proof
- [ ] Pending implementation

## Notes
## Implementation Evidence

Commands run:
- go test ./internal/lint ./internal/story ./cmd/pvg -count=1
- go test -cover -count=1 ./internal/lint ./internal/story ./cmd/pvg
- go test ./cmd/pvg -run TestFormalAcceptanceCriteriaIntegration -count=1 -v
- go test -count=1 ./...
- pvg verify changed source and changed integration tests --include-tests --check-mocks
- git diff --check; git diff --cached --check

Summary: targeted PASS (3/3 packages), full Go suite PASS (24/24 tested packages, 0 failures), integration PASS (1/1), pvg verify PASS, mock check PASS, whitespace PASS. Coverage: lint 94.0%, story 77.9%, cmd/pvg 6.7%.

Commit SHA: 98f5b1d6e8f6603d6e0ba2031e4cf3cce6e9f347

Detailed commands, outputs, wiring, AC table, historical WD-9t9o SHA evidence, safe isolated backlog lint, and DISCOVERED_BUG for WD-t0il are in the preceding DELIVERED evidence block.

## nd_contract
status: delivered

### evidence
- Commit 98f5b1d6e8f6603d6e0ba2031e4cf3cce6e9f347 pushed to fork story/WD-9ymi.
- All targeted, integration, full-suite, verify, mock, whitespace, safe-lint, and historical-record checks recorded above.

### proof
- [x] AC #1 through AC #6 verified in the preceding AC Verification table.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-26.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

PROOF:

### CI/Test Results
- Commands run:
  - `go test ./internal/lint ./internal/story ./cmd/pvg -count=1`
  - `go test -cover -count=1 ./internal/lint ./internal/story ./cmd/pvg`
  - `go test ./cmd/pvg -run TestFormalAcceptanceCriteriaIntegration -count=1 -v`
  - `go test -count=1 ./...`
  - `/tmp/pvg-WD-9ymi-verify verify internal/lint/backlog.go internal/story/story.go --format text`
  - `/tmp/pvg-WD-9ymi-verify verify internal/lint/formal_acceptance_test.go internal/story/formal_acceptance_test.go cmd/pvg/formal_acceptance_integration_test.go internal/story/story_test.go --include-tests --check-mocks --format text`
  - `git diff --check` and `git diff --cached --check`
- Summary: targeted PASS (3/3 packages), full Go suite PASS (24/24 packages with tests, 0 failures), integration PASS (1/1), source verify PASS, integration mock check PASS, whitespace checks PASS.
- Coverage: lint 94.0%; story 77.9%; cmd/pvg 6.7%.
- Key output:
  - Full suite: `ok github.com/paivot-ai/pvg/cmd/pvg` through `ok github.com/paivot-ai/pvg/internal/worktree`; 0 failing packages.
  - Source verify: `VERIFY: PASSED (2 files scanned, 0 issues)`.
  - Test verify/mock: `MOCK CHECK: PASSED (3 integration/e2e test files scanned, 0 mock usages)`.
  - Real isolated-vault integration drives `pvg issues`, blank-AC `story deliver`, `story verify-delivery`, failed `story accept`, `nd edit` repair, `lint --backlog`, repaired deliver/verify/accept, and a closed accepted legacy fixture. Its safe-backlog assertions require `PASSED: 0 error(s), 0 review finding(s)` before and after the legacy case.

### Commit
- Branch: `story/WD-9ymi`
- SHA: `98f5b1d6e8f6603d6e0ba2031e4cf3cce6e9f347`
- Fork remote verification: `git ls-remote fork refs/heads/story/WD-9ymi` returned the same SHA.
- Push: `git push fork story/WD-9ymi` created the branch at the SHA above.

### Wiring
- Shared typed formal-AC parser: `internal/lint/backlog.go:993-1173`.
- Lint gate wiring: `internal/lint/backlog.go:152` and `internal/lint/backlog.go:1155-1173`.
- Delivery/acceptance pre-mutation gates: `internal/story/story.go:120-137` and `internal/story/story.go:138-154`.
- Delivery report gate: `internal/story/story.go:304-318`.
- Real-command transition coverage: `cmd/pvg/formal_acceptance_integration_test.go:54-167`.

### pvg verify
- Changed source scan: `VERIFY: PASSED (2 files scanned, 0 issues)`.
- Changed test/integration scan: `MOCK CHECK: PASSED (3 integration/e2e test files scanned, 0 mock usages)`.

### Historical-record evidence
- Branch-built `pvg story verify-delivery WD-9t9o`: 8 passed, 2 failed (expected missing post-acceptance `delivered` label plus the new blank formal-AC diagnostic).
- Diagnostic includes: `WD-9t9o`, `"## Acceptance Criteria"`, required repair, and `legacy accepted record; not rewritten`.
- Body SHA-256 before/after verification: `e83f23d49ad0958ac62802b9432433b65b966fcb13717654db8c99b686b6b0ab`; unchanged=true.

### AC Verification
| AC | Requirement | Code Location | Test Location | Status |
|---|---|---|---|---|
| 1 | Blank formal AC cannot pass delivery verification/lint despite Description and delivered table | `internal/story/story.go:304-318`; `internal/lint/backlog.go:1050-1173` | `internal/story/formal_acceptance_test.go:46-76`; `cmd/pvg/formal_acceptance_integration_test.go:101-114` | PASS |
| 2 | Concrete AC passes; blank, placeholder-only, malformed heading, malformed items, and duplicates fail typed | `internal/lint/backlog.go:993-1153` | `internal/lint/formal_acceptance_test.go:9-134` | PASS |
| 3 | Acceptance refuses to close blank formal AC and names story, section, repair | `internal/story/story.go:138-154` | `internal/story/formal_acceptance_test.go:99-118`; `cmd/pvg/formal_acceptance_integration_test.go:116-120` | PASS |
| 4 | Accepted/closed history is not rewritten | `internal/story/story.go:304-318` | `internal/story/formal_acceptance_test.go:120-152`; `cmd/pvg/formal_acceptance_integration_test.go:149-167` | PASS |
| 5 | Real isolated-vault create/fixture, deliver, failed accept, repair, successful verify/accept coverage with no direct test issue-file writes | `cmd/pvg/formal_acceptance_integration_test.go` | Same file | PASS |
| 6 | Targeted/full tests and safe `pvg lint --backlog` pass | `internal/lint/backlog.go:152`; `cmd/pvg/formal_acceptance_integration_test.go:137-167` | Full-suite and isolated integration evidence above | PASS |

LEARNINGS:
- `nd` exposes the formal AC section as a manual-edit section; the integration repair uses `nd edit` (not a test write to the issue file) and then exercises the real pvg transitions.
- Delivery proof and the formal story contract had different parsers by design; sharing one typed validator at lint/story boundaries prevents the delivered-table substitution from diverging again.
- The live Wangp backlog now correctly exposes an existing deferred blank-AC record, WD-t0il. This is a tracker repair, not a reason to weaken the transition gate.

### DISCOVERED_BUG
  title: Existing deferred gate WD-t0il has a blank formal Acceptance Criteria section
  context: Branch-built `pvg lint --backlog` against the live Wangp shared vault scanned 134 issues and returned one error for WD-t0il: formal acceptance criteria section blank. WD-t0il is a deferred operator-authorization gate with contract proof items in Notes, but its formal section is blank. No tracker mutation was made.
  affected_files: Shared nd story WD-t0il (tracker record, not PVG source)
  discovered_during: WD-9ymi

## nd_contract
status: delivered

### evidence
- Commit `98f5b1d6e8f6603d6e0ba2031e4cf3cce6e9f347` pushed to fork branch `story/WD-9ymi`.
- Targeted, integration, full Go, pvg verify/mock, whitespace, safe lint, and historical WD-9t9o evidence recorded above.

### proof
- [x] AC #1: blank formal AC fails delivery verification/lint before PM acceptance.
- [x] AC #2: concrete AC passes; blank/placeholder/malformed/duplicate sections fail with typed diagnostics.
- [x] AC #3: acceptance refuses pre-close and names story, section, and repair.
- [x] AC #4: accepted/closed historical records are reported as legacy and left byte-stable.
- [x] AC #5: real isolated nd-vault integration covers create/fixture, failed deliver/accept, repair, lint, successful deliver/verify/accept, and history without direct issue-file writes.
- [x] AC #6: targeted/full tests pass and the isolated real backlog lint reports 0 errors/0 reviews.

## History
- 2026-09-26T17:13:27Z dep_added: blocks WD-fay0
- 2026-09-26T17:54:27Z status: open -> in_progress
- 2026-09-26T17:54:27Z auto-follows: linked to predecessor WD-9t9o
- 2026-09-26T17:54:27Z claimed by dev-WD-9ymi
- 2026-09-26T18:13:50Z status: in_progress -> in_progress
- 2026-09-26T18:13:50Z auto-follows: linked to predecessor WD-isg9
- 2026-09-26T18:30:19Z status: in_progress -> open
- 2026-09-26T18:30:19Z released by speed

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-9t9o]], [[WD-isg9]]

## Comments
