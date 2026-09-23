---
id: WD-7zrq
title: "pvg story verify-delivery is unsatisfiable with the append-notes API"
status: open
priority: 2
type: task
created_at: 2026-09-21T18:26:11Z
created_by: speed
updated_at: 2026-09-23T17:25:08Z
content_hash: "sha256:e3ba6ae7709b9c45c6258bc6f3a3238a77dd8845669166a8327d45bb6624a5a7"
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

SHA: e9aba21ebe0028a6906c4b4c0dfea528fee3df7c

### CI/Test Results

- Exact-head CI check `test` at e9aba21: recorded in the PR (see #176); the guard suite and the README drift suite both pass locally at that head.
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
- Head e9aba21ebe0028a6906c4b4c0dfea528fee3df7c on story/WD-7zrq; PR #176; guard suite 8 passed locally at that head.
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

## Links
## Comments
