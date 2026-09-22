# Contributing to Wangp

Wangp accepts changes that preserve its no-GPU planning boundary, fail-closed gates, and verifiable provenance. Contributions do not need a render host unless the story explicitly authorizes one.

## Setup

```bash
uv sync --extra dev
```

Python 3.11+, `uv`, `ffmpeg`, and `ffprobe` are required. GPU-model work is optional and must never be triggered by the default test suite.

## Verify

For a documentation-only change:

```bash
uv run --frozen --extra dev pytest tests/test_readme_quickstart.py -q
```

Before requesting review, run the full suite and Git whitespace check:

```bash
uv run --frozen --extra dev pytest -q
git diff --check
```

The targeted README test creates a clean temporary Git worktree and executes the documented quickstart without mocks. If you change a quickstart command, update both README and that test in the same change; untested prose must not claim to be a quickstart.

## Provenance and clean trees

Runs intentionally fail closed when Git reports opaque untracked directories, including embedded worktrees. Work from a clean checkout or resolve untracked content explicitly. Never bypass `repository_identity()`, delete evidence to make a run “clean,” edit hashes to match a desired result, or fabricate gate scores.

Keep generated outputs outside the checkout unless a story explicitly asks you to commit evidence. If evidence is in scope, include artifact paths and content-derived hashes so reviewers can verify without a GPU.

## Code and evidence expectations

- Preserve typed exceptions at validation and gate boundaries; do not replace them with silent fallbacks.
- Keep planning deterministic and model-free unless a story explicitly wires an LM.
- Keep host execution behind the existing `host/` seams; tests must not SSH or render implicitly.
- Maintain public function type annotations and tests for observable behavior.
- Document a real failure, its evidence path, and the exact remedy rather than inventing a quality claim.
- Include before/after command output or artifact hashes in story evidence.

## Changes and licensing

Repository-owned contributions are accepted for inclusion under the repository's [MIT licence](LICENSE), Copyright (c) 2026 Straughter Guthrie. Third-party models and weights remain governed by [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md); this repository cannot relicence them or grant rights to their outputs, so the MIT grant covers repository-owned code and documentation only.

For operator-facing release history, update [CHANGELOG.md](CHANGELOG.md). For architecture and process decision records, continue the existing corpus in `docs/`.
