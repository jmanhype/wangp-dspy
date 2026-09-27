---
id: WD-qswf
title: "Bug: LF004 launcher setup heredoc deadlock"
status: in_progress
priority: 0
type: bug
labels: [bug, test, evidence, discovered-by-pm, rejected]
parent: WD-3nod
created_at: 2026-09-27T20:09:48Z
created_by: speed
updated_at: 2026-09-27T21:35:19Z
content_hash: "sha256:4117250c046dd06aefb85d660d70c375de23751505cf8e109bf2a28ee80d2c5e"
blocks: [WD-fay0]
follows: [WD-osfm, WD-28i5, WD-ycjg, WD-8h6p]
assignee: dev-WD-qswf
---

## Description

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


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-27.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


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
status: delivered

### evidence
- Final delivered head 5e017192760c11c6382561a98ea1c701013f9cee on story/WD-qswf; PR https://github.com/jmanhype/wangp-dspy/pull/210.
- Root-cause/focused-repeat/full-suite/lint/release/protected evidence is recorded above and under datasets/runs/maestro-parity/WD-qswf/.

### proof
- [x] All six WD-qswf acceptance criteria are delivered for independent PM review.

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


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-27.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


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
status: delivered

### evidence
- Final delivered head 5e017192760c11c6382561a98ea1c701013f9cee on story/WD-qswf; PR https://github.com/jmanhype/wangp-dspy/pull/210.
- Root-cause/focused-repeat/full-suite/lint/release/protected evidence is recorded above and under datasets/runs/maestro-parity/WD-qswf/.

### proof
- [x] All six WD-qswf acceptance criteria are delivered for independent PM review.

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

Summary: Rework adds the missing delivery proof only: measured focused coverage, required learnings, exact-head CI result, and explicit ownership of the two pre-existing CI warning classes. The implementation head remains `5e017192760c11c6382561a98ea1c701013f9cee`.

Commands run:

- `uv run --frozen --extra dev --with coverage coverage run -m pytest -q tests/test_lf004_recovery_tooling.py`
- `uv run --frozen --extra dev --with coverage coverage report -m`
- `uv run --frozen --extra dev --with coverage coverage report --include='tests/test_lf004_recovery_tooling.py,datasets/content_briefs/lf004-operator-dogfood-56f/run/write_command_record.py' -m`
- Exact-head CI: GitHub Actions run `36350323341`, job `108707648658`, `test` completed successfully in 22m9s.

SHA: 5e017192760c11c6382561a98ea1c701013f9cee

PR: https://github.com/jmanhype/wangp-dspy/pull/210

### CI/Test Results

- Focused real-process integration test: 3/3 consecutive prior runs passed.
- Undeselected full suite at the same code head: 2,108 tests, 0 failures, 0 errors, 1 skipped, 1,168.374 seconds.
- Exact-head PR CI at `5e017192`: SUCCESS in 22m9s.
- Measured coverage command scope: focused launcher test module.
- Coverage result: `tests/test_lf004_recovery_tooling.py` 303 statements, 12 missed, **96%**; overall files imported by that focused run: 3,408 statements, 2,027 missed, **41%**.
- Coverage boundary: the helper is intentionally exercised as a real subprocess by the integration test and therefore is not included in the parent pytest process's Python line-coverage report; its behavior is asserted through deterministic stdout, exit status, setup-command record, and stage-plan files.

### AC Verification

- [x] AC 1: two real foreign-cwd launcher runs pass under a bounded process-group timeout.
- [x] AC 2: deterministic root-relative command record and seven-asset stage plan are asserted.
- [x] AC 3: command-record generation uses a directly executed helper, not a reader-less heredoc.
- [x] AC 4: timeout terminates the process group and returns diagnostic exit 124.
- [x] AC 5: undeselected full suite and exact-head CI passed with zero failures/errors.
- [x] AC 6: protected engine files are unchanged.

LEARNINGS:

- A Bash here-document inside a captured launcher can fork a child that holds both pipe ends before exec'ing the intended reader; direct execution of a small helper removes that reader-less state.
- Integration tests that spawn Bash must own an entire process group, redirect descendant output away from pytest's pipes, and enforce a short timeout so a regression fails instead of stalling the suite.
- A successful CI run is not warning-clean proof; every dependency and action warning must be explicitly owned or routed even when the test and build conclusions are success.

