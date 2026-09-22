---
id: WD-u8yk
title: "One-command install and the v0.1.0 release note"
status: in_progress
priority: 1
type: feature
labels: [packaging, documentation, delivered]
created_at: 2026-09-22T20:19:06Z
created_by: speed
updated_at: 2026-09-22T20:32:56Z
content_hash: "sha256:37378de576832bd2ad1719db9cb1435caebdb6cfa9ea8ce1acd7df6389cf8b34"
assignee: dev-WD-u8yk
---

## Description
## USER INTENT
Observable outcome: a stranger who has never seen this repository can install the product with one documented command and land in a working `wgp`, and the repository carries written v0.1.0 release notes. Today the only path is clone plus `uv sync`, which is a contributor workflow, not an install.

## Context (Embedded)
- The repository is public and installable from source: `uv tool install --from <repo> wangp-dspy` produces a real `wgp` executable on PATH without cloning, and `wgp doctor` then reports readiness. No PyPI publication is authorized by this story (credentials are an operator decision), so the documented one-command path must work from the git source and be verified in a temporary tool directory.
- `README.md` currently documents install as `git clone` plus `uv sync --extra dev`; the contributor path must remain documented for development, but the first-class install path comes first.
- v0.1.0 is unreleased: `VERSION` is `0.1.0`, `CHANGELOG.md` has the `## [0.1.0]` entry, and `wgp release verify` already reports `tag-ready=v0.1.0` with `tag_created=false`. This story writes the release note; cutting the tag stays with the dispatcher/operator.
- Maestro (the reference product) installs through a one-click Pinokio launcher, so an install path with a single command and an explicit prerequisite check is the parity target.

## OUT OF SCOPE
- Publishing to PyPI, npm, Homebrew, or any registry, and any credential, token, or paid service.
- Creating a Git tag, GitHub release, or uploaded artifact: the tag is cut by the dispatcher after acceptance.
- Any Pinokio-hosted launcher repository or external account, and any GUI.
- Any change to renderer, queue, provenance, QC, gate, retry, recipe, or release-verification semantics.

## DIFF BUDGET
- Roughly 5 files, under 200 authored changed LOC.

## Boundary Map
PRODUCES:
- install.sh -> POSIX-shell installer: verifies `uv` is present (typed message plus the exact install command when it is not), installs the package from a source argument or the canonical git URL into the user's tool directory, then runs `wgp doctor`. Must support `--help`, `--dry-run`, `--source <path-or-url>`, and must never require root.
- docs/install.md -> prerequisites, one-command install, verifying the install, upgrading, uninstalling, and the contributor (clone + `uv sync`) alternative.
- docs/RELEASE_NOTES_v0.1.0.md -> written release notes for the first public version: what the product does, what the no-GPU lane guarantees, known limits, and how to verify a recipe.
- README.md -> an "Install" section whose first command is the one-command path, with the contributor path second.
- tests/test_install.py -> real-process tests: `sh -n install.sh` is clean, `install.sh --help` and `--dry-run` exit 0 and print the documented commands, and a real temporary `UV_TOOL_DIR`/`UV_TOOL_BIN_DIR` install from the working tree produces an executable `wgp` whose `wgp doctor` reports `ready=yes`.
CONSUMES:
- wangp/cli.py -> `doctor` remains the post-install readiness check and the single place that reports remediation.
- pyproject.toml -> console script and version metadata stay the install contract.

## Required Outcomes
1. `install.sh --dry-run` prints the exact commands it would run and exits 0 without changing the machine; `--help` documents every flag.
2. A real install from the working tree into temporary `UV_TOOL_DIR`/`UV_TOOL_BIN_DIR` yields an executable `wgp`; running `wgp doctor` from it reports `ready=yes` and needs no GPU, no SSH host, and no network beyond the install itself.
3. When `uv` is missing (simulated with a restricted PATH and a fake absent `uv`), the installer exits non-zero with a typed message naming the missing prerequisite and the exact command to install it, and does not attempt a partial install.
4. README's install section leads with the one-command path and keeps the contributor path documented; the README quickstart test still passes unchanged.
5. `docs/RELEASE_NOTES_v0.1.0.md` describes the real product surface and limits honestly, including that renders require an authorized host and that the recipe proves logical identity, not byte-identical pixels.
6. No tag, release, publication, or credential is created; `wgp release verify` still reports `release=ready` with `tag_created=false`.

