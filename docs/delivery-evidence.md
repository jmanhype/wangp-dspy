# Delivery evidence contract

This document records the exact shape a story's notes must have before
`pvg story verify-delivery <story-id>` will report `Passed: 9, Failed: 0`, and the
procedure that reliably produces that shape. It exists because the checks are
literal: three deliveries in this repository were rejected or delayed by notes that
contained the right facts in the wrong shape.

## Tool boundary

`pvg` is a compiled binary installed on `PATH`. Its check list and its note
ordering behaviour are properties of that binary, not of this repository's code, and
cannot be changed from here. What follows is the contract as **verified against the
`pvg` shipped alongside this repository** (nine checks, reproduced repeatedly while
closing out epic `WD-t741`). If a future `pvg` changes the vocabulary, this document
must be updated with the new observed behaviour — the guard test in
`tests/test_delivery_evidence_doc.py` fails if the vocabulary recorded here drifts.

## The nine checks

`pvg story verify-delivery` evaluates exactly these items, in this order:

| Check | What it requires | Literal the verifier actually matches |
| --- | --- | --- |
| `label:delivered` | The story carries the `delivered` label (added by `pvg story deliver`) | n/a — tool-managed |
| `nd_contract:last_block` | The **last** `## nd_contract` block in the issue file has `status: delivered` | `status: delivered` |
| `nd_contract:eof` | That authoritative contract block is not followed by stray note content | n/a — layout |
| `notes:implementation_evidence` | An implementation-evidence section exists | `## Implementation Evidence` |
| `notes:ci_test_results` | A CI/test-results section exists, as a third-level heading | `### CI/Test Results` — `### Test Results` is also accepted |
| `notes:commands_run` | A commands-run list exists | `Commands run:` — a lowercase `commands run:` is also accepted |
| `notes:summary` | A summary line exists | `Summary:` at the start of a line |
| `notes:commit_sha` | A commit SHA is recorded | `SHA: <7-40 hex>` — case-insensitive (upper or lower) |
| `proof:ac_items` | Acceptance-criteria verification exists | an exact `### AC Verification` heading **or** a checklist line beginning `[x] AC` |

Two of these are easy to get wrong and cost a round trip:

- `proof:ac_items` does **not** match a table header. Writing
  `| AC | Result | Evidence |` alone does not satisfy it. The check is satisfied by
  the exact `### AC Verification` heading (which is why the recommended shape keeps
  that heading and puts the readable table underneath it) or by proof lines written
  as `[x] AC #1: ...` at the start of a line.
- `notes:commit_sha` accepts upper-case hex, and `notes:ci_test_results` /
  `notes:commands_run` accept their alternate spellings above.
- `notes:commit_sha` validates the **shape** of the SHA, not its identity. The check
  cannot tell whether the recorded SHA is the head you actually delivered. Every
  rework therefore invalidates the recorded SHA: after any new commit, update the
  `SHA:` line **and** any head reference in the evidence block to the new head
  before re-delivering. (This contract was itself rejected once for a stale head.)

### Patterns observed from the shipped binary

These are the patterns the installed `pvg` matches (extracted from the binary while
closing out this epic), recorded so the document can be checked against reality
rather than against memory:

```text
(?m)^## Implementation Evidence$
(?m)^### (CI/Test Results|Test Results)$
(?m)^(Commands run:|commands run:)\b
(?m)^Summary:
(?m)SHA: [0-9a-fA-F]{7,40}
(?m)(^\[x\] AC|^### AC Verification$)
```

Anything not in this list does not help, and a check whose literal is missing fails
even when the underlying fact is true.

## Required notes shape

Deliver with a single notes block in this shape (the literals in the left column
above must appear verbatim):

```markdown
## Implementation Evidence

Summary: one sentence naming what changed and what proves it.

Commands run:
- `uv run --frozen --extra dev pytest <targeted test> -q` -> exit 0, N passed.
- `uv run --frozen --extra dev pytest -q` -> exit 0, parsed JUnit counters.

SHA: 0123456789abcdef0123456789abcdef01234567

### CI/Test Results

- Exact-head CI check `test` at `<sha>`: completed/success.
- Targeted suite: parsed counters; full suite: parsed counters.

### AC Verification

| AC | Result | Evidence |
| --- | --- | --- |
| 1. <criterion> | PASS | <command output or artifact digest> |

## nd_contract
status: delivered

### evidence
- <what was delivered, at which head, with which CI result>

### proof
- [x] AC #1: <verifiable statement>
```

## The ordering caveat

`pvg nd update --append-notes` does **not** guarantee that the appended text lands
physically last in the issue file: content can be inserted before trailing
`## nd_contract` blocks. Because `nd_contract:last_block` reads the *last* contract
block in the file, a correct-looking notes block can still fail if an older contract
block follows it.

Reliable procedure used in this repository:

1. Author the notes block above (all nine literals present) and deliver.
2. Check which contract block is physically last:
   `grep -n "^## nd_contract" .git/paivot/nd-vault/issues/<STORY>.md | tail -1`.
3. If the last block is not your `status: delivered` block, append a fresh
   `## nd_contract` block with `status: delivered` as the final note, or correct the
   trailing block in place, then re-run the verifier.
4. Re-run `pvg story verify-delivery <STORY>` until it reports `Passed: 9, Failed: 0`.

Never reorder or rewrite unrelated historical notes to satisfy the check; only the
authoritative (last) contract block needs to be correct.

## The post-acceptance caveat

`pvg story accept` closes the story and intentionally drops the `delivered` label
(status/label mapping: accepted -> closed + `accepted`). A re-run of
`pvg story verify-delivery` after acceptance therefore reports `Passed: 8, Failed: 1`,
with the single failure being `label:delivered -- missing 'delivered' label`. That is
expected: the nine-check result is a **pre-acceptance** gate proving the delivery is
reviewable, not a permanent property of a closed story. Record the 9/9 result in the
story notes at delivery time (as the worked example does) so it remains auditable.

## Working example

A delivery that satisfied all nine checks in this repository (epic `WD-t741`,
capstone `WD-gc09`) carried, as its last note:

```markdown
## nd_contract
status: delivered

### evidence
- Head 841625de02446ae2d98e5a8024fae29c29e28702; exact-head CI check `test` completed/success.
- Targeted editor suite 5 passed; README drift 5 passed; full suite 1972 tests, 0 failures, 1 skipped.

### proof
- [x] Project create/save/reopen round-trip preserves every source hash and prior decision.
- [x] Mutated source fails typed at exit 2 with no partial output; repeated export is byte-identical.
```
