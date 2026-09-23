---
id: WD-dt94
title: "README tour: capability status, verb map, and docs index"
status: closed
priority: 2
type: task
labels: [documentation, accepted]
created_at: 2026-09-23T06:52:21Z
created_by: speed
updated_at: 2026-09-23T07:31:08Z
content_hash: "sha256:b222147324dc41f272c9c303edb05c4e2e70f52adb460bc7e5385c9a703e9b28"
assignee: dev-WD-dt94
closed_at: 2026-09-23T07:31:07Z
close_reason: "Accepted: exact-head 580b362d is docs-only, verb map matches the live CLI, links resolve, quickstart stays intact, targeted/full tests pass, release is ready, CI is green, and delivery proof is 9/9."
---

## Description
## USER INTENT
Observable outcome: a stranger opening the repository can see, in one screen of README, what the product does today, which capabilities are planning-only versus generation, every first-class `wgp` verb, and where the detailed documents live. Today the README documents install, quickstart, host configuration, recipes and release readiness but has no capability-status section, no verb map covering the video/image/music/speech/first-run lanes, and no index of the capability documents.

## Context (Embedded)
- Verified at main `080fe1a`: `wgp --help` exposes `{video,image,music,speech,first-run,doctor,content,brief,plan,status,review,recipe,release}`; capability documents exist for video, image, music, voice, first-run and content; every capability row is `planned` with no generation evidence.
- The reference product (Maestro) presents capability breadth on its front page. Our equivalent must be honest: planning-only surfaces may be named as planning, and generation must stay explicitly unverified.
- `tests/test_readme_quickstart.py` executes the README quickstart and asserts required README phrases; any README change must keep that test passing (or update it deliberately with justification).

## OUT OF SCOPE
- Any code change: no CLI, module, renderer, queue, gate, recipe or release behaviour may change.
- Any capability claim beyond what a recorded run bundle proves.
- Rewriting existing sections that are already accurate; this is additive and structural.

## DIFF BUDGET
- Roughly 3 files, under 250 authored changed LOC.

