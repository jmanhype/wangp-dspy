---
id: WD-0if0
title: "A tool-installed wgp resolves the repository root to site-packages and reports an internal error"
status: closed
priority: 1
type: bug
labels: [packaging, diagnostics, accepted]
created_at: 2026-09-22T20:40:52Z
created_by: speed
updated_at: 2026-09-22T22:57:50Z
content_hash: "sha256:25c4507cefb96578dc31e1da32d708be4301a84a0a4bf7e624b3c58d99e02f22"
assignee: dev-WD-0if0
closed_at: 2026-09-22T22:32:36Z
close_reason: "Accepted: real installed-boundary, override, parity, front-door, full-suite, exact-head CI, and tag checks all pass."
---

## Description
## USER INTENT
Observable outcome: a user who installed `wgp` with one command (no checkout) gets a typed, actionable message for every verb that needs repository evidence, naming the exact fix, instead of an "unexpected internal error" pointing at a site-packages directory. Verbs that genuinely need no repository keep working.

## Context (Embedded)
- Reproduced on this machine after a real tool install (`UV_TOOL_DIR=<tmp> UV_TOOL_BIN_DIR=<tmp> uv tool install --from . wangp-dspy`), executed from `/tmp` with absolute brief and plate paths:
  `wgp plan --brief <repo>/datasets/content_briefs/lf004-operator-dogfood-56f/brief.json --plates <repo>/datasets/content_briefs/lf004-operator-dogfood/plates --out <tmp>/plan.json`
  prints `wgp: error: unexpected internal error: RepositoryIdentityError: git rev-parse --show-toplevel failed for /private/tmp/.../lib/python3.14/site-packages: fatal: not a git repository` and produces no plan.
- Cause: `wangp/cli.py::_repository_root()` returns `Path(__file__).resolve().parents[1]`, which for an installed package is the site-packages directory. Every repository-scoped verb then reads `VERSION`/`datasets`/`CHANGELOG.md` from site-packages, and provenance fails closed against a non-repository.
- WD-u8yk documents the current boundary honestly (which verbs need a checkout) but the failure shape is still an internal error reported to the user, which contradicts the epic's "typed, actionable diagnostics rather than tracebacks" outcome and weakens the one-command install promise.
- `wgp doctor` already succeeds outside a checkout and `wgp content` (WD-cpb8) is the intended no-checkout front door.

## OUT OF SCOPE
- Weakening repository-identity fail-closed provenance: a run outside any repository must still refuse to claim repository provenance.
- Changing renderer, queue, gate, retry, recipe, or release-verification semantics.
- Publishing to a registry, tagging, or any credential use.

## DIFF BUDGET
- Roughly 3 files, under 150 authored changed LOC.

## Boundary Map
PRODUCES:
- wangp/cli.py -> repository-root resolution that distinguishes a checkout from an installed package, supports an explicit override (for example `--repository-root` on the affected verbs and/or a documented `WANGP_REPOSITORY_ROOT` environment variable), and fails with a typed input/configuration diagnostic (exit 2) that names the missing prerequisite and the exact next command.
- tests/test_repository_root_resolution.py -> real-process tests for the installed-package case, the explicit-override case, and the in-checkout case.
CONSUMES:
- wangp/diagnostics.py -> typed, redacted diagnostics carrying remediation plus next command.
- wangp/config.py -> host/configuration resolution must not gain hidden defaults.

## Required Outcomes
1. Running a repository-scoped verb from an installed package outside a checkout exits 2 with a typed diagnostic that names the real fix (run inside a Git checkout, or point at one explicitly) and never the string "unexpected internal error".
2. An explicit repository root (flag and/or documented environment variable) makes the repository-scoped verbs work against a real checkout from any working directory, with unchanged provenance recorded for that checkout.
3. Inside a checkout, behaviour is byte-identical to today: same plan output, same provenance, same exit codes.
4. `wgp doctor`, `wgp brief validate`, and the no-GPU front door continue to work outside a checkout.
5. Repository-identity fail-closed behaviour is preserved: no repository, no provenance claim.

## Testing Requirements
- Real-process, no mocks: `uv run --frozen --extra dev pytest tests/test_repository_root_resolution.py -q` plus the full `uv run --frozen --extra dev pytest -q`.
- The installed-package case must be exercised for real, for example by installing into temporary `UV_TOOL_DIR`/`UV_TOOL_BIN_DIR` and running the resulting binary from a non-repository directory.
- Assert the exact new exit code and diagnostic vocabulary, and assert no traceback is printed.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must paste the before and after command transcripts for all three cases, targeted and full-suite output, and the exact-head CI conclusion into notes.
- Developer must use `pvg story deliver`.
- No GPU, SSH, network, model inference, tag, release, or publish is authorized; the story branch and its PR are the only push target.

