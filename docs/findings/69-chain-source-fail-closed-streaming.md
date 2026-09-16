# 69 — chain-source hashing still trusted remote-only bytes

Status: CLOSED in PR #100 / commit `ff1bf2a`; fail-closed streaming chain-source
identity is on `main`.

## Evidence

Qodo review of PR #90 found two follow-up gaps:

1. when the accepted local MP4 was absent, an existing remote file was treated
   as current without any artifact identity;
2. the local digest loaded the entire MP4 into memory.

## Minimal fix

Require the accepted local chain source to exist and fail closed if it does
not. Hash that source with `hashlib.file_digest` over a binary file handle,
then compare it to the mapped remote artifact and the post-push verification
hash.

## Regression coverage

Tests now prove:

```text
missing local source + occupied remote path → WiringError, no extraction
matching local/remote hashes                   → no whole-MP4 Path.read_bytes
```

## Stack verification

The complete #62–#69 source-only follow-up stack passed:

```text
1375 tests
0 failures
0 errors
1 skipped
```

Evidence:
`datasets/runs/provenance/qodo-followups-20260916/fullsuite.xml`.

## Resolution

`services/director/wiring.py` requires the accepted local chain source,
hashes it with `hashlib.file_digest`, and verifies remote identity before
extraction. Regression coverage is in `tests/test_director_wiring.py`; the
committed stack-suite JUnit remains available. The full suite at `9b70be1`
passed 1380 tests with one intentional skip and no failures.