## Boundary Map
PRODUCES:
- README.md -> a capability-status section (implemented planning surfaces versus generation, explicitly marked unverified), a verb map with a one-line purpose for every `wgp` verb, and a docs index linking each capability document, the install guide, the content guide, the recipe document, the release checklist and the first-run guide.
- docs/README-MAP.md (or an equivalent single index) if the README would otherwise become unwieldy.
- tests/test_readme_quickstart.py -> extend the existing contract test to assert the new sections exist and name the current verbs, so the tour cannot silently drift from the CLI.
CONSUMES:
- wangp/cli.py -> the verb list must match `wgp --help` exactly; the test should derive or assert the same set.
- docs/*-capabilities.md -> links only; do not modify those documents.

## Required Outcomes
1. README names every currently available `wgp` verb with a one-line purpose, and the test asserts that set matches the CLI so a new verb cannot ship undocumented.
2. README states plainly which capabilities are planning-only and that no generation is verified, with links to each capability document.
3. README links the install, content, recipe, release and first-run documents from one index section.
4. The existing quickstart remains byte-identical in behaviour and `uv run --frozen --extra dev pytest tests/test_readme_quickstart.py -q` passes.
5. No code, gate, queue, renderer, recipe or release semantics change; the repository stays release-ready (`wgp release verify` reports `release=ready`).

## Testing Requirements
- Real-process: `uv run --frozen --extra dev pytest tests/test_readme_quickstart.py -q` and the full `uv run --frozen --extra dev pytest -q` with parsed JUnit counters.
- The README quickstart commands are executed by the test; keep them unchanged.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must paste the new README structure (section list), the targeted and full-suite counters, `wgp release verify` output, and the exact-head CI conclusion into notes.
- Developer must include an AC verification table and must use `pvg story deliver`.
- No GPU, SSH, network, tag, publish, or code change is authorized; the story branch and its PR are the only push target.

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence
Summary: Added an honest README capability tour, CLI-derived verb map, documentation index, and drift tests; docs-only scope preserved.

Commands run:
- `uv run --frozen --extra dev wgp --help`
- `pvg verify README.md tests/test_readme_quickstart.py --format=text`
- `uv run --frozen --extra dev pytest tests/test_readme_quickstart.py -q --junitxml=<tmp>/t.xml`
- `uv run --frozen --extra dev pytest -q --junitxml=<tmp>/f.xml`
- `uv run --frozen --extra dev wgp release verify`
- `git push origin story/WD-readme-tour`
- `gh pr create --base main --head story/WD-readme-tour --title "docs(WD-dt94): README capability tour"`
- `gh api repos/jmanhype/wangp-dspy/commits/580b362d3b31793ba3cf45a89a5b0fe911d99e2d/check-runs`

SHA: 580b362d3b31793ba3cf45a89a5b0fe911d99e2d

### CI/Test Results
- PR: https://github.com/jmanhype/wangp-dspy/pull/169
- Files: `README.md` 39 insertions / 0 deletions; `tests/test_readme_quickstart.py` 60 insertions / 2 deletions.
- README headings added: `Capability status`, `` `wgp` verb map ``, `Documentation index`.
- Documented verbs in CLI order: `video`, `image`, `music`, `first-run`, `voice`, `doctor`, `content`, `brief`, `plan`, `status`, `review`, `recipe`, `release`.
- Targeted parsed JUnit: `tests=5 errors=0 failures=0 skipped=0 exit=0`.
- Full parsed JUnit: `tests=1819 errors=0 failures=0 skipped=1 exit=0`; the single skip is the pre-existing environment-gated live-3090 integration test, correctly not run under this no-host/no-GPU story. Output also carries the pre-existing FastAPI/Starlette deprecation warning.
- `wgp release verify`: `version=0.1.0`, all checks pass, `tag-ready=v0.1.0`, `tag_created=false`, `release=ready`.
- `pvg verify README.md tests/test_readme_quickstart.py --format=text`: `VERIFY: PASSED (1 files scanned, 0 issues)`.
- Exact-head CI check run for SHA `580b362d3b31793ba3cf45a89a5b0fe911d99e2d`: `test`, `completed`, `success`.

### AC Verification
| AC | Result | Evidence |
| --- | --- | --- |
| 1 | PASS | README verb map at `README.md:109`; live CLI set asserted by `tests/test_readme_quickstart.py:259`. |
| 2 | PASS | Planning-only/no-generation status and existing capability links at `README.md:14`; links checked by `tests/test_readme_quickstart.py:230`. |
| 3 | PASS | Documentation index links install, content, first-run, capability plans, recipe, and release checklist at `README.md:198`. |
| 4 | PASS | Quickstart commands remain unchanged; targeted suite executed them with 5/5 passing. |
| 5 | PASS | Diff contains only `README.md` and `tests/test_readme_quickstart.py`; full suite exit 0 and `release=ready` with `tag_created=false`. |

## nd_contract
status: delivered

### evidence
- Commit: `580b362d3b31793ba3cf45a89a5b0fe911d99e2d`
- PR: https://github.com/jmanhype/wangp-dspy/pull/169
- Targeted tests: 5 passed, 0 failed, exit 0.
- Full tests: 1819 passed, 0 failed, 1 no-host-gated 3090 skip, exit 0.
- Release verify: `release=ready`, `tag_created=false`.
- CI: exact-head `test` check completed with `success`.

### proof
- [x] AC #1: README names every current `wgp` verb, and the test derives the exact set from `wgp --help`.
- [x] AC #2: README marks each existing capability surface planning/readiness-only and states generation is not verified.
- [x] AC #3: README documentation index links the required guides, recipe/release documents, first-run guide, and capability documents.
- [x] AC #4: The existing quickstart behavior is unchanged and its targeted test suite passes.
- [x] AC #5: No code/gate/queue/renderer/recipe/release semantics changed and `wgp release verify` reports ready.

## History
- 2026-09-23T06:52:27Z status: open -> in_progress
- 2026-09-23T06:52:27Z claimed by dev-WD-dt94
- 2026-09-23T07:18:34Z status: in_progress -> in_progress
- 2026-09-23T07:31:07Z status: in_progress -> closed

## Links


## Comments
