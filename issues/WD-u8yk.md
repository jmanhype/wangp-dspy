---
id: WD-u8yk
title: "One-command install and the v0.1.0 release note"
status: open
priority: 1
type: feature
labels: [packaging, documentation]
created_at: 2026-09-22T20:19:06Z
created_by: speed
updated_at: 2026-09-22T20:19:06Z
content_hash: "sha256:d8824db48400dcd4a3dd27c669ec70e2d654854d612ca76625d906c2299bbb29"
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


## History


## Links


## Comments
