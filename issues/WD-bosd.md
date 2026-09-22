---
id: WD-bosd
title: "Adopt the MIT licence with the recorded copyright holder"
status: closed
priority: 2
type: task
labels: [licence, hygiene, delivered]
created_at: 2026-09-22T18:33:06Z
created_by: speed
updated_at: 2026-09-22T18:46:17Z
content_hash: "sha256:d2c529f0c7d69b078fc5047e69947389fabc288522fb37473d72ee21f6bd5c61"
assignee: dev-WD-bosd
closed_at: 2026-09-22T18:46:17Z
close_reason: "Accepted: exact-head 4b12f9f has canonical MIT LICENSE with Straughter Guthrie holder, MIT build metadata, passing targeted/full tests and CI, release=ready, no tag."
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


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-22.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Summary: LICENSE replaced with the canonical MIT text (`Copyright (c) 2026 Straughter Guthrie`), pyproject now declares `license = "MIT"` with `license-files`, the repository hygiene guard was inverted so it now asserts the MIT grant and holder instead of the retired no-rights notice, and README, CONTRIBUTING, CHANGELOG and the THIRD_PARTY_NOTICES pointer describe the adopted licence. Third-party model terms are untouched.

Commands run:
- `uv run --frozen --extra dev pytest tests/test_readme_quickstart.py -q` -> 3 passed.
- `uv run --frozen --extra dev pytest -q` -> 1660 tests, 0 failures, 0 errors, 1 skipped.
- `uv build --out-dir <tmp>` -> one wheel and one sdist; wheel METADATA reports `License-Expression: MIT` and `License-File: LICENSE`, and the wheel ships `dist-info/licenses/LICENSE`.
- `uv run --frozen --extra dev wgp release verify` -> version/changelog/recipe_schema/tree all `pass`, `release=ready`, `tag_created=false`.
- `shasum -a 256 LICENSE` -> `ca04658a538e5347a4f863758ce72f307a49fe103a8f8af3cf7ced5bac76711b`.

SHA: 4b12f9ff26a3e7be7413df02b1374ee62fa0a766

### CI/Test Results

- Exact-head CI check `test` at `4b12f9ff26a3e7be7413df02b1374ee62fa0a766`: completed/success (check id 106883801870, PR #158).
- Targeted hygiene suite 3 passed; full suite 1660 passed / 0 failed / 0 errors / 1 skipped.
- Build produced exactly one wheel and one sdist; the wheel metadata carries `License-Expression: MIT`.
- The first full-suite run failed only `test_clean_checkout_and_real_repository_are_release_ready` because the worktree was still dirty with these edits; the same test passes once the change is committed, which is the repo's own clean-tree guard working as designed.
- No tag, release, publish, GPU, SSH, or network work was performed; the only push was `story/WD-bosd`.

### AC Verification

| AC | Result | Evidence |
| --- | --- | --- |
| 1. LICENSE carries canonical MIT text with the recorded holder | PASS | `LICENSE` is the standard MIT grant with `Copyright (c) 2026 Straughter Guthrie`; sha256 `ca04658a538e5347a4f863758ce72f307a49fe103a8f8af3cf7ced5bac76711b`; no source-available language remains. |
| 2. pyproject declares MIT so artifacts report it | PASS | `license = "MIT"` + `license-files = ["LICENSE"]`; built wheel METADATA shows `License-Expression: MIT`, `License-File: LICENSE`. |
| 3. The hygiene guard fails closed in the new direction | PASS | `tests/test_readme_quickstart.py` asserts the MIT grant, the exact holder line, and the absence of `All rights reserved` / `NO LICENCE GRANTED`; the retired assertions were replaced, not deleted. |
| 4. Docs describe the licence; CHANGELOG records the change | PASS | README licence bullet, CONTRIBUTING licensing section, THIRD_PARTY_NOTICES pointer, and a new `### Changed` bullet under 0.1.0 naming WD-bosd. |
| 5. Build and release verification still pass | PASS | `uv build` produced wheel plus sdist; `wgp release verify` reports all four checks `pass`, `release=ready`, `tag_created=false`. |
| 6. Third-party terms untouched | PASS | Only the repository-licence pointer sentence changed in `THIRD_PARTY_NOTICES.md`; the asserted third-party phrases ("WanGP Non-Commercial Evaluation 1.1", "MiniMax H3", "SyncNet v2", "does not licence, relicence, or waive conditions") are intact and still asserted by the hygiene test. |

## nd_contract
status: delivered

### evidence
- Head 4b12f9ff26a3e7be7413df02b1374ee62fa0a766 on story/WD-bosd; exact-head CI check 106883801870 completed/success (PR #158).
- Targeted hygiene suite 3 passed; full suite 1660 passed / 0 failed / 1 skipped; build produced wheel plus sdist with `License-Expression: MIT`; `wgp release verify` green.

### proof
- [x] AC #1: LICENSE is canonical MIT text with `Copyright (c) 2026 Straughter Guthrie` and no source-available language.
- [x] AC #2: pyproject declares MIT and built artifacts report `License-Expression: MIT`.
- [x] AC #3: the hygiene guard asserts the MIT grant and holder and rejects the retired no-rights notice.
- [x] AC #4: README, CONTRIBUTING, THIRD_PARTY_NOTICES pointer and CHANGELOG describe the adopted licence.
- [x] AC #5: wheel plus sdist build and `wgp release verify` remains `release=ready` with `tag_created=false`.
- [x] AC #6: third-party model and weight terms are unchanged.

## History
- 2026-09-22T18:33:18Z status: open -> in_progress
- 2026-09-22T18:33:18Z claimed by dev-WD-bosd
- 2026-09-22T18:41:11Z status: in_progress -> in_progress
- 2026-09-22T18:46:17Z status: in_progress -> closed

## Links


## Comments
