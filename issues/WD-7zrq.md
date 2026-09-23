---
id: WD-7zrq
title: "pvg story verify-delivery is unsatisfiable with the append-notes API"
status: open
priority: 2
type: task
created_at: 2026-09-21T18:26:11Z
created_by: speed
updated_at: 2026-09-23T16:04:26Z
content_hash: "sha256:4a5884a3f9bbc9ffee1b57440be9ef2f90fd0b0020277f0f2f2433809036f916"
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


## History


## Links
## Comments
