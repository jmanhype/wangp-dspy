---
id: WD-r4n8
title: "Finishing: honor film-grain size plus temporal_persistence in the emitted command graph"
status: closed
priority: 1
type: feature
labels: [capability, finishing, evidence, accepted]
parent: WD-3nod
created_at: 2026-09-26T02:04:03Z
created_by: speed
updated_at: 2026-09-26T03:17:49Z
content_hash: "sha256:4b973528f6164937452bc1e971aeebd26a17fa865ac9d5bb9a3b1450a42669ce"
assignee: dev-WD-r4n8
follows: [WD-fay0, WD-dmf2, WD-bxhc]
closed_at: 2026-09-26T03:17:49Z
close_reason: "AC1-AC7 independently reproduced at 3edd0282da0cb7b8983debd3c10b86b908c4046a: real-source grain graphs differ by encoded size/persistence, plans deterministic, plan-only invariants and fail-closed film rejection verified, docs honest, full suite/lint/release/diff and scope gates green."
led_to: [WD-i7qs, WD-14ej, WD-isg9]
blocks: [WD-fay0]
---

## Description
### Why (measured evidence, all on main @ 9cc501d6)

The finishing surface declares film-grain controls it never applies:

- `predict/finishing.py:187-192` — `FilmGrainControls` declares `strength`, `size`
  (default 16, ge=4, le=64) and `temporal_persistence` (default 0.5, ge=0, le=1)
  with `extra="forbid"`, so these are validated, frozen request inputs.
- `predict/finishing.py:367` records the full control set into `backend_settings`,
  and `backend_settings_sha256` hashes it.
- `services/finishing/pipeline.py:266` emitted only
  `noise=alls={strength:g}:allf=t+u`; `size` and `temporal_persistence` never
  reached the command.
- Host measurement in `datasets/runs/maestro-parity/WD-r81u/execution-summary.md`
  found actual pixel grain size 1 and temporal persistence 0, contradicting the
  declared defaults 16 and 0.5.

The plan's recorded settings and emitted command therefore disagreed, and measured
media followed the command. FFmpeg's bare `noise` filter is per-pixel by
construction and `allf=t` reseeds every frame, so the declared controls require a
different graph or a typed refusal.

### Acceptance criteria

- AC1: Identical requests differing only in `film_grain.size` emit different
  film-grain graphs, each encoding its own size; size is never silently dropped.
- AC2: Identical requests differing only in `temporal_persistence` emit different
  graphs. Persistence 1.0 holds grain across frames, while 0.0 reseeds every frame.
- AC3: The same request and `recipe_seed` produce byte-identical plan records,
  including `backend_settings_sha256` and command-hash fields.
- AC4: Any backend/operation that cannot honour a non-default size or persistence
  returns a typed exit-2 rejection naming the control; it never silently drops the
  control or falls back to another backend.
- AC5: Plan-only invariants remain unchanged: no host contact, execution, GPU work,
  or model download; records keep `plan_only=true`, `executable=false`,
  `queue_submitted=false`, `host_contact=false`, `media_generated=false`, and
  `measurement_status=unverified`, and the `jobs` table remains absent.
- AC6: `docs/finishing-capabilities.md` states the applied grain semantics and
  updates the film disposition honestly to match the graph.
- AC7: Standing gates remain green: backlog lint has 0 errors; the full suite has
  0 failures/errors; release verification reports `release=ready` with
  `tag_created=false`.

### Constraints

- Do not execute any render and do not contact the host. Verification of produced
  media belongs to a later authorized batch.
- Protect `services/jobs/queue.py`, `services/director/renderers/policy.py`,
  `services/director/wiring.py`, `services/jobs/preflight.py`, and
  `scripts/run_film.py` from changes.
- Add no capability outside the finishing matrix row.

## MANDATORY SKILLS
- pvg

## MANDATORY SKILLS
- pvg

### Superseded malformed body
#### Description
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

#### Acceptance criteria

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

#### Constraints

- Do not execute any render and do not contact the host; this is the deterministic
  plan surface. Verification of produced media is a later authorized batch.
- Protected engine files (services/jobs/queue.py, services/director/renderers/policy.py,
  services/director/wiring.py, services/jobs/preflight.py, scripts/run_film.py) must
  stay unchanged.
- No new capability outside the finishing matrix row.

#### MANDATORY SKILLS
- pvg

#### nd_contract
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

#### Acceptance Criteria


#### Design


#### Notes


#### History
- 2026-09-26T02:04:16Z status: open -> in_progress
- 2026-09-26T02:04:16Z auto-follows: linked to predecessor WD-fay0
- 2026-09-26T02:04:16Z claimed by dev-WD-r4n8

#### Links
- Parent: [[WD-3nod]]
- Follows: [[WD-fay0]]

#### Comments

#### Why (measured evidence, all on main @ 9cc501d6)

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

#### Acceptance criteria

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

#### Constraints

- Do not execute any render and do not contact the host; this is the deterministic
  plan surface. Verification of produced media is a later authorized batch.
- Protected engine files (services/jobs/queue.py, services/director/renderers/policy.py,
  services/director/wiring.py, services/jobs/preflight.py, scripts/run_film.py) must
  stay unchanged.
- No new capability outside the finishing matrix row.

#### nd_contract
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

#### Acceptance Criteria


#### Design


#### Notes


#### History
- 2026-09-26T02:04:16Z status: open -> in_progress
- 2026-09-26T02:04:16Z auto-follows: linked to predecessor WD-fay0
- 2026-09-26T02:04:16Z claimed by dev-WD-r4n8
- 2026-09-26T02:47:58Z dep_added: blocks WD-fay0

