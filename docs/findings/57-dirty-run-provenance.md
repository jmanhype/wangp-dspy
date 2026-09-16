# 57 — dataset runs record HEAD but not dirty-tree state

Status: CLOSED in PR #87 / commit `08237d2`; dirty-tree provenance and the
clean-tree default are on `main`.

## Evidence

The operator-accepted LF002 run was generated through repo-owned code, but the
working tree contained uncommitted repairs. Its dataset-run record named commit
`5da39d5` without a tracked-diff hash or dirty/clean state, so the commit SHA
alone could not reconstruct the executing source.

## Minimal fix

Extend repository identity and every append-only dataset-run record with:

- `clean_tree` / `dirty_tree`;
- SHA-256 of `git status --porcelain`;
- SHA-256 of the tracked diff versus `HEAD`;
- changed-path and untracked-path counts.

The acceptance runner defaults to a clean tree. A dirty experimental run
requires both:

```text
WANGP_ALLOW_DIRTY_RUN=1
WANGP_DIRTY_RUN_REASON=<non-empty operator-approved reason>
```

The reason and full provenance are persisted in the completed run record.

## Resolution

Repository identity and acceptance-run gating landed with coverage in
`tests/test_run_acceptance.py` and `tests/test_run_identity.py`. Finding #66
later completed canonical dataset-run emission and untracked-content hashing.
The full suite at `9b70be1` passed 1380 tests with one intentional skip and no
failures.
