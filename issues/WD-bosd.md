---
id: WD-bosd
title: "Adopt the MIT licence with the recorded copyright holder"
status: in_progress
priority: 2
type: task
labels: [licence, hygiene]
created_at: 2026-09-22T18:33:06Z
created_by: speed
updated_at: 2026-09-22T18:33:18Z
content_hash: "sha256:fdd934e7ab0c79310f309b5bbdddd4143ab1adb31c9af34b16966b423413e5a2"
assignee: dev-WD-bosd
---

## Description
## USER INTENT
Observable outcome: the repository carries a real, unambiguous open-source licence -- the MIT licence, naming the copyright holder Straughter Guthrie -- instead of the source-available notice that granted no rights, and the repository's own fail-closed licence test proves the adopted licence rather than the retired notice.

## Context (Embedded)
- Recorded owner decision (2026-09-22, operator): licence = MIT, copyright holder = Straughter Guthrie. The retired `LICENSE` notice stated: "A permissive open-source licence may replace this notice at any time, but only by an explicit, recorded decision of the repository owner." This story records and applies that decision.
- `tests/test_readme_quickstart.py::test_repository_hygiene_and_readme_contract` currently asserts the retired notice ("All rights reserved", "NO LICENCE GRANTED", and explicitly that "MIT License" is absent). That assertion exists to make a silent licence change impossible; it must be inverted to assert the adopted MIT licence and its holder, so the guard keeps working in the new direction.
- `LICENSE` is referenced by `README.md` ("Version, changes, contribution, and licences"), `CONTRIBUTING.md` ("Changes and licensing" claims source-available/no rights), `CHANGELOG.md` (0.1.0 entry), and is packaged into the wheel/sdist by hatchling. `pyproject.toml` currently declares no licence metadata.
- Third-party constraints are unaffected: `THIRD_PARTY_NOTICES.md` governs models, weights, datasets, hosted services and generated media, and this repository cannot licence or relicence them.

## OUT OF SCOPE
- Any change to `THIRD_PARTY_NOTICES.md` third-party terms, model usage constraints, or upstream licence claims.
- Creating a Git tag, release, publishing to PyPI, or any external publication.
- Any change to renderer, queue, provenance, QC, gate, retry, CLI verb, or recipe/release verification semantics.
- Any other repository hygiene file beyond the licence surface named in the boundary map.

## DIFF BUDGET
- Roughly 5 files, under 120 authored changed LOC.

## Boundary Map
PRODUCES:
- LICENSE -> the unmodified MIT licence text with `Copyright (c) 2026 Straughter Guthrie`.
- pyproject.toml -> declared licence metadata consistent with the LICENSE file.
- tests/test_readme_quickstart.py -> hygiene assertions that the MIT licence text and the Straughter Guthrie copyright line are present, and that the retired no-grant notice is gone.
- CONTRIBUTING.md -> licensing section states contributions are accepted under MIT.
- CHANGELOG.md -> 0.1.0 entry records the licence adoption (documentation only).
CONSUMES:
- README.md -> "Version, changes, contribution, and licences" link to LICENSE stays accurate.

## Required Outcomes
1. `LICENSE` contains the standard MIT licence text with the copyright line `Copyright (c) 2026 Straughter Guthrie` and no remaining source-available language.
2. `pyproject.toml` declares `MIT` as the project licence so built artifacts report it.
3. The hygiene test fails if the licence is silently changed in either direction: it asserts the MIT grant, the holder, and the absence of the retired no-grant notice.
4. README and CONTRIBUTING describe the licence accurately; CHANGELOG records the change.
5. `uv build` still produces both a wheel and an sdist, and `wgp release verify` still reports `release=ready` with `tag_created=false`.

## Testing Requirements
- Real-process, no mocks: `uv run --frozen --extra dev pytest tests/test_readme_quickstart.py -q` and the full `uv run --frozen --extra dev pytest -q`.
- `uv build --out-dir <tmp>` must produce exactly one wheel and one sdist.
- `uv run --frozen --extra dev wgp release verify` must remain green (it checks VERSION, package metadata, changelog entry, recipe schema, and clean tree).

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must paste targeted and full-suite output, the build result, and the release-verification output into notes.
- Developer must include an AC verification table and the sha256 of the new LICENSE.
- Developer must use `pvg story deliver`.
- No GPU, SSH, network, model inference, tag, release, publish, or push to main is authorized; the story branch and its PR are the only push target.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-22T18:33:18Z status: open -> in_progress
- 2026-09-22T18:33:18Z claimed by dev-WD-bosd

## Links


## Comments