## History
- 2026-09-26T02:51:31Z status: in_progress -> in_progress
- 2026-09-26T02:51:31Z auto-follows: linked to predecessor WD-dmf2
- 2026-09-26T02:52:46Z status: in_progress -> in_progress
- 2026-09-26T02:52:46Z auto-follows: linked to predecessor WD-bxhc
- 2026-09-26T03:17:49Z status: in_progress -> closed
- 2026-09-26T03:17:49Z dep_removed: no_longer_blocks WD-fay0
- 2026-09-26T04:30:28Z dep_added: blocks WD-fay0
- 2026-09-26T20:50:57Z dep_added: blocks WD-mulc
- 2026-09-26T20:53:07Z dep_removed: no_longer_blocks WD-mulc
- 2026-09-26T20:53:10Z dep_added: blocks WD-e96x
- 2026-09-26T20:53:44Z dep_removed: no_longer_blocks WD-e96x

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-fay0]], [[WD-dmf2]], [[WD-bxhc]]
- Led to: [[WD-i7qs]], [[WD-14ej]], [[WD-isg9]]

## Notes

### Implementation Evidence
- Commit/push: `3edd0282da0cb7b8983debd3c10b86b908c4046a` on `story/WD-r4n8`; `git ls-remote origin refs/heads/story/WD-r4n8` returned the same SHA.
- AC1/AC2 graph proof: size 4 emits `scale=ceil(iw/4):ceil(ih/4)` and `scale=iw*4:ih*4`; size 64 emits `scale=ceil(iw/64):ceil(ih/64)` and `scale=iw*64:ih*64`. Persistence 0 emits `blend=all_mode=normal:all_opacity=0`; persistence 1 emits `all_opacity=1`. Both graphs retain seeded `allf=u` held and `allf=t+u` reseeded branches, so the emitted graph differs for each control.
- AC3: two compilations of the same request/seed produced identical canonical plan bytes, `backend_settings_sha256=09cfe594f5ccb081af18edfe31ecda055881e7db218a6e1f6ec81c75f84d2cc5`, and `command_graph_sha256=c88faff36f3628acd6874b1a085e6a73ac5b2a99426d99ef6d911aef9da80a4d`.
- AC4: backend `film` with grain controls exits through typed `FINISH_GRAIN_CONTROL_UNSUPPORTED`, naming `film_grain.size` and `film_grain.temporal_persistence`; no ffmpeg fallback is emitted.
- AC5: compiled record invariants were `plan_only=True`, `executable=False`, `queue_submitted=False`, `host_contact=False`, `media_generated=False`, `measurement_status=unverified`; plan-only compilation created no `jobs` table. No render, GPU work, host contact, model download, or network operation was performed.
- AC6: `docs/finishing-capabilities.md` now defines the ceil-grid/nearest-neighbor size semantics, static-versus-reseeded persistence blend, and honest unmeasured/fail-closed film dispositions.
- Full suite: `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-r4n8-full.xml` passed after commit; parsed JUnit `tests=2089,failures=0,errors=0,skipped=1`. The pre-commit attempt had two release-tree failures caused solely by the intentionally dirty working tree and was superseded by the clean-tree run.
- Backlog lint: `pvg lint --backlog` PASS, 127 scanned, 0 errors, 0 review findings.
- Release: `uv run --frozen --extra dev wgp release verify` returned `release=ready`, `tag_created=false`.
- Whitespace/protected parity: `git diff --check` exit 0; protected-file diff from `9cc501d6` exit 0.
Delivery proof headings normalized for verify-delivery.


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-25.

### proof
- [x] Story closed after accepted label was applied.


## Implementation Evidence
The ffmpeg graph now generates grain on a ceil(width/size) x ceil(height/size) nearest-neighbor grid, then crops to the exact frame. It seeds and blends one held `allf=u` branch with one reseeded `allf=t+u` branch using `temporal_persistence` as the held-pattern opacity. Requests for the non-native `film` backend fail closed with `FINISH_GRAIN_CONTROL_UNSUPPORTED`; they do not fall back to ffmpeg.

### CI/Test Results
Commands run:
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-r4n8-full.xml`
- `uv run --frozen --extra dev python /tmp/WD-r4n8-evidence.py`
- `pvg lint --backlog`
- `uv run --frozen --extra dev wgp release verify`
- `git diff --check`
- `git diff --exit-code 9cc501d6 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
- `git push -u origin story/WD-r4n8`
- `git ls-remote origin refs/heads/story/WD-r4n8`
- `pvg story deliver WD-r4n8`
- `pvg story verify-delivery WD-r4n8`

Summary: full suite PASS with JUnit tests=2089, failures=0, errors=0, skipped=1; graph-diff/determinism proof PASS; lint PASS with 0 errors and 0 review findings; release=ready with tag_created=false; diff-check and protected-file parity exit 0; no render/host/network work occurred.

Commit SHA: 3edd0282da0cb7b8983debd3c10b86b908c4046a

### AC Verification
- [x] AC1: size 4 versus 64 changes and is encoded by the ceil/downsample and nearest-neighbor upscale graph.
- [x] AC2: persistence 0 versus 1 changes `all_opacity`; 1 selects the held pattern and 0 selects the reseeded pattern.
- [x] AC3: identical request/seed compilations produced identical plan bytes and matching settings/command hashes.
- [x] AC4: non-native film grain fails closed with typed exit-2 `FINISH_GRAIN_CONTROL_UNSUPPORTED`, naming both controls.
- [x] AC5: plan-only record flags remain false for execution/queue/host/media and measurement remains unverified; no jobs table is created.
- [x] AC6: docs define applied semantics and honestly mark ffmpeg grain unmeasured and film fail-closed.
- [x] AC7: lint, clean-tree full suite, release verify, diff-check, and protected-file parity pass.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-25.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.
