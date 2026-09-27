---
id: WD-qswf
title: "Bug: LF004 launcher setup heredoc deadlock"
status: open
priority: 0
type: bug
labels: [bug, test, evidence, discovered-by-pm]
parent: WD-3nod
created_at: 2026-09-27T20:09:48Z
created_by: speed
updated_at: 2026-09-27T20:09:49Z
content_hash: "sha256:61b8e6efa256e70fcd32f9464cf17db4182604987ff94946445a21706fe39ebb"
blocks: [WD-fay0]
---

## Description
## Context (Embedded)

## USER INTENT
The Maestro-parity standing gate requires the repository's normal full `pytest -q` command to finish with zero failures. A hidden launcher hang is worse than a red test: it consumes the timeout, forces deselection, and makes "full suite green" ambiguous.

## Observed defect
During WD-osfm's first full-suite run at story base `0f91e83c`, `tests/test_lf004_recovery_tooling.py::test_launcher_setup_is_root_relative_from_foreign_cwd` stopped progressing at 48% for more than ten minutes. The JUnit boundary eventually recorded 2,108 tests, 3 failures, 0 errors, and 1 skip. Two release-test failures were the expected dirty-tree observations before commit; the launcher test was the real hang.

Direct process evidence:

- Parent PID `70269`: Bash launcher blocked in `wait4`.
- Child PID `70419`: the same `run_recovery_once.sh`, blocked in Bash `heredoc_write` with zero CPU and no reader child.
- The stalled source area is the inline `"$PYTHON" - <<'PY'` block used to write the setup/execution command record.
- Terminating only those two stale launcher PIDs allowed the rest of the suite to complete. The clean committed-head run with this one test deselected passed 2,107 tests with 0 failures, 0 errors, and 1 skip.

This is a launcher/test-harness bug, not a WD-osfm capability result and not GPU or host infeasibility.

## OUT OF SCOPE
- No change to render policy, queue admission, LF004 media, accepted provenance hashes, or the approved 56-frame plan; those are production evidence and must remain immutable.
- No broad pytest timeout wrapper or permanent test deselection; that would hide the defect rather than fix it.
- No WD-osfm evidence rewrite; the already accepted boundary document remains historical evidence.

## DIFF BUDGET
- About 3 files and under 200 changed LOC: the LF004 launcher/setup helper, its regression test, and narrowly scoped test evidence if needed.

## Boundary Map
PRODUCES:
- datasets/content_briefs/lf004-operator-dogfood-56f/run/ -> a setup-only launcher path that writes the same command record without an unbuffered inline heredoc deadlock
  spec: two foreign-cwd setup-only invocations finish within the test timeout and produce byte-identical root-relative stage plans.
- tests/test_lf004_recovery_tooling.py -> bounded regression coverage for both launcher invocations
  event: fail within a short local timeout if the launcher stops consuming input or stops producing its setup record; do not hang the full suite.

CONSUMES:
- (existing): datasets/content_briefs/lf004-operator-dogfood-56f/run/run_recovery_once.sh -> setup-only path with `RECOVERY_PYTHON` and `WANGP_RECOVERY_SETUP_ONLY=1`
  Pattern: the test must invoke the real launcher from two different foreign working directories, not a mock.
- (existing): datasets/content_briefs/lf004-operator-dogfood-56f/run/verify.py -> `main(argv: list[str] | None) -> int` and `replay_and_verify(count: int = 2) -> list[str]`
  Pattern: preserve the approved input/canonical-plan verification semantics unless the setup-only launcher explicitly and testably avoids rerunning the expensive replay in setup mode.

## Story Acceptance Criteria
1. [State] The real launcher setup-only integration test invokes the launcher from two distinct foreign working directories and completes both invocations under a bounded local timeout without hanging the process suite.
2. [State] The setup command record and stage plan are root-relative, deterministic across the two invocations, and contain the expected seven staged assets.
3. [State] The launcher's command-record generation has no reader-less inline Bash heredoc deadlock; any pipe/heredoc or replacement helper is demonstrably consumed and exits on success or failure.
4. [Unwanted] A launcher failure produces a nonzero, diagnostic result inside the local timeout; it does not leave a child shell blocked in `heredoc_write`, does not require an operator kill, and does not cause the full suite to stall.
5. [State] The undeselected command `uv run --frozen --extra dev pytest -q --junitxml=<evidence>.xml` finishes with parsed JUnit `errors=0` and `failures=0`; the previously deselected launcher test is included and passes.
6. [Unwanted] `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py` remain unchanged from merged base `7393245f59c7ff03f26493d722577e2481657299`.

## Testing Requirements
- Integration tests are MANDATORY with no mocks: run the actual launcher/script and verify filesystem effects.
- Add or retain a bounded timeout around the real launcher invocation so a regression fails rather than hangs.
- Run the focused launcher test repeatedly (at least three consecutive times) and record pass counts.
- Run the undeselected full suite at a clean committed head and record parsed JUnit counters.
- Run `pvg lint --backlog`, `uv run --frozen --extra dev wgp release verify` (`release=ready`, `tag_created=false`), protected-file parity against `7393245f59c7ff03f26493d722577e2481657299`, and `git diff --check`.

## Delivery Requirements
- Record the exact root-cause analysis and the chosen deadlock fix.
- Paste focused repeat-test output, full-suite JUnit counters, lint/release/protected/diff results, commit SHA, branch, and PR.
- Provide the standard Implementation Evidence, Commands run, CI/Test Results, Summary, SHA, and AC Verification sections.

## Skills To Use
- pvg
- tool-systematic-debugging

## nd_contract
status: new

### evidence
- Discovered during WD-osfm full-suite verification at merged base `7393245f59c7ff03f26493d722577e2481657299`; process stacks and the 2,107-test deselected clean-run boundary are recorded in `datasets/runs/maestro-parity/WD-osfm/fullsuite-launcher-boundary.md`.

### proof
- [ ] Pending bounded root-cause reproduction, launcher fix, and undeselected full-suite pass.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-27T20:09:49Z dep_added: blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]

## Comments
