---
id: WD-14ej
title: "Finishing: honor interpolation scene_detection in the emitted minterpolate graph"
status: in_progress
priority: 2
type: bug
labels: [capability, finishing, evidence, delivered]
parent: WD-3nod
created_at: 2026-09-26T04:32:47Z
created_by: speed
updated_at: 2026-09-26T05:12:59Z
content_hash: "sha256:6d8ea8fc3a23bffe47c23356275134c8d78ee07549928c75ae9d5028de33dcb1"
blocks: [WD-fay0]
assignee: dev-WD-14ej
follows: [WD-i7qs, WD-r4n8]
---

## Description
## Why (same defect class as WD-r4n8, different control)

The finishing surface declares an interpolation control it never applies:

- `predict/finishing.py:177` declares `scene_detection: bool = True` on
  `InterpolationControls`, with `extra="forbid"`.
- `backend_settings` records interpolation (including `scene_detection`), so the
  value is captured in the plan record and hashed.
- `services/finishing/pipeline.py:247` emits, for the ffmpeg backend:

      minterpolate=fps={fps:g}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1

  with NO `scd` term. `scene_detection` never reaches the command graph.

Consequence: `scene_detection=False` is **silently ignored**. ffmpeg's
`minterpolate` defaults `scd` to `fdiff`, i.e. scene-change detection is ON, so a
caller who explicitly disables it still gets it. `scene_detection=True` is only
accidentally honoured because it happens to match the ffmpeg default, and even
then the graph never records the mode. The plan's recorded settings and its
emitted command therefore disagree.

Verified locally that ffmpeg can honour both directions:

    scd        <int>  0..1   scene change detection method (default fdiff)
    scd_threshold <double> 0..100  scene change threshold (default 10)

    minterpolate=...:scd=0  -> parses, exit 0
    minterpolate=...:scd=1  -> parses, exit 0
    minterpolate=...  (current, no scd) -> parses, exit 0

## Acceptance criteria

- AC1: `scene_detection=True` and `scene_detection=False` produce different emitted
  interpolation graphs, and each graph explicitly encodes the mode (`scd=1` for
  enabled, `scd=0` for disabled). Quote both command strings.
- AC2: No reliance on an ffmpeg default for a declared control. The emitted graph
  always states the scene-detection mode explicitly.
- AC3: Determinism preserved: same request and `recipe_seed` give byte-identical
  plan records, including `backend_settings_sha256` and `command_graph_sha256`.
- AC4: Plan-only invariants unchanged: no host contact, no execution, no GPU work,
  no model download; records keep `plan_only=true`, `executable=false`,
  `queue_submitted=false`, `host_contact=false`, `media_generated=false`,
  `measurement_status=unverified`, and the `jobs` table stays absent.
- AC5: Both emitted graphs are valid ffmpeg filter graphs, demonstrated by running
  each against a synthetic source to a null sink with no error.
- AC6: `docs/finishing-capabilities.md` states the applied interpolation semantics
  (what `scene_detection` now means in the graph) and stays honest that the graph is
  unexecuted and unmeasured.
- AC7: Standing gates green: `pvg lint --backlog` 0 errors;
  `uv run --frozen --extra dev pytest -q` 0 failures/errors per JUnit counters;
  `wgp release verify` release=ready with tag_created=false; `git diff --check` 0.

## Constraints

- Only `predict/finishing.py`, `services/finishing/pipeline.py`,
  `tests/test_finishing_capabilities.py`, `docs/finishing-capabilities.md` may change.
- Protected engine files (services/jobs/queue.py, services/director/renderers/policy.py,
  services/director/wiring.py, services/jobs/preflight.py, scripts/run_film.py) must
  stay unchanged.
- Do NOT execute a render and do NOT contact the host; this is the deterministic
  no-GPU plan surface. AC5's local ffmpeg parse check on a synthetic source is the
  only execution permitted, and it must not use any repository source media.
- Do not change the `scene_detection` default (True) or make previously valid
  requests invalid; this must not break the accepted `ffmpeg` Interpolation cell.

## MANDATORY SKILLS
None identified.

## nd_contract
status: new

### evidence
- (pending)

