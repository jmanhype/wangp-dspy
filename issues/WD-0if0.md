---
id: WD-0if0
title: "A tool-installed wgp resolves the repository root to site-packages and reports an internal error"
status: in_progress
priority: 1
type: bug
labels: [packaging, diagnostics]
created_at: 2026-09-22T20:40:52Z
created_by: speed
updated_at: 2026-09-22T21:44:01Z
content_hash: "sha256:f09c9aeee16855d75f8de1b79755621ece9e044b8b3762ff3128724f9ad7f0e0"
assignee: dev-WD-0if0
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


## History
- 2026-09-22T21:44:01Z status: open -> in_progress
- 2026-09-22T21:44:01Z claimed by dev-WD-0if0

## Links


## Comments
