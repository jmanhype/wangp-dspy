# Finding #51 — repository-identity test is pinned to one workstation path

## Status

Confirmed 2026-09-13 during isolated source-only validation of the #50 repair.
Test-only fix implemented and independently verified in both checkouts. It is
committed as `e258e85` and pushed on `codex/golden-v3-lf003-repro`, separately
from #50's render/conditioning repair.

## What was needed

Run the full suite in a checkout at a different filesystem location, without
copying the operator's untracked media, queue databases or experimental scripts.
The identity assertion must prove the actual checkout and SHA, not enforce
the original workstation's path spelling.

## Observed failure

A local clone at HEAD `23dd219ff76b406f8d41d81ea4f66583f936d966`, overlaid with
the candidate's current tracked edits and 11 explicitly selected new repair
files, collected 1,314 tests: **1,312 passed, 1 failed, 1 skipped**.

Only `tests/test_run_identity.py::test_repository_identity_resolves_repo_root_and_head`
failed. Its expected root was the literal
`/Users/Shared/HermesWorkspace/wangp-dspy`; the actual correctly resolved root
was `/private/tmp/wangp-parity-source-only-20260913-bJlI0Z`.

Original failing evidence is retained at:

- `/tmp/wangp-parity-source-only-20260913-bJlI0Z/pytest-stdout.log`
- `/tmp/wangp-parity-source-only-20260913-bJlI0Z/test-results.xml`
- `/tmp/wangp-parity-source-only-result-20260913.json`

## Root cause and minimal PR

`services/director/run_ledger.py::repository_identity()` already resolves its
default from the package checkout, not the process working directory, then
reads the canonical root and HEAD via Git. The production function returned
the right answer. The test at `tests/test_run_identity.py:13` encoded a single
machine's checkout path as if it were the invariant.

The minimal PR changes only that test module and this finding:

1. Compare the identity to the canonical checkout containing the code and to
   its actual Git HEAD, retaining SHA format checks.
2. Change cwd to a non-repository directory and verify that the default still
   identifies the package checkout.
3. Pass an explicit second local clone and verify its canonical root and SHA.
4. Keep the existing outside-Git fail-closed test; do not bypass identity checks
   or modify production identity behavior.

## Validation scope

The isolated candidate used the existing Python environment and overlaid the
then-uncommitted source, including disclosed pre-existing changes. It was a
source-portability test, **not** a clean-dependency install, fresh-clone GPU
acceptance, or a new creative-quality verdict. No GPU work was needed to
discover this failure, and no original render evidence was changed.

## Fix verification — 2026-09-13

The changed module now checks the package checkout against its canonical Git
root and exact HEAD. The cwd-independence and second-local-clone regressions
were added; the original outside-Git rejection remains. Production
`services/director/run_ledger.py` is unchanged.

The orchestrator independently ran the complete suite after reviewing the
delegated test fix:

- Working checkout: **1,315 passed, 1 skipped**, zero failures/errors.
- Isolated source-only checkout: **1,315 passed, 1 skipped**, zero failures/errors.
- Both runs collected 1,316 tests, including all five identity tests.

The original failing run is retained, not overwritten. Final JUnit files are
`/tmp/wangp-parity-root-verified-20260913.xml` and
`/tmp/wangp-parity-isolated-verified-20260913.xml`; archival evidence is grouped
under `datasets/runs/provenance/v3-parity-release-check-20260913/`.

**PR boundary:** this test-only correction remains separately reviewable from
#50. Passing it does not reclassify any film verdict; the implementation is
published on `codex/golden-v3-lf003-repro` and is not merged to `main`.