### proof
- [ ] AC1: scene_detection changes the emitted graph; scd=1 / scd=0 encoded
- [ ] AC2: graph states the mode explicitly, never relying on an ffmpeg default
- [ ] AC3: plan records stay deterministic and byte-identical for a fixed request
- [ ] AC4: plan-only invariants unchanged
- [ ] AC5: both graphs parse and run to a null sink without error
- [ ] AC6: docs/finishing-capabilities.md updated and honest
- [ ] AC7: lint + pytest + release verify + diff-check green

## Why (same defect class as WD-r4n8, different control)

The finishing surface declares an interpolation control it never applies:

- `predict/finishing.py:177` declares `scene_detection: bool = True` on
  `InterpolationControls`, with `extra="forbid"`.
- `backend_settings` records interpolation (including `scene_detection`), so the
  value is captured in the plan record and hashed.
- `services/finishing/pipeline.py:247` emits, for the ffmpeg backend:

      minterpolate=fps={fps:g}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1

  with NO `scd` term. `scene_detection` never reaches the command graph.

Consequence: `scene_detection=False` is **silently ignored**. ffmpeg's
`minterpolate` defaults `scd` to `fdiff`, i.e. scene-change detection is ON, so a
caller who explicitly disables it still gets it. `scene_detection=True` is only
accidentally honoured because it happens to match the ffmpeg default, and even
then the graph never records the mode. The plan's recorded settings and its
emitted command therefore disagree.

Verified locally that ffmpeg can honour both directions:

    scd        <int>  0..1   scene change detection method (default fdiff)
    scd_threshold <double> 0..100  scene change threshold (default 10)

    minterpolate=...:scd=0  -> parses, exit 0
    minterpolate=...:scd=1  -> parses, exit 0
    minterpolate=...  (current, no scd) -> parses, exit 0

## Acceptance criteria

- AC1: `scene_detection=True` and `scene_detection=False` produce different emitted
  interpolation graphs, and each graph explicitly encodes the mode (`scd=1` for
  enabled, `scd=0` for disabled). Quote both command strings.
- AC2: No reliance on an ffmpeg default for a declared control. The emitted graph
  always states the scene-detection mode explicitly.
- AC3: Determinism preserved: same request and `recipe_seed` give byte-identical
  plan records, including `backend_settings_sha256` and `command_graph_sha256`.
- AC4: Plan-only invariants unchanged: no host contact, no execution, no GPU work,
  no model download; records keep `plan_only=true`, `executable=false`,
  `queue_submitted=false`, `host_contact=false`, `media_generated=false`,
  `measurement_status=unverified`, and the `jobs` table stays absent.
- AC5: Both emitted graphs are valid ffmpeg filter graphs, demonstrated by running
  each against a synthetic source to a null sink with no error.
- AC6: `docs/finishing-capabilities.md` states the applied interpolation semantics
  (what `scene_detection` now means in the graph) and stays honest that the graph is
  unexecuted and unmeasured.
- AC7: Standing gates green: `pvg lint --backlog` 0 errors;
  `uv run --frozen --extra dev pytest -q` 0 failures/errors per JUnit counters;
  `wgp release verify` release=ready with tag_created=false; `git diff --check` 0.

## Constraints

- Only `predict/finishing.py`, `services/finishing/pipeline.py`,
  `tests/test_finishing_capabilities.py`, `docs/finishing-capabilities.md` may change.
- Protected engine files (services/jobs/queue.py, services/director/renderers/policy.py,
  services/director/wiring.py, services/jobs/preflight.py, scripts/run_film.py) must
  stay unchanged.
- Do NOT execute a render and do NOT contact the host; this is the deterministic
  no-GPU plan surface. AC5's local ffmpeg parse check on a synthetic source is the
  only execution permitted, and it must not use any repository source media.
- Do not change the `scene_detection` default (True) or make previously valid
  requests invalid; this must not break the accepted `ffmpeg` Interpolation cell.

## nd_contract
status: new

### evidence
- (pending)

### proof
- [ ] AC1: scene_detection changes the emitted graph; scd=1 / scd=0 encoded
- [ ] AC2: graph states the mode explicitly, never relying on an ffmpeg default
- [ ] AC3: plan records stay deterministic and byte-identical for a fixed request
- [ ] AC4: plan-only invariants unchanged
- [ ] AC5: both graphs parse and run to a null sink without error
- [ ] AC6: docs/finishing-capabilities.md updated and honest
- [ ] AC7: lint + pytest + release verify + diff-check green

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

