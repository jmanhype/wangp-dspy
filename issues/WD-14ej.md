---
id: WD-14ej
title: "Finishing: honor interpolation scene_detection in the emitted minterpolate graph"
status: open
priority: 2
type: bug
labels: [capability, finishing, evidence]
parent: WD-3nod
created_at: 2026-09-26T04:32:47Z
created_by: speed
updated_at: 2026-09-26T04:32:47Z
content_hash: "sha256:ee03bbc6018f6e06312c4628d6836451b349616f1882b39a56338e461ceea4b4"
blocks: [WD-fay0]
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


## History
- 2026-09-26T04:32:53Z dep_added: blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]

## Comments
