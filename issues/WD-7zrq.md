---
id: WD-7zrq
title: "pvg story verify-delivery is unsatisfiable with the append-notes API"
status: closed
priority: 2
type: task
created_at: 2026-09-21T18:26:11Z
created_by: speed
updated_at: 2026-09-23T18:06:24Z
content_hash: "sha256:6252a19b32c83313d0b567cfacdb28d1abfb04f1df2188a8d99a140f11c76247"
labels: [rejected-x2, accepted]
closed_at: 2026-09-23T18:06:24Z
close_reason: "Accepted at 5a815c92252e151b039804bb856b09898fd16f7c: exact matcher contract, three verified caveats, matching story SHA/head, 8 targeted tests, and successful exact-head CI."
---

## Description
## USER INTENT
A user can run `pvg story verify-delivery` after using the documented note API and see the verifier accept the honest delivery evidence without manual note reordering.

## Symptom
`pvg story verify-delivery` cannot be satisfied using the documented append API, because `pvg nd update --append-notes` PREPENDS new content to the Notes section. The authoritative `## nd_contract` block (the newest one) therefore always lands before older note content, so the `nd_contract:eof` check can never pass once any earlier note exists.

## Measured evidence
Three consecutive deliveries hit the same three checks while the underlying values were present in the notes:

```text
[FAIL] nd_contract:eof -- authoritative contract is not at EOF
[FAIL] notes:ci_test_results -- missing CI/Test Results section
[FAIL] notes:commit_sha -- missing commit SHA
```

- WD-m1sj at `5dadcda`: 5 passed / 4 failed, including `nd_contract:eof`.
- WD-fp49 at `4aa2e92`: 6 passed / 3 failed, same three checks.
- Reading `pvg nd show <id>` shows newest-appended content FIRST and the oldest `## nd_contract` block physically last, confirming the prepend behaviour.
- The literal-string expectations are not documented in the developer skill or the story template: the verifier wants an exact `### CI/Test Results` heading and an exact `Commit SHA:` label, and no shipped template tells authors this.

## Impact
Every story delivery costs an extra round trip, and authors are pushed toward `pvg nd edit` (interactive `$EDITOR`) to reorder notes — which has previously corrupted an accumulated body in this repository. It also makes an honest delivery look incomplete to the PM acceptor, which is exactly the signal the check exists to provide.

## Scope
Either make note appends land after existing content (append semantics that match the name), or teach the verifier to treat the newest `nd_contract` block as authoritative regardless of physical position, and document the required note labels in the developer/story template.

## Out of scope
- Changing any product behaviour.
- Rewriting historical story notes.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Reproduced from `pvg story verify-delivery` output on WD-m1sj and WD-fp49, with `pvg nd show` ordering evidence.

### proof
- [ ] Pending: append semantics or verifier expectations reconciled, and the required labels documented.

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-23.

### proof
- [x] Story closed after accepted label was applied.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## nd_contract
status: delivered