### CI/Test Results
Commands run:
- uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-14ej-full.xml
- uv run --frozen --extra dev python /tmp/wd_14ej_verify.py
- pvg verify services/finishing/pipeline.py tests/test_finishing_capabilities.py docs/finishing-capabilities.md --format=text
- pvg lint --backlog
- uv run --frozen --extra dev wgp release verify
- git diff --check

Summary: full regression PASS with JUnit tests=2090, failures=0, errors=0, skipped=1; synthetic ffmpeg probes PASS for scd=1 and scd=0; pvg verify PASS; backlog lint PASS with 0 errors; release=ready tag_created=false; diff-check PASS.
Coverage: coverage collection was not requested; full no-GPU regression evidence is the JUnit XML.
Commit SHA: 2a564c5a544161def3fdc943ab6c254a2b8b8d38

### Commit
- Branch: story/WD-14ej
- SHA: 2a564c5a544161def3fdc943ab6c254a2b8b8d38
- Push: origin/story/WD-14ej at the same SHA.

### AC Verification
| AC # | Requirement | Code Location | Test Location | Status |
|------|-------------|---------------|---------------|--------|
| 1 | Explicit differing scd modes | services/finishing/pipeline.py:247-250 | tests/test_finishing_capabilities.py:444-468 | PASS |
| 2 | No ffmpeg default reliance | services/finishing/pipeline.py:247-250 | tests/test_finishing_capabilities.py:464-468 | PASS |
| 3 | Deterministic records and hashes | services/finishing/pipeline.py:352-415 | tests/test_finishing_capabilities.py:472-483 | PASS |
| 4 | Plan-only invariants | services/finishing/pipeline.py:384-415 | tests/test_finishing_capabilities.py:484-499 | PASS |
| 5 | Valid graphs on synthetic source | services/finishing/pipeline.py:247-250 | /tmp/wd_14ej_verify.py synthetic lavfi run | PASS |
| 6 | Honest interpolation docs | docs/finishing-capabilities.md:9 | docs review | PASS |
| 7 | Standing gates | N/A | CI/Test Results above | PASS |

## nd_contract
status: delivered

### evidence
- Commands and outputs recorded in CI/Test Results.
- Commit 2a564c5a544161def3fdc943ab6c254a2b8b8d38 is pushed.

### proof
- [x] AC1: explicit scd=1 and scd=0 graphs differ.
- [x] AC2: emitted graph always states scd.
- [x] AC3: repeated request has byte-identical record and matching hashes.
- [x] AC4: plan-only flags, unverified status, and absent jobs table verified.
- [x] AC5: both synthetic lavfi-to-null graphs exit 0.
- [x] AC6: semantics and unmeasured status documented.
- [x] AC7: lint, pytest, release, and diff-check gates pass.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-26.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

PROOF:

### Change
- Commit: `2a564c5a544161def3fdc943ab6c254a2b8b8d38` on `story/WD-14ej`.
- Diff: 3 files changed, 64 insertions(+), 1 deletion(-).
- `services/finishing/pipeline.py:247-250` now emits ffmpeg
  `minterpolate` with `scd=1` for `scene_detection=True` and `scd=0`
  for `scene_detection=False`.
- `tests/test_finishing_capabilities.py:444-499` covers both graphs,
  deterministic repeat records/hashes, and plan-only flags.
- `docs/finishing-capabilities.md:9` documents explicit `scd` semantics and
  keeps the graph unexecuted/unmeasured.

### Required verification
- Initial focused RED run failed exactly because the old graph had no `scd`:
  `AssertionError: ... 'minterpolate=fps=48:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1'.endswith(':scd=1')`.
- Final focused test: `uv run --frozen --extra dev pytest -q tests/test_finishing_capabilities.py::test_interpolation_scene_detection_is_explicit_deterministic_and_plan_only`
  -> `1 passed`.
- Plan probe (`uv run --frozen --extra dev python /tmp/wd_14ej_verify.py`,
  synthetic non-repository source):
  - enabled: `minterpolate=fps=48:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:scd=1`
  - disabled: `minterpolate=fps=48:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:scd=0`
  - repeated enabled record bytes identical; record SHA-256 both
    `ca408229762c561b2b46e89c314d28dc3d726fc14e82246d8082cc484502915e`
  - `backend_settings_sha256` and `command_graph_sha256` repeat matches.
  - `plan_only=true executable=false queue_submitted=false host_contact=false
    media_generated=false measurement_status=unverified jobs_table_absent=true`.
