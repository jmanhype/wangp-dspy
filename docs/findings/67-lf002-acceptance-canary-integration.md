# 67 — LF002 reproduction did not enforce its golden canary

Status: OPEN; source repair staged for review.

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
- persist the canary report in the run’s ignored pull namespace;
- preserve caller-supplied artifact paths in reports;
- republish the committed canary with repository-relative paths;
- repoint scene provenance to the committed fresh bundle;
- normalize report-write failures to `LF002CanaryError`.

The acceptance record now carries the mandatory canary result. A run that
requests the LF002 golden contract cannot complete with mismatched bytes.
