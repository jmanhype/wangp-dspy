---
id: WD-i7nn
title: "Release probes can silently verify the real checkout instead of the mutated clone"
status: in_progress
priority: 2
type: bug
labels: [testing, release]
created_at: 2026-09-22T18:57:15Z
created_by: speed
updated_at: 2026-09-23T16:05:37Z
content_hash: "sha256:51c0b290d02978c548bc51562b0049f60de9cf07cbc3dd9380912a10740798b2"
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


## History
- 2026-09-23T16:05:37Z status: open -> in_progress
- 2026-09-23T16:05:37Z claimed by dev-WD-i7nn

## Links
## Comments