## Acceptance Criteria


## Design


## Notes
## Rework Verification
Verdict: HOLDS
SHA: d45ce9306c53476ec0db58095b5a7f54fa442957
Commands:
- uv build; uv tool install --offline from the built wheel
- real-wheel doctor/content/plan/recipe write/recipe verify/release verify flag matrix
- no-checkout content with embedded-newline dialogue
- content --submit against separate checkout with partial wangp.toml
- release verify with subdirectory --repository-root
- installed boundary, exact-root override, and in-checkout parity
- uv run --frozen --extra dev pytest tests/test_repository_root_resolution.py tests/test_install.py -q
- uv run --frozen --extra dev pytest -q
- gh api commit check-runs; gh pr checks 162; git rev-parse v0.1.0^{commit}
Observed:
- wheel install exit 0; all six advertising verbs accepted --repository-root, exit 0, no "unrecognized arguments"; parser inventory is exactly content, doctor, plan, recipe write, recipe verify, release verify.
- newline dialogue exit 2 INPUT_INVALID; no plan, run directory, script, or ledger.
- selected-checkout submit exit 3 with missing host.target, host.wgp_python; zero site-packages references.
- subdirectory release override exit 0 with release=ready.
- installed boundary exit 2 typed/no internal error; override and checkout both exit 0 with four clips, 9.332s, no GPU/no queue, identical SHA cc645889bd0bfb2cf7c3c71a25a3b85644c230e4f205e80b5f0766c5ab9ea884 (cmp 0).
- targeted 10 passed; full 1682 passed, 1 skipped; both exit 0.
- exact-head CI test completed/success; PR test pass; v0.1.0 targets 3916fe4cb1d2272a0602a871b4157394afc5ebfa.

## Rework Evidence
- Finding 2 fixed: audited all guidance callers and registered `--repository-root` on `doctor --capabilities` and `content` (plan/recipe/release already had it); a real-wheel test passes the flag to all six advertising surfaces and all exit 0.
- Finding 3 fixed: the no-provenance content path applies line-safety validation before `build_run_film_inputs`; the control-character regression exits 2 and leaves no plan, script, ledger, or run directory.
- Finding 4 fixed: `content --submit` diagnostics reload host configuration from the validated selected root; the selected checkout with `host.wgp_root` reports only `host.target, host.wgp_python`.
- Finding 5 fixed: explicit overrides return Git's canonical Wangp top level; a `--repository-root <checkout>/wangp` release verification now succeeds instead of reading release inputs from the subdirectory.
- Verification at head `d45ce9306c53476ec0db58095b5a7f54fa442957`: targeted repository/install suite 8 passed, exit 0; full suite 1,683 collected, 0 failures/errors, 1 pre-existing skip, exit 0; build produced one wheel and one sdist, exit 0; GitHub `test` completed/success. Fresh transcripts: `/tmp/wd0if0-rework-evidence/transcript.txt`.


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-22.

### proof
- [x] Story closed after accepted label was applied.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-22.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence
Summary: Installed repository-scoped verbs now fail closed with typed exit-2 diagnostics, explicit checkout overrides bind provenance to that checkout, and checkout-free front doors remain available without a provenance claim.