### evidence
- Final head `5a815c92252e151b039804bb856b09898fd16f7c` on story/WD-7zrq (PR #176). Exact-head CI check `test` id 107305667334: completed/success.
- SECOND REJECTION (stale head): the previous re-delivery corrected the verifier patterns but left the authoritative contract recording `SHA: e9aba21e…` and `Head e9aba21e…` while the branch head was already `e81745ce…`. The verifier's `(?m)SHA: [0-9a-fA-F]{7,40}` check validates shape only and cannot detect a stale head, so this had to be fixed by hand.
- Fix: every head reference in this contract now names the delivered head, and the document itself now carries the lesson — `docs/delivery-evidence.md` states that the SHA check proves shape, not identity, and that any rework invalidates the recorded SHA and every head reference. `tests/test_delivery_evidence_doc.py` asserts that caveat so it cannot be dropped.
- Guard suite and README drift suite: 8 passed locally at this head; full suite green in CI at this head.

### proof
- [x] The nine checks and their exact literals are documented verbatim, including `(?m)(^\[x\] AC|^### AC Verification$)` for `proof:ac_items` and the alternate CI/commands spellings.
- [x] The document states that a `| AC | Result | Evidence |` table header alone does NOT satisfy the acceptance check.
- [x] The document states that the SHA check validates shape, not identity, and that a rework must update the recorded SHA and every head reference.
- [x] The append-ordering caveat and the post-acceptance 8-of-9 caveat are documented with their causes.
- [x] The guard test fails if any check name, literal, caveat or worked-example property disappears.
- [x] CONTRIBUTING.md and the README documentation index link the contract; no product code or protected engine file changed.

## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-09-23.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Rework Evidence

Rejection (independent acceptor): the first version documented inexact literals. Verified against the shipped binary, the real patterns are:

```text
(?m)^## Implementation Evidence$
(?m)^### (CI/Test Results|Test Results)$
(?m)^(Commands run:|commands run:)\b
(?m)^Summary:
(?m)SHA: [0-9a-fA-F]{7,40}
(?m)(^\[x\] AC|^### AC Verification$)
```

The material error was `proof:ac_items`: a `| AC | Result | Evidence |` table header alone does not satisfy it. It is satisfied by the exact `### AC Verification` heading (which every delivery in this repository happened to include) or by checklist lines beginning `[x] AC`. The check also accepts `### Test Results`, a lowercase `commands run:`, and upper- or lower-case hex in the SHA.

Fix at head e81745ceaf312e967d27de0f27cfdec088f187be: the document now records the observed patterns verbatim, states explicitly that the table is presentation underneath the heading rather than the matched literal, and lists the accepted alternates. The guard test now asserts each of those facts (including the `### AC Verification` literal and the `[x] AC` form) so the contract cannot drift back to an inexact statement.

Also corrected in the first version and still true: the recorded `SHA:` is the real head, not a placeholder.

## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-09-23.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Summary: documented the nine-check delivery-evidence contract (`docs/delivery-evidence.md`), added a drift guard (`tests/test_delivery_evidence_doc.py`) that pins the check names, literals and caveats and proves the worked example is itself a valid delivered contract, and linked the document from `CONTRIBUTING.md` and the README documentation index.

Commands run:
- `uv run --frozen --extra dev pytest tests/test_delivery_evidence_doc.py tests/test_readme_quickstart.py -q` -> exit 0, 8 passed.
- `git diff main..HEAD --name-only` -> docs/delivery-evidence.md, CONTRIBUTING.md, README.md, tests/test_delivery_evidence_doc.py.

SHA: 5a815c92252e151b039804bb856b09898fd16f7c

### CI/Test Results

- Exact-head CI check `test` id 107305667334 at 5a815c92252e151b039804bb856b09898fd16f7c: completed/success (PR #176).
- Targeted: 8 passed / 0 failed / 0 errors; full-suite result recorded with the PR.

### AC Verification

| AC | Result | Evidence |
| --- | --- | --- |
| 1. The exact checks and literals are documented | PASS | docs/delivery-evidence.md lists all nine checks and every required literal verbatim. |
| 2. The reliable procedure is documented | PASS | Ordering procedure and the post-acceptance 8/9 caveat are recorded, with the observed cause. |
| 3. The document cannot silently drift | PASS | tests/test_delivery_evidence_doc.py asserts the checks, literals, caveats and example shape. |
| 4. The contract is discoverable | PASS | CONTRIBUTING.md and the README documentation index both link it; README drift test still passes. |
| 5. No product behaviour changes | PASS | Documentation, test and two link lines only; no `wangp/`, gate, queue or renderer change. |

## nd_contract
status: delivered

### evidence
- Head 5a815c92252e151b039804bb856b09898fd16f7c on story/WD-7zrq; PR #176; guard suite 8 passed locally at that head; exact-head CI `test` completed/success.
- The document records the tool boundary explicitly: the check vocabulary and note ordering belong to the compiled `pvg` binary, and this document is the verified contract for the shipped version.

### proof
- [x] The nine checks and their exact literals are documented verbatim.
- [x] The append-ordering caveat and the post-acceptance 8-of-9 caveat are documented with causes.
- [x] A drift guard fails if any check name, literal, caveat or worked-example property disappears.
- [x] CONTRIBUTING.md and the README documentation index link the contract.
- [x] No product code, gate, queue, renderer or protected engine file changed.

## History
- 2026-09-23T16:34:00Z status: open -> in_progress
- 2026-09-23T16:34:00Z claimed by dev-WD-7zrq
- 2026-09-23T16:37:28Z status: in_progress -> in_progress
- 2026-09-23T17:25:08Z status: in_progress -> open
- 2026-09-23T17:25:08Z released by speed
- 2026-09-23T17:27:13Z status: open -> in_progress
- 2026-09-23T17:42:39Z claimed by dev-WD-7zrq
- 2026-09-23T17:42:39Z status: in_progress -> open
- 2026-09-23T17:42:39Z released by speed
- 2026-09-23T18:05:20Z status: open -> in_progress
- 2026-09-23T18:06:24Z status: in_progress -> closed

## Links
## Comments

### 2026-09-23T17:25:08Z speed
REJECT: the literal contract is inaccurate. Installed pvg 1.64.0 matches notes:ci_test_results with ^### (CI/Test Results|Test Results)$, notes:commands_run with ^(Commands run:|commands run:), notes:commit_sha with SHA: [0-9a-fA-F]{7,40}, and proof:ac_items with ^[x] AC or ^### AC Verification$; the document/guard instead present the table header | AC | Result | Evidence | as the exact matched literal, omit ### AC Verification from REQUIRED_LITERALS, and describe SHA as lowercase-only. Documentation-only resolution is acceptable in principle because pvg is external, but this story requires the documented and guarded contract to match the shipped verifier.

### 2026-09-23T17:42:40Z speed
REJECT at e81745ceaf312e967d27de0f27cfdec088f187be: the code/document delta corrects the verifier patterns, but the re-delivery notes still record SHA: e9aba21ebe0028a6906c4b4c0dfea528fee3df7c and Head e9aba21e... from the rejected delivery. The actual branch head is e81745ceaf312e967d27de0f27cfdec088f187be. verify-delivery's 9/9 only validates the SHA pattern, not head identity; update the delivery evidence to the new head and re-deliver.
