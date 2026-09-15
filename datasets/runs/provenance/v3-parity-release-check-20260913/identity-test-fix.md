# Run-identity test portability fix — 2026-09-13

## Scope

- Owned repository edit: `tests/test_run_identity.py` only.
- Temporary verification edit: the identical fixed test was overlaid with `apply_patch` into `/tmp/wangp-parity-source-only-20260913-bJlI0Z/tests/test_run_identity.py`.
- No production code was edited.
- No commit, push, fetch, network operation, SSH operation, GPU work, inference, or new Git commit was performed.

## Fix

The default identity test no longer hardcodes `/Users/Shared/HermesWorkspace/wangp-dspy`. It now:

1. Anchors the expected checkout to the resolved checkout containing `services/director/run_ledger.py`.
2. Uses Git `rev-parse --show-toplevel` for the canonical expected root.
3. Compares the returned SHA to the actual Git `rev-parse HEAD`, not only to a 40-character lowercase-hex pattern.
4. Retains the 40-character lowercase-hex validation.

Added regressions:

- Changing the process cwd to a temporary non-repository does not change the default repository identity.
- An explicit other checkout is made with local `git clone --no-hardlinks`; its identity root resolves to the clone and its HEAD equals the source HEAD.
- The existing outside-Git fail-closed test remains unchanged.

The explicit-clone test was corrected before execution to anchor its source checkout with `Path(__file__).resolve().parents[1]` (the repository root for a test file).

## Test execution

Python interpreter (absolute original-tree path):

`/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python`

### Original checkout

- Root: `/Users/Shared/HermesWorkspace/wangp-dspy`
- HEAD: `23dd219ff76b406f8d41d81ea4f66583f936d966`
- Result: **5 passed**
- Log: `/tmp/wangp-identity-test-fix-20260913-local.log`
- JUnit XML: `/tmp/wangp-identity-test-fix-20260913-local.xml`

### Isolated source-only candidate

- Root: `/private/tmp/wangp-parity-source-only-20260913-bJlI0Z`
- HEAD: `23dd219ff76b406f8d41d81ea4f66583f936d966`
- Result: **5 passed**
- Log: `/tmp/wangp-identity-test-fix-20260913-candidate.log`
- JUnit XML: `/tmp/wangp-identity-test-fix-20260913-candidate.xml`

## Hashes

- Original fixed test (`tests/test_run_identity.py`): `69300dfd52946dcf929edf39b72c9e6117bb565f05d2c4fb70fdf4da99367595`
- Candidate fixed test (`tests/test_run_identity.py`): `69300dfd52946dcf929edf39b72c9e6117bb565f05d2c4fb70fdf4da99367595`
- Original `services/director/run_ledger.py`: `60987fe28e051de096addc3ac556cf08e868e8e6bbc2e3bb4d0e502dfeb7e0ce`
- Candidate `services/director/run_ledger.py`: `60987fe28e051de096addc3ac556cf08e868e8e6bbc2e3bb4d0e502dfeb7e0ce`
- Original test log: `04ebcdc5fc5f78ba983483f0dbda97a1f4d9b23310e2f8f526a71e9ad9082128`
- Original JUnit XML: `4339e62be7a71be93c5b9b4f115cba8a11831614f2edf74efed3211b5e611825`
- Candidate test log: `65d5c02a400f69e8c3e662ccf1ab2ffaf32e209410c2e956182694fa341370ad`
- Candidate JUnit XML: `387034581b5203ffdd3c48403425110f3f5e39e2a18dd3f7727428c7793db5a6`

The original and candidate fixed test files are byte-identical.
