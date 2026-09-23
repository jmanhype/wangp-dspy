---
id: WD-dt94
title: "README tour: capability status, verb map, and docs index"
status: open
priority: 2
type: task
labels: [documentation]
created_at: 2026-09-23T06:52:21Z
created_by: speed
updated_at: 2026-09-23T06:52:21Z
content_hash: "sha256:31247814313367329435a6e2d09bf8377da40677ad21d5bc09fa8f147ebbec2b"
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


## History


## Links


## Comments
