---
id: WD-i7nn
title: "Release probes can silently verify the real checkout instead of the mutated clone"
status: in_progress
priority: 2
type: bug
labels: [testing, release]
created_at: 2026-09-22T18:57:15Z
created_by: speed
updated_at: 2026-09-23T16:45:34Z
content_hash: "sha256:7b6c01e4028fff1498839bebd8f031e203a83e23fd6b83587cc959b6b141ddcd"
assignee: dev-WD-i7nn
---

## Description
## USER INTENT
Observable outcome: every negative-path release probe in `tests/test_release.py` is proven to have exercised the *mutated* clone. A probe that silently falls back to the real, unmutated checkout must fail loudly instead of returning exit 0.

## Context (Embedded)
- Observed once during a full-suite run of `tests/test_release.py` in the `dev-WD-bosd` worktree on 2026-09-22: `test_release_failure_matrix_is_typed_and_read_only` failed with `assert 0 == 2` at `tests/test_release.py:144` (the mutated case returned exit 0 instead of a typed failure). Isolation rerun and a subsequent full rerun passed; 6/6 isolation runs pass on the main worktree.
- Mechanism: `_run` executes the venv's `wgp` with `PYTHONPATH=<guard>:<clone>` and relies on `guard/sitecustomize.py` removing editable-install finders from `sys.meta_path` so the clone's `wangp` package shadows the editable install. `wangp/cli.py::_repository_root()` resolves `Path(__file__).resolve().parents[1]`, so if the editable finder is not stripped, `wgp` imports the real worktree's code, resolves the real repository root, verifies the unmutated repository, and legitimately exits 0 — the mutation is never seen and the probe reports a pass-shaped result.
- The shadow filter matches only `finder.__class__.__module__ == '_virtualenv'`. Any other editable finder implementation (path-based `.pth` insertion, a differently named finder class, or a finder registered after `sitecustomize` runs) leaves the editable install winning, and `sys.meta_path` finders run before path-based finding.
- This is a fail-open hole in a fail-closed gate: the suite can report "typed failure verified" while having verified the wrong source tree.

## OUT OF SCOPE
- Changing release-verification semantics in `wangp/release.py` or the `wgp release verify` exit-code contract.
- Rewriting unrelated tests or the `_clone` helper beyond what the fix needs.
- Any GPU, SSH, network, model-inference, tag, release, or publish work.

## DIFF BUDGET
- Roughly 1-2 files, under 80 authored changed LOC.

## Boundary Map
PRODUCES:
- tests/test_release.py -> every probe asserts the shadowing actually took effect (for example by asserting the resolved repository root or the imported `wangp` package path is inside the clone) and fails with a diagnostic when it did not.
CONSUMES:
- wangp/cli.py -> `_repository_root()` remains the single, inspectable resolution point.
  spec: `_repository_root(args: argparse.Namespace, next_command: str) -> Path` resolves exactly one explicit or checkout-local Wangp repository root.
- tests/test_release.py -> `_run` / `_run_verified` keep the existing network and SSH guards.
  spec: `_run(root: Path, guard_root: Path, *args: str) -> subprocess.CompletedProcess[str]`; `_run_verified(root: Path, guard_root: Path, extra: Path | None, *args: str)` additionally asserts tree immutability.

## Required Outcomes
1. A probe that resolves the wrong source tree fails with an explicit diagnostic naming the resolved root and the expected clone root, instead of asserting a wrong-shaped result.
2. The shadowing mechanism is made robust for the editable-install implementations actually present in this repository's `.venv` (not only a `_virtualenv`-named finder).
3. The failure matrix still passes on a clean checkout and still fails when the mutation is applied, and the run proves which tree was verified.
4. A regression test demonstrates the guard: for example, deliberately disabling the shadowing makes the probe fail rather than silently pass.
5. No change to release-verification behaviour, exit codes, or protected engine paths.

## Testing Requirements
- Real-process, no mocks: `uv run --frozen --extra dev pytest tests/test_release.py -q` and the full `uv run --frozen --extra dev pytest -q`.
- Reproduce the historical observation or state explicitly that the exact ordering trigger could not be reproduced, and show the new guard failing when shadowing is disabled.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must paste targeted and full-suite output, the disabled-shadowing demonstration, and the resolved-root evidence into notes.
- Developer must use `pvg story deliver`.
- No GPU, SSH, network, model inference, tag, release, or publish is authorized; the story branch and its PR are the only push target.

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

Summary: Release probes now run with a startup guard that drops every non-standard `sys.meta_path` finder and removes the venv's path-based editable project root when the expected tree is a clone. Every real-process probe writes `import-provenance.json`; the parent test asserts the imported `wangp` module and its resolved repository root equal the expected tree before accepting any CLI result. This closes both editable-hook and winning-path-injection routes and preserves the existing network/SSH guards.