DISCOVERED_BUG:
  title: CI pytest emits StarletteDeprecationWarning
  context: Exact-head CI run 36350323341 succeeded, but pytest reports a StarletteDeprecationWarning when importing FastAPI TestClient via fastapi/testclient.py and recommends httpx2.
  affected_files: dependency environment evidenced by CI log; exact importing tests not isolated during WD-qswf review
  discovered_during: WD-qswf

DISCOVERED_BUG:
  title: CI workflow emits action and runner deprecation warnings
  context: Exact-head CI reports Node.js 20 deprecation for actions/setup-python@v5 and astral-sh/setup-uv@v6, plus an ubuntu-latest migration notice.
  affected_files: .github/workflows/ci.yml
  discovered_during: WD-qswf

## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-09-27.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-27.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


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
- 2026-09-27T21:31:29Z status: in_progress -> open
- 2026-09-27T21:31:29Z released by speed
- 2026-09-27T21:35:18Z status: open -> in_progress
- 2026-09-27T21:35:18Z auto-follows: linked to predecessor WD-ycjg
- 2026-09-27T21:35:18Z claimed by dev-WD-qswf
- 2026-09-27T21:35:19Z status: in_progress -> in_progress
- 2026-09-27T21:35:19Z auto-follows: linked to predecessor WD-8h6p

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-osfm]], [[WD-28i5]], [[WD-ycjg]], [[WD-8h6p]]

## Comments

### 2026-09-27T21:06:46Z speed
## nd_contract
status: delivered

### evidence
- Final delivered head `5e017192760c11c6382561a98ea1c701013f9cee` on `story/WD-qswf`.
- PR: https://github.com/jmanhype/wangp-dspy/pull/210
- Delivery proof and gate outputs are recorded in the story notes and `datasets/runs/maestro-parity/WD-qswf/`.

### proof
- [x] AC 1: two real foreign-cwd launcher runs pass under a bounded process-group timeout.
- [x] AC 2: deterministic root-relative command record and seven-asset stage plan are asserted.
- [x] AC 3: command-record generation uses a directly executed helper, not a reader-less heredoc.
- [x] AC 4: timeout terminates the process group and returns diagnostic exit 124.
- [x] AC 5: undeselected full suite passed 2,108 tests with 0 failures/errors and 1 skip.
- [x] AC 6: protected engine files are unchanged.

### 2026-09-27T21:31:32Z speed
## PM Decision
REJECTED [2026-09-27]:
EXPECTED: A delivered story must carry the canonical proof fields: exact commands, full pass/fail counts, commit SHA, coverage percentage, and AC verification, plus a LEARNINGS section. Test/build output must own every warning through resolution or an explicit OBSERVATIONS/DISCOVERED_BUG block; exact-head CI must be terminal.
DELIVERED: Technical review supports the launcher fix: final worktree is clean at 5e017192760c11c6382561a98ea1c701013f9cee; evidence hashes verify; focused runs are 3x2 passed; committed JUnit reports 2108 tests, 0 failures, 0 errors, 1 skipped with the launcher test passing; protected files are unchanged; and PR #210 CI succeeded at the exact head in 22m9s. However, the story has no coverage percentage, no LEARNINGS section, and exact-head CI logs contain a StarletteDeprecationWarning plus Node.js 20 action-deprecation warnings with no corresponding OBSERVATIONS/DISCOVERED_BUG delivery block.
GAP: The implementation appears behaviorally correct, but the delivery proof is incomplete and does not satisfy the mandatory zero-warning ownership rule. A green exit status alone cannot be accepted.
FIX: Re-deliver with (1) a measured coverage percentage and exact command, (2) a LEARNINGS section, and (3) every exact-head CI/test warning either resolved or explicitly acknowledged in OBSERVATIONS/DISCOVERED_BUG blocks. Keep the current exact-head terminal CI result unless the code/head changes.

## nd_contract
status: rejected

### evidence
- Missing canonical proof fields: coverage percentage and LEARNINGS.
- Exact-head CI run 36350323341 succeeded but emitted unowned warnings.
- Launcher behavior evidence itself was independently verified and is not the rejection cause.

### proof
- [ ] Delivery proof completeness: coverage percentage and LEARNINGS are absent.
- [ ] Zero-warning ownership: exact-head CI warnings are not acknowledged or reported.

