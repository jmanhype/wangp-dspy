# 67 — LF002 reproduction did not enforce its golden canary

Status: CLOSED in PR #98 / commit `3a95d79`; the LF002 golden canary is a
mandatory acceptance gate on `main`.

## Evidence

Qodo review of PR #88 found four reproduction-contract gaps:

1. the documented fresh-run command did not compare generated artifacts to
   the pinned LF002 hashes;
2. the canary report used machine-specific absolute artifact paths and could
   dirty a clean checkout;
3. scene provenance referenced an unpublished `staging.json`;
4. report filesystem errors escaped as uncaught `OSError`.

## Minimal fix

- add an explicit `golden_canary` block to the LF002 fresh bundle;
- validate the pinned recipe version before staging or queueing;
- invoke `verify_lf002_canary` after assembly and before recording completion;
- verify raw cut 1, raw cut 2, assembled pair, and chain frame hashes;
- assemble sibling raw cuts locally (see Finding #70: remote ffmpeg changes
  the pinned pair container);
- persist the canary report in the run’s ignored pull namespace;
- preserve caller-supplied artifact paths in reports;
- republish the committed canary with repository-relative paths;
- repoint scene provenance to the committed fresh bundle;
- normalize report-write failures to `LF002CanaryError`.

The acceptance record now carries the mandatory canary result. A run that
requests the LF002 golden contract cannot complete with mismatched bytes.

## Resolution

The committed LF002 fresh bundle carries `golden_canary`, the runner invokes
`predict.lf002_canary.verify_lf002_canary` after assembly, and report errors
are typed. Regression coverage is in `tests/test_lf002_canary.py` and
`tests/test_run_acceptance.py`. The committed strict single-ledger evidence
records `passed: true` with no errors. The full suite at `9b70be1` passed 1380
tests with one intentional skip and no failures.