- Synthetic ffmpeg graphs (no repository media):
  `ffmpeg -v error -f lavfi -i testsrc=duration=0.2:size=128x96:rate=24 -vf <graph> -frames:v 3 -f null -`
  -> enabled exit 0; disabled exit 0.
- Full suite: `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-14ej-full.xml`.
  Parsed JUnit: tests=2090, failures=0, errors=0, skipped=1, time=970.275s.
  The sole skip is the explicitly env-gated live 3090 preflight; this story forbids host contact.
- `pvg verify services/finishing/pipeline.py tests/test_finishing_capabilities.py docs/finishing-capabilities.md --format=text`
  -> `VERIFY: PASSED (2 files scanned, 0 issues)` (docs need no code scan).
- `pvg lint --backlog` -> scanned 129 issues, 0 errors, 0 review findings.
- `uv run --frozen --extra dev wgp release verify` -> all four checks pass,
  `tag_created=false`, `release=ready`. Bare shell `wgp` was not on PATH, so the
  project venv entry point was used.
- `git diff --check` -> exit 0.
- Push: `git push -u origin story/WD-14ej`; remote head equals local
  `2a564c5a544161def3fdc943ab6c254a2b8b8d38`.

### AC Verification
| AC | Result | Evidence |
| --- | --- | --- |
| 1 | PASS | Explicit `scd=1` / `scd=0` graphs differ; strings quoted above; test lines 464-468. |
| 2 | PASS | Both graphs state `scd`; implementation never omits the declared control. |
| 3 | PASS | Repeated request serialized record bytes and both hashes match. |
| 4 | PASS | Plan-only flags, unverified measurement, executed=false, and absent jobs table recorded above. |
| 5 | PASS | Both graphs run from synthetic lavfi testsrc to null sink with exit 0. |
| 6 | PASS | Docs state enabled/disabled semantics and unexecuted/unmeasured status. |
| 7 | PASS | Lint, full pytest counters, release ready/tag false, and diff-check recorded above. |

LEARNINGS:
- A split f-string fragment must itself be prefixed with `f`; the first synthetic
  ffmpeg run caught a literal `{fps:g}` and prevented shipping an invalid graph.
- Full release tests intentionally treat an uncommitted story worktree as dirty;
  commit before the authoritative full-suite/release verification.
- Keep host-gated 3090 tests skipped under this no-host story rather than violating
  the no-contact constraint.

### OBSERVATIONS (unrelated)
- [CONCERN] dependency warning: FastAPI's testclient import emits
  `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated`;
  no failures. This is outside the four owned files.

## nd_contract
status: delivered

### evidence
- Commit `2a564c5a544161def3fdc943ab6c254a2b8b8d38`, pushed to `origin/story/WD-14ej`.
- Full JUnit 2090/0/0; lint 0 errors; release ready with no tag; diff-check clean.
- Synthetic ffmpeg probes exit 0 for both `scd=1` and `scd=0`.

### proof
- [x] AC1: both explicit, different interpolation graphs quoted above.
- [x] AC2: emitted graph always includes `scd`; no ffmpeg default reliance.
- [x] AC3: same request/seed yields byte-identical record and matching hashes.
- [x] AC4: all plan-only invariants and absent jobs table verified.
- [x] AC5: both synthetic lavfi-to-null ffmpeg runs exit 0.
- [x] AC6: applied semantics and unmeasured status documented.
- [x] AC7: all standing gates green per evidence above.

## History
- 2026-09-26T04:32:53Z dep_added: blocks WD-fay0
- 2026-09-26T04:32:54Z status: open -> in_progress
- 2026-09-26T04:32:54Z auto-follows: linked to predecessor WD-i7qs
- 2026-09-26T04:32:54Z claimed by dev-WD-14ej
- 2026-09-26T05:11:44Z status: in_progress -> in_progress
- 2026-09-26T05:11:44Z auto-follows: linked to predecessor WD-r4n8

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-i7qs]], [[WD-r4n8]]

## Comments
