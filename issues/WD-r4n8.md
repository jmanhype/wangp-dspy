---
id: WD-r4n8
title: "Finishing: honor film-grain size and temporal_persistence in the emitted command graph"
status: in_progress
priority: 1
type: feature
labels: [capability, finishing, evidence]
parent: WD-3nod
created_at: 2026-09-26T02:04:03Z
created_by: speed
updated_at: 2026-09-26T02:04:16Z
content_hash: "sha256:c1ed7ae5381644a4fcd106331fd967601e15db95e38a53238a28d8f510bd9071"
assignee: dev-WD-r4n8
follows: [WD-fay0]
---

## Description
## Why (measured evidence, all on main @ 9cc501d6)

The finishing surface declares film-grain controls it never applies:

- `predict/finishing.py:187-192` — `FilmGrainControls` declares `strength`, `size`
  (default 16, ge=4, le=64) and `temporal_persistence` (default 0.5, ge=0, le=1)
  with `extra="forbid"`, so these are validated, frozen request inputs.
- `predict/finishing.py:367` — `settings["film_grain"] = request.film_grain.model_dump(mode="json")`
  records the full control set into `backend_settings`, and
  `backend_settings_sha256` hashes it.
- `services/finishing/pipeline.py:266` — the emitted command graph is ONLY
  `noise=alls={strength:g}:allf=t+u`. `size` and `temporal_persistence` never
  reach the command.
- Host measurement `datasets/runs/maestro-parity/WD-r81u/execution-summary.md:15`:
  `noise=alls=12:allf=t+u:all_seed=2935` — "actual pixel grain size is 1 and
  temporal persistence is 0 (new noise each frame)"; line 18 records the same
  1 / 0 for the WanGP film-grain path.

Consequence: the plan's recorded settings and its emitted command disagree, and
the measured media follows the command. This is exactly the contradiction
recorded in `datasets/runs/maestro-parity/WD-fay0/evidence-index.json` — row
`film`, cell Film grain: "Measured film-grain pixel size 1 and temporal
persistence 0 contradict planned controls 16 and 0.5." The `film` row cannot
reach a terminal evidence-backed state while the command cannot honour the
controls it accepts. ffmpeg's `noise` filter is per-pixel by construction and
`allf=t` reseeds every frame, so the declared size/persistence are unreachable
without a different graph.

## Acceptance criteria

- AC1: For identical requests differing only in `film_grain.size`, the emitted
  film-grain command graph differs and each encodes its own `size`. A request's
  `size` is never silently dropped.
- AC2: For identical requests differing only in `temporal_persistence`, the
  emitted graph differs; `1.0` holds grain across frames (temporal correlation)
  rather than reseeding every frame, and `0.0` reseeds every frame.
- AC3: Determinism is preserved: same request and `recipe_seed` produce
  byte-identical plan records, including `backend_settings_sha256` and any
  command-hash fields.
- AC4: Fail closed. Any backend/operation pair that cannot honour a non-default
  `size` or `temporal_persistence` returns a typed exit-2 rejection naming the
  control; it never silently drops the control and never falls back to another
  backend.
- AC5: Plan-only invariants hold unchanged: no host contact, no execution, no
  GPU work, no model download; records keep `plan_only=true`, `executable=false`,
  `queue_submitted=false`, `host_contact=false`, `media_generated=false`,
  `measurement_status=unverified`, and the `jobs` table stays absent.
- AC6: `docs/finishing-capabilities.md` states the applied grain semantics
  (what `size` and `temporal_persistence` now mean in the graph) and updates the
  `film` row disposition honestly to match what the command graph can deliver.
- AC7: Standing gates stay green: `pvg lint --backlog` 0 errors;
  `uv run --frozen --extra dev pytest -q` 0 failures/errors per JUnit counters;
  `wgp release verify` release=ready with tag_created=false.

## Constraints

- Do not execute any render and do not contact the host; this is the deterministic
  plan surface. Verification of produced media is a later authorized batch.
- Protected engine files (services/jobs/queue.py, services/director/renderers/policy.py,
  services/director/wiring.py, services/jobs/preflight.py, scripts/run_film.py) must
  stay unchanged.
- No new capability outside the finishing matrix row.

## nd_contract
status: new

### evidence
- (pending)

### proof
- [ ] AC1: size changes the emitted graph and is encoded
- [ ] AC2: temporal_persistence changes the emitted graph; 1.0 holds grain
- [ ] AC3: plan records stay byte-identical/deterministic for a fixed request+seed
- [ ] AC4: unsupported controls fail closed with a typed exit-2 naming the control
- [ ] AC5: plan-only invariants unchanged (no host contact, no execution)
- [ ] AC6: docs/finishing-capabilities.md updated and film row honest
- [ ] AC7: lint + pytest + release verify green

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-26T02:04:16Z status: open -> in_progress
- 2026-09-26T02:04:16Z auto-follows: linked to predecessor WD-fay0
- 2026-09-26T02:04:16Z claimed by dev-WD-r4n8

## Links
- Parent: [[WD-3nod]]
- Follows: [[WD-fay0]]

## Comments