The repository `.venv` inspection found `_virtualenv._Finder` plus the path-based `_editable_impl_wangp_dspy.pth` entries for the real worktree. The old guard removed only a finder whose class module was `_virtualenv`; it did not address path injection or differently named editable finders. The historical one-shot ordering was not reproducible: the pre-change targeted suite passed 6/6. The committed regression creates a real unshadowed path order (`guard:ROOT:clone`) and mutates only the clone's `VERSION`; the venv `wgp` verifies the clean real checkout and returns 0, but recorded root is ROOT. `_assert_import_provenance` then fails closed with: `release probe verified the wrong source tree: resolved_root=<real-root>; expected_root=<clone-root>; wangp_module=<real-root>/wangp/__init__.py`.

Commands run:
- Venv inspection -> `_virtualenv.pth` imports `_virtualenv._Finder`; `_editable_impl_wangp_dspy.pth` contains the real worktree path; probe `sys.meta_path` contained `_virtualenv._Finder`, BuiltinImporter, FrozenImporter, PathFinder.
- Pre-change `uv run --frozen --extra dev pytest tests/test_release.py -q` -> exit 0; 6 passed (historical ordering not reproduced).
- `uv run --frozen --extra dev pytest tests/test_release.py::test_probe_fails_closed_when_import_shadowing_is_disabled -q` -> exit 0; regression passed after commit because the wrong-tree child result is rejected by provenance assertion.
- `uv run --frozen --extra dev pytest tests/test_release.py -q --junitxml=/tmp/wd-i7nn-targeted/t.xml` -> exit 0; parsed `tests=7,failures=0,errors=0,skipped=0,time=21.685`.
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-i7nn-full/f.xml` -> exit 0; parsed `tests=1973,failures=0,errors=0,skipped=1,time=675.148`.
- `uv build --out-dir=/tmp/wd-i7nn-build` -> exit 0; one wheel and one sdist.
- `git push -u origin story/WD-i7nn` -> pushed only `story/WD-i7nn`; `gh pr create` -> PR #175.

SHA: 2346dc4654b79f492acfca0e4a7b16502e06215d

### CI/Test Results

- Exact-head check `test` for SHA `2346dc4654b79f492acfca0e4a7b16502e06215d`: completed / success (check run id `107274610462`, PR #175).
- Targeted release suite: exit 0; JUnit parsed counters tests=7, failures=0, errors=0, skipped=0.
- Full suite: exit 0; JUnit parsed counters tests=1973, failures=0, errors=0, skipped=1.
- Build: `wangp_dspy-0.1.0-py3-none-any.whl` sha256 `79362f88af9e41d119c842e5322aea968f5f837c56f16db5778e36dc31d84418`; `wangp_dspy-0.1.0.tar.gz` sha256 `8bbbedf6b44e9dfa823c83dbad8819155dab234fa7e62d46c287996517748718`; exactly one wheel and one sdist (`uv` also emitted its output-directory `.gitignore`).
- No `wangp/`, release semantics, GPU, SSH, model inference, tag, release, or publish changes; the only pushed branch was `story/WD-i7nn`.

### AC Verification

| AC | Result | Evidence |
| --- | --- | --- |
| 1. Wrong-tree probes fail with resolved and expected roots | PASS | `_assert_import_provenance` rejects missing provenance or mismatch with `resolved_root`, `expected_root`, and `wangp_module`; `_run` invokes it for every probe. |
| 2. Shadowing handles the installed editable implementations | PASS | Guard retains only the three standard importers and removes the inspected `_editable_impl_wangp_dspy.pth` project-root path for clones; `_virtualenv._Finder` and any other non-standard finder are dropped. |
| 3. Clean/mutated matrix passes and proves its tree | PASS | Targeted suite exit 0 with parsed tests=7, failures=0, errors=0, skipped=0; every release subprocess records `wangp.__file__` and derived root. |
| 4. Disabled-shadowing regression fails closed | PASS | `test_probe_fails_closed_when_import_shadowing_is_disabled` uses a real process, gets pass-shaped exit 0 from the clean real tree, then rejects mismatched provenance. |
| 5. Existing guards/behavior and protected files remain intact | PASS | Network audit hook and fake SSH guard remain; only `tests/test_release.py` changed; full suite exit 0 with 1973 tests, 0 failures/errors, 1 skipped. |

## nd_contract
status: delivered

### evidence
- Head `2346dc4654b79f492acfca0e4a7b16502e06215d` on `story/WD-i7nn`; PR #175 exact-head CI check `test` completed/success.
- Targeted JUnit: tests=7, failures=0, errors=0, skipped=0. Full JUnit: tests=1973, failures=0, errors=0, skipped=1. Build produced one wheel and one sdist.

### proof
- [x] AC #1: every probe fails closed with resolved root, expected root, and imported module diagnostics when provenance does not match.
- [x] AC #2: both inspected path-based editable injection and non-standard meta-path finders are neutralized for clone probes.
- [x] AC #3: targeted release suite passes and every probe records the tree it imported; mutated matrix remains typed and read-only.
- [x] AC #4: `test_probe_fails_closed_when_import_shadowing_is_disabled` proves an unshadowed wrong-tree exit 0 is rejected.
- [x] AC #5: network/SSH guards and release behavior remain unchanged; no protected `wangp/` or engine file changed.

## History
- 2026-09-23T16:05:37Z status: open -> in_progress
- 2026-09-23T16:05:37Z claimed by dev-WD-i7nn

## Links
## Comments
