---
id: WD-qswf
title: "Bug: LF004 launcher setup heredoc deadlock"
status: in_progress
priority: 0
type: bug
labels: [bug, test, evidence, discovered-by-pm, delivered]
parent: WD-3nod
created_at: 2026-09-27T20:09:48Z
created_by: speed
updated_at: 2026-09-27T21:04:36Z
content_hash: "sha256:12d3d741aa03053d6358b18e74a63a8c08a962f7a826352af4d2d0992020d172"
blocks: [WD-fay0]
assignee: dev-WD-qswf
follows: [WD-osfm, WD-28i5]
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
## Implementation Evidence

Summary: WD-qswf removes the reader-less LF004 setup-command Bash heredoc by moving payload construction to a directly executed Python helper, bounds the real launcher test with process-group timeout, and proves the previously hanging undeselected full suite now finishes green.

Commands run:

- `timeout 40s uv run --frozen --extra dev pytest -q tests/test_lf004_recovery_tooling.py::test_launcher_setup_is_root_relative_from_foreign_cwd` (pre-fix reproduction: local exit 124 at 15 seconds)
- `uv run --frozen --extra dev pytest -q tests/test_lf004_recovery_tooling.py` (three consecutive post-fix runs: 2 passed each)
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-qswf-fullsuite.xml`
- `pvg lint --backlog`
- `uv run --frozen --extra dev wgp release verify`
- `git diff --check`
- `git diff --name-only 7393245f59c7ff03f26493d722577e2481657299 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
- `git push -u origin story/WD-qswf`

SHA: 5e017192760c11c6382561a98ea1c701013f9cee

PR: https://github.com/jmanhype/wangp-dspy/pull/210

Root cause and fix:

- The setup launcher forked a Bash child that entered `heredoc_write` while holding both pipe ends, with `/dev/null` as stdin and no Python reader exec'd.
- Command-record construction moved to `datasets/content_briefs/lf004-operator-dogfood-56f/run/write_command_record.py`.
- `run_recovery_once.sh` invokes that helper directly with `--root` and `--output`.
- The focused integration test runs the real launcher in a new process session, redirects descendants to temporary files, and terminates the whole group after 15 seconds if progress stops.
- The test now compares deterministic setup-command records and stage plans from two foreign working directories, asserts seven staged assets and root-relative database/ledger fields, and rejects foreign-cwd leakage.

### CI/Test Results

- Focused real-process integration test: 3/3 consecutive runs passed; recorded in `focused-1.*`, `focused-2.*`, and `focused-3.*`.
- Undeselected full suite: 2,108 tests, 0 failures, 0 errors, 1 skipped, 1,168.374 seconds; `fullsuite.xml` and `fullsuite-counters.json`.
- Backlog lint: 145 scanned, 0 errors, 0 review findings.
- Clean-head release verification at `5e017192`: version/changelog/recipe/tree PASS, `release=ready`, `tag_created=false`.
- Protected-file parity from `7393245f`: 0 changed.
- `git diff --check`: PASS.
- PR #210 CI at `5e017192`: pending at delivery; exact-head result must be reviewed before merge.

### AC Verification

- [x] AC 1: the real launcher runs from `cwd-a` and `cwd-b` under a 15-second local process-group bound and both invocations pass.
- [x] AC 2: setup-command and stage-plan bytes are deterministic, seven assets are present, and root-relative DB/ledger fields plus foreign-cwd exclusion are asserted.
- [x] AC 3: command records are generated by a directly executed helper rather than a reader-less inline heredoc.
- [x] AC 4: regression timeout returns exit 124, captures output, and terminates the complete launcher process group rather than requiring a manual kill.
- [x] AC 5: undeselected full suite passed 2,108 tests with 0 failures/errors and 1 skip.
- [x] AC 6: protected engine files remain unchanged from `7393245f`.

## nd_contract
status: in_progress

### evidence
- Claimed by dev-WD-qswf; implementation underway at base 7393245f59c7ff03f26493d722577e2481657299.

### proof
- [ ] Pending launcher fix, focused repeats, undeselected full suite, release gates, branch, commit, and PR.

## MANDATORY SKILLS
- pvg
- tool-systematic-debugging

## History
- 2026-09-27T20:09:49Z dep_added: blocks WD-fay0
- 2026-09-27T20:10:33Z status: open -> in_progress
- 2026-09-27T20:10:33Z auto-follows: linked to predecessor WD-osfm
- 2026-09-27T20:10:34Z claimed by dev-WD-qswf
- 2026-09-27T21:04:36Z status: in_progress -> in_progress
- 2026-09-27T21:04:36Z auto-follows: linked to predecessor WD-28i5

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-osfm]], [[WD-28i5]]

## Comments