Commands run:
- `pvg nd show WD-0if0`
- `uv run --frozen --extra dev pytest tests/test_repository_root_resolution.py -q` — 2 passed, exit 0.
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd0if0-full-final.xml` — 1,679 tests, 0 errors, 0 failures, 1 skipped, exit 0.
- `uv build --out-dir /tmp/wd0if0-dist-65959fa` — exit 0; exactly one wheel and one sdist.
- `pvg verify wangp/cli.py docs/install.md tests/test_install.py tests/test_repository_root_resolution.py --include-tests --format=text` — VERIFY: PASSED.
- `git push origin story/WD-0if0`; `gh pr create` produced PR #162.
- `gh api repos/jmanhype/wangp-dspy/commits/65959faf64da9a7c59dda0324aaba88d6cc276f5/check-runs` — `test` completed, conclusion `success`.

Before transcripts (base `3916fe4cb1d2272a0602a871b4157394afc5ebfa`, evidence `/tmp/wd0if0-before.kYXvzx/transcript.txt`):
- Installed outside checkout: `wgp plan ...` exit 4; stderr `wgp: error: unexpected internal error: RepositoryIdentityError: git rev-parse --show-toplevel failed for .../site-packages: fatal: not a git repository`; no plan.
- Installed with `WANGP_REPOSITORY_ROOT=<checkout>`: previously ignored, same exit 4/internal RepositoryIdentityError; no plan.
- Normal checkout: exit 0; `brief=sha256:67202d... clips=4`, `summary clips=4 duration_s=9.332 gpu_work=false queue_submitted=false`, ledger written.

After transcripts (head below, evidence `/tmp/wd0if0-after-65959fa/transcript.txt`):
- Installed wheel outside checkout: exit 2; typed `diagnostic code=INPUT_INVALID ... A Wangp Git checkout is required`; redacted observed state; remediation names running in a checkout or `--repository-root`/`WANGP_REPOSITORY_ROOT`; no traceback, no `unexpected internal error`, no plan.
- Installed wheel from outside with `WANGP_REPOSITORY_ROOT=<checkout>`: exit 0; `clips=4`, `duration_s=9.332`, `gpu_work=false`, `queue_submitted=false`, ledger written for the named checkout.
- Normal checkout: exit 0 with the same plan shape and summary. Override copy and checkout plan compared byte-equal (`cmp` exit 0), SHA-256 `6b8eddfa64c3edfba33e8b2ea19cb7d5ae451424823532c1a8d82e7ad93ae0a5`.
- Front doors outside checkout: `doctor` exit 0 ending `ready=yes`; `brief validate` exit 0; plain `content` exit 0 with no repository claim/plan.

Legacy test contract update:
- Old exact assertions: `assert plan.returncode == 4, plan_output`; `assert "unexpected internal error: RepositoryIdentityError" in plan_output`; `assert "not a git repository" in plan_output`.
- New exact assertions: `assert plan.returncode == 2, plan_output`; `assert "diagnostic code=INPUT_INVALID" in plan_output`; `assert "Run inside a Wangp Git checkout" in plan_output`; `assert "WANGP_REPOSITORY_ROOT=<repository>" in plan_output`; `assert "unexpected internal error" not in plan_output`.
- The adjacent installed `release verify` expectation was also updated from the obsolete missing-version phrase to the same typed checkout requirement, preserving exit-2 and no-ready-claim coverage.

SHA: 65959faf64da9a7c59dda0324aaba88d6cc276f5

### CI/Test Results
- PR: https://github.com/jmanhype/wangp-dspy/pull/162
- GitHub check `test`: completed / success at SHA `65959faf64da9a7c59dda0324aaba88d6cc276f5` (https://github.com/jmanhype/wangp-dspy/actions/runs/35791811528/job/106961830469).
- Targeted: 2 passed, 0 failed, exit 0.
- Full committed tree: 1,679 tests, 0 errors, 0 failures, 1 skipped, exit 0. One pre-existing Starlette/httpx deprecation warning was unchanged.
- Build: one `wangp_dspy-0.1.0-py3-none-any.whl` and one `wangp_dspy-0.1.0.tar.gz`, exit 0.

### AC Verification
| AC | Result | Evidence |
| 1 | PASS | Installed-wheel plan outside a checkout exits 2 with redacted `INPUT_INVALID`, remediation, and next command; no internal error/traceback (`tests/test_repository_root_resolution.py`, after transcript). |
| 2 | PASS | `WANGP_REPOSITORY_ROOT` and `--repository-root` target a real checkout; installed override records checkout provenance and is byte-identical to in-checkout plan SHA `6b8eddfa...`; flag/env paths tested. |
| 3 | PASS | Normal checkout remains exit 0 with same summary/ledger; override and checkout plan bytes compare equal; full suite passes. |
| 4 | PASS | Outside checkout: doctor exits 0 `ready=yes`, brief validate exits 0, plain content exits 0 with no repository claim. |
| 5 | PASS | Outside repository plan writes no plan/provenance; plain content emits no repository field; release/plan require a Wangp checkout. No new config default was added. |

## nd_contract
status: delivered

### evidence
- Final branch `story/WD-0if0`, PR #162, SHA `65959faf64da9a7c59dda0324aaba88d6cc276f5`.
- Targeted 2/2 passed; full suite 1,679 tests, 0 failures/errors, 1 skipped; build produced one wheel and one sdist; CI `test` success.
- Before/after transcripts recorded above; plan parity SHA `6b8eddfa64c3edfba33e8b2ea19cb7d5ae451424823532c1a8d82e7ad93ae0a5`.

### proof
- [x] AC #1: installed repository-scoped failure is typed exit 2 with actionable checkout remediation and no internal-error string.
- [x] AC #2: explicit environment/flag override targets a real checkout and preserves its provenance.
- [x] AC #3: in-checkout output, provenance, and exit codes remain unchanged; byte comparison passed.
- [x] AC #4: doctor, brief validate, and plain content keep working outside a checkout.
- [x] AC #5: repository identity remains fail closed and no hidden repository/config default was introduced.


## History
- 2026-09-22T21:44:01Z status: open -> in_progress
- 2026-09-22T21:44:01Z claimed by dev-WD-0if0
- 2026-09-22T22:24:32Z status: in_progress -> in_progress
- 2026-09-22T22:32:36Z status: in_progress -> closed

## Links


## Comments