## Testing Requirements
- E2e/real-process only: `uv run --frozen --extra dev pytest tests/test_install.py -q`, plus the full `uv run --frozen --extra dev pytest -q`.
- The install test must perform a real `uv tool install` into temporary directories and execute the resulting binary; no mocks.
- `sh -n install.sh` (syntax) and `install.sh --help` / `--dry-run` are part of the evidence.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must paste the install transcript, the installed `wgp doctor` output, targeted and full-suite results, and the exact-head CI conclusion into notes.
- Developer must include an AC verification table.
- Developer must use `pvg story deliver`.
- No GPU, SSH, model inference, PyPI publication, tag, or push to main is authorized; the story branch and its PR are the only push target.

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence
Summary: Added a POSIX one-command uv tool installer, boundary-honest install/release documentation, README install ordering, and real-process installer tests. Local targeted/full tests, real temporary install, build, release verification, PR #159, and exact-head CI all passed; the full suite retained one pre-existing skip and one pre-existing StarletteDeprecationWarning.
Commands run:
- `uv run --frozen --extra dev pytest tests/test_install.py -q` -> exit 0; 3 passed, 0 failed, 0 skipped.
- `uv run --frozen --extra dev pytest -q` -> exit 0; 1662 passed, 0 failed, 1 pre-existing skipped; one existing StarletteDeprecationWarning.
- `sh -n install.sh` -> exit 0.
- `./install.sh --help` -> exit 0; documented `--dry-run`, `--source <path-or-url>`, default source, one-command path, and commands run.
- `UV_TOOL_DIR=<tmp>/tools UV_TOOL_BIN_DIR=<tmp>/bin ./install.sh --dry-run --source <worktree>` -> exit 0; printed `uv tool install --upgrade --from <worktree> wangp-dspy` and `<tmp>/bin/wgp doctor`; made no changes.
- Real install from committed working tree with temporary `UV_TOOL_DIR`/`UV_TOOL_BIN_DIR`, from a non-repository cwd: `sh install.sh --source <worktree>` -> exit 0; transcript included `+ wangp-dspy==0.1.0 (from file://<worktree>)`, `Installed 1 executable: wgp`, then all local doctor checks and `ready=yes`.
- Installed executable from non-repository cwd: `<tmp>/bin/wgp doctor` -> exit 0; `ready=yes`.
- Installed repository-boundary probe from non-repository cwd: `<tmp>/bin/wgp release verify` -> exit 2 with typed `INPUT_INVALID` diagnostic: `version: cannot read release version sources: [Errno 2] No such file or directory: '<UV_TOOL_DIR>/wangp-dspy/lib/python3.14/site-packages/VERSION'`; no traceback and no `release=ready` claim.
- `uv build --out-dir <tmp>` -> exit 0; exactly one wheel and one sdist. SHA-256 wheel `674ea666fa01ad8e33d639b071ce59026e83f3749133da8fcdf962f357a9295f`; sdist `f2208fa6321b5289a3a05c561a5ce8c331d63ba5069957e70725e2cd38fbf2ad`.
- `uv run --frozen --extra dev wgp release verify` -> exit 0; `version=0.1.0`, all four checks pass, `tag-ready=v0.1.0`, `tag_created=false`, `release=ready`.
- `git push origin story/WD-u8yk`; `gh pr create ...` -> PR #159.
- `gh api repos/jmanhype/wangp-dspy/commits/60aaab0a9c98704fe972f298b356f9ac44a446e2/check-runs` -> 1/1 completed; `test` conclusion `success`.
- `pvg verify install.sh docs/install.md docs/RELEASE_NOTES_v0.1.0.md README.md tests/test_install.py --include-tests --format=text` -> `VERIFY: PASSED (1 files scanned, 0 issues)`.
SHA: 60aaab0a9c98704fe972f298b356f9ac44a446e2

### CI/Test Results
- PR: https://github.com/jmanhype/wangp-dspy/pull/159
- Exact-head check run: `test` = completed/success.
- Targeted: exit 0, 3 passed / 0 failed / 0 skipped.
- Full suite: exit 0, 1662 passed / 0 failed / 1 pre-existing skipped.
- Real install and external-cwd doctor: exit 0, ending `ready=yes`.
- Build: exit 0, exactly 1 wheel and 1 sdist.
- Release preflight: exit 0, `release=ready`, `tag_created=false`.

### AC Verification
| AC | Result | Evidence |
| --- | --- | --- |
| 1 | PASS | `install.sh --dry-run` exited 0, printed both exact commands, and left temporary tool dirs unchanged; `--help` documented both flags and the default/one-command source. `tests/test_install.py::test_help_and_dry_run_print_commands` passed. |
| 2 | PASS | A real temporary `uv tool install` produced executable `<tmp>/bin/wgp`; installer and explicit installed `wgp doctor`, both run from a non-repository cwd, exited 0 and ended `ready=yes`. `tests/test_install.py::test_real_install_doctor_and_checkout_boundary` passed. |
| 3 | PASS | With a restricted PATH containing no `uv`, the installer exited 127 with `MISSING_PREREQUISITE: uv is required`, the exact uv install command, and empty temporary tool dirs. `tests/test_install.py::test_missing_uv_fails_closed` passed. |
| 4 | PASS | README Install now leads with the raw `install.sh | sh` path and places clone/`uv sync --extra dev` second; `tests/test_readme_quickstart.py` was included in the full-suite pass. |
| 5 | PASS | `docs/RELEASE_NOTES_v0.1.0.md` describes the governed product, no-GPU lane, authorized render-host limit, checkout evidence limit, logical-recipe (not byte-pixel) guarantee, and exact recipe verification commands. |
| 6 | PASS | No tag, GitHub release, registry publication, or credential was created. Checkout `wgp release verify` exited 0 with `release=ready` and `tag_created=false`. |

## nd_contract
status: delivered

### evidence
- Branch `story/WD-u8yk`; PR #159; SHA 60aaab0a9c98704fe972f298b356f9ac44a446e2.
- Targeted/full pytest, real install/doctor, shell checks, build, release verify, pvg verify, and exact-head CI outputs recorded above.

### proof
- [x] AC 1: Dry-run and help expose the exact install behavior without machine changes.
- [x] AC 2: Real temporary tool install yields an executable wgp whose external-cwd doctor ends ready=yes.
- [x] AC 3: Missing uv fails closed with the typed prerequisite message and exact install command.
- [x] AC 4: README installs first and keeps the contributor path second while quickstart tests pass.
- [x] AC 5: Release notes describe the real product, guarantees, checkout/host limits, and recipe verification honestly.
- [x] AC 6: Release readiness remains ready with no tag created and no publication occurs.

## History
- 2026-09-22T20:19:17Z status: open -> in_progress
- 2026-09-22T20:19:18Z claimed by dev-WD-u8yk
- 2026-09-22T20:32:56Z status: in_progress -> in_progress

## Links


## Comments
