---
id: WD-9ymi
title: "Story workflow accepts a delivered story with a blank formal AC section"
status: open
priority: 0
type: bug
labels: [discovered-by-pm]
parent: WD-3nod
created_at: 2026-09-26T17:07:01Z
created_by: speed
updated_at: 2026-09-26T17:08:36Z
content_hash: "sha256:a32df0b20694de807311aa026f84cac3cef6aa611c344deb9d03a992724c9b1e"
---

## Description

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

No `blocks WD-fay0` dependency is added. This is a governance/workflow defect, not missing Maestro-parity evidence; WD-fay0's consolidated evidence contract can still consume the accepted lane artifacts. The guard must prevent future acceptances rather than invalidate the existing capstone linkage.

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

## Design


## Notes


## History


## Links
- Parent: [[WD-3nod]]

## Comments

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

No `blocks WD-fay0` dependency is added. This is a governance/workflow defect, not missing Maestro-parity evidence; WD-fay0's consolidated evidence contract can still consume the accepted lane artifacts. The guard must prevent future acceptances rather than invalidate the existing capstone linkage.

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

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-3nod]]

## Comments
