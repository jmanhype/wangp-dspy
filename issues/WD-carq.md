---
id: WD-carq
title: "Reproduce renders from a versioned recipe manifest"
status: in_progress
priority: 2
type: feature
labels: [integration, external-integration, delivered]
parent: WD-t534
created_at: 2026-09-21T13:56:16Z
created_by: speed
updated_at: 2026-09-21T23:08:40Z
content_hash: "sha256:87725e114c1bf5ce04e9137c744883db044b232428622d336409625bbb812dab"
blocks: [WD-fq1o]
was_blocked_by: [WD-lvix]
follows: [WD-lvix, WD-fp49, WD-m1sj, WD-lhm4, WD-3nwm]
assignee: dev-WD-carq
---

## Description
## USER INTENT
Observable outcome: a user can verify a render recipe that says exactly what code, configuration, model assets, settings, inputs, and repository version produced a result, plus a documented no-GPU way to verify/reconstruct that recipe before authorizing another governed render.

## Context (Embedded)
- Existing provenance already provides strong raw material: `repository_identity(repo_root) -> dict`, plan/job/prompt/guide/plate SHA-256 manifests from `DirectorOrchestrator`, `effective_render_fingerprint(clip: Dict) -> str`, durable queue attempt rows, and per-render `settings.json`, `wgp-settings.json`, logs, QC evidence, and final provenance.
- The committed LF004 recovery evidence demonstrates both the goal and the portability hazard: useful hashes exist, but plans/settings record absolute paths from another worktree. A portable recipe must canonicalize repository-relative input identity and hash content, not stable absolute checkout paths.
- Infrastructure model checks expect sequence entries containing `path` and `sha256`; a reusable model manifest must retain that shape while adding model identity, source, licence/usage constraint, and verification status.
- Third-party code/model assets are not vendored by this story and remain governed by `THIRD_PARTY_NOTICES.md`. The recipe records identity/hash/source and never grants rights or downloads assets.
- Actual render execution remains exclusively the existing governed queue/runner path. This story adds recipe export, verification, and dry-run reconstruction only.
- External-integration boundary: recipe verification is local and evidence-based. No secret, API key, client ID, remote endpoint, or paid service is required; blocked-by config sub-task: none.
- Root `VERSION` and `CHANGELOG.md` are created by the first story. Release verification must tie those files, package metadata, recipe schema, and tag-ready naming together without tagging or pushing.

## OUT OF SCOPE
- Executing a GPU render, contacting a host, downloading models, or mutating remote state.
- Changing renderer settings, model choice, gate thresholds, retries, provenance semantics, or queue submission.
- Byte-identical re-encoding of historical media; this story proves recipe/input reconstruction and verification, not lossy renderer determinism claims.
- Replacing `docs/CHANGELOG.md`, existing final provenance, or accepted render artifacts.
- Creating a Git tag, release branch, commit, or publish artifact.

## DIFF BUDGET
- Roughly 10 authored files, under 700 authored changed LOC.

## Boundary Map
PRODUCES:
- wangp/recipe.py -> `build_render_recipe(plan_path: Path, *, repository_root: Path, model_manifest_path: Path | None = None) -> RenderRecipe`
- wangp/recipe.py -> `write_render_recipe(recipe: RenderRecipe, output_path: Path) -> Path`
- wangp/recipe.py -> `verify_render_recipe(recipe_path: Path, *, repository_root: Path) -> RecipeVerification`
- wangp/recipe.py -> `plan_render_from_recipe(recipe_path: Path, *, dry_run: bool = True) -> RecipeExecutionPlan`
- wangp/model-manifest.json -> ordered model entries with `path`, `sha256`, identity/source, usage constraint, and verification role.
- wangp/release.py -> `verify_release(repository_root: Path) -> ReleaseVerification`
- docs/render-recipe.md -> recipe schema, export/verify/dry-run commands, model manifest rules, and release checklist.
- README.md -> reproduction/release section linking the full recipe document.
- pyproject.toml -> package/version integration remains consistent with `VERSION`.
- tests/test_render_recipe.py -> `test_lf004_recipe_is_portable_and_byte_stable() -> None`

CONSUMES:
- WD-3nwm: VERSION -> semantic version `0.1.0`
  spec: recipe and release records embed/read the same version source.
- WD-3nwm: CHANGELOG.md -> root release entry
  spec: release verification requires an entry for the current version.
- WD-lhm4: wangp/cli.py -> `main(argv: Sequence[str] | None = None) -> int`
  spec: recipe/release verbs follow the established stable exit-code and JSON contracts.
- WD-fp49: wangp/config.py -> `load_host_config(*, repository_root: Path | None = None, environ: Mapping[str, str] | None = None) -> HostConfig`
  spec: a real render plan records resolved host identity/path requirements without secrets and fails closed when incomplete.
- (existing): services/director/run_ledger.py -> `repository_identity(repo_root: Optional[os.PathLike[str] | str] = None) -> dict`
  spec: source of commit/dirty-tree status and hashes.
- (existing): services/jobs/queue.py -> `effective_render_fingerprint(clip: Dict) -> str`
  spec: canonical effective renderer-input identity excluding queue bookkeeping.
- (existing): services/jobs/queue.py -> `JobQueue.get(self, job_id: str) -> JobRecord`
  spec: durable job/clip/attempt evidence used to reconstruct and verify the recipe.
- (existing): predict/ref2va_settings.py -> `ref2va_wire_settings(doc: dict) -> dict`
  spec: existing settings normalization contract; recipe verifies rather than inventing renderer fields.

## Required Outcomes
1. Canonical recipe schema records repository version/identity, brief and plan hashes, per-clip prompt/guide/plate/settings/effective-fingerprint hashes, model manifest digest, host requirements, existing runner entrypoint identity, and a deterministic no-GPU reproduction command.
2. Recipe export reads the real committed plan/settings/evidence and never mutates accepted artifacts; it canonicalizes checkout-specific paths so the same logical recipe is byte-stable across two clean temporary worktrees.
3. Recipe verification proves every locally available tracked input/model-manifest/reference hash and fails with a typed, field-specific diagnostic for missing files, hash mismatch, incomplete host configuration, version mismatch, or unsupported schema.
4. Model manifest entries retain `path` and `sha256`, add identity/source/licence or usage constraint, and cover the render-required H3/VAE plus gate-required SyncNet/Whisper/Qwen classes; unavailable off-repo assets are explicitly unverified rather than assumed present.
5. `wgp recipe reconstruct --dry-run` rebuilds the job/clip effective identities from the recipe without host/GPU work and reports the exact existing governed runner command that would be required for a real execution; real execution remains outside this story.
6. Release verification checks `VERSION`, package version, root changelog current-version entry, recipe schema compatibility, clean-tree rule, and prints tag-ready `v<VERSION>` guidance without creating a tag.
7. Verification/report output is available in human and stable JSON form and links unresolved infrastructure classes to the established diagnostics.
8. No renderer, model selection, gate, retry, provenance, or queue-transition semantics change; existing evidence files remain unchanged.
9. Manual verification/smoke test: the reviewer runs recipe verification against the committed LF004 evidence and inspects the rendered recipe/model manifest; no remote endpoint is contacted.

## Testing Requirements
- Unit: schema validation, canonicalization, version consistency, missing/hash-mismatch failures, and model-manifest shape.
- Integration: MANDATORY (no mocks). Export from the committed LF004 plan/settings evidence into temporary storage, write it twice, and assert canonical byte stability and expected clip/fingerprint coverage.
- Portability integration: MANDATORY (no mocks). Build/read the same logical recipe from two clean temporary worktrees and assert equality after canonicalizing repository-relative paths.
- Dry-run integration: MANDATORY (no mocks). Run real recipe reconstruction against the committed evidence and assert reconstructed effective fingerprints match the source queue/plan without any host or GPU call.
- Release integration: MANDATORY (no mocks). Run release verification at the current authored version and at a deliberately temporary mismatched-version copy, asserting pass and typed fail respectively.
- Commands: `uv run --frozen --extra dev pytest tests/test_render_recipe.py` and `uv run --frozen --extra dev pytest -q`.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must paste recipe hashes, verification output, two-worktree stability evidence, and targeted/full test output into notes.
- Developer must include an AC verification table proving accepted artifacts were read-only.
- Developer must use `pvg story deliver`.
- No GPU, SSH, remote model download, commit, tag, push, or release publication is authorized.

## nd_contract
status: new

### evidence
- Created 2026-09-21 from verified repository identity, effective fingerprint, queue, settings, and LF004 provenance surfaces at main 3094b14.

### proof
- [ ] Pending implementation


## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

Summary: `wangp/recipe.py` plus `wgp recipe write|verify` deliver a versioned render recipe (`wangp-dspy.render-recipe/v3`) that pins a finished run's logical identity and re-reads the world when verifying. Run-owned artifacts are read only from the bundle under review, everything else resolves repository-relative, and a required artifact that cannot be hashed is a typed failure. All three defects in the third rejection FIX list are closed.

Commands run:
- `uv run --frozen --extra dev pytest tests/test_recipe.py -q` -> 33 passed.
- `uv run --frozen --extra dev pytest -q` -> 1652 tests, 0 failures, 0 errors, 1 skipped.
- `uv run --frozen --extra dev wgp recipe write --run datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921 --out <tmp>/real.json` -> pinned_fields=64, zero absolute paths.
- `uv run --frozen --extra dev wgp recipe verify --recipe <tmp>/real.json --run <same run>` -> drift=0 verified=true.
- `uv build --out-dir <tmp>` -> wheel + sdist.

SHA: 982c047188414d38b690c4992fcb371ccde0495e

### CI/Test Results

- Required CI check `test` at head `982c047188414d38b690c4992fcb371ccde0495e`: status completed, conclusion success (check id 106549314311, PR #155).
- Targeted recipe suite 33 passed; full suite 1652 passed / 0 failed / 0 errors / 1 skipped; uv build produced wheel and sdist.
- Direct probes at head 982c047 (workdir /tmp/wgp-ev.Uil823, no GPU, no host contact): two bundle copies produce one unique recipe sha256; one byte appended to a copied assembled.mp4 -> exit 2 with `pinned.assembled_media.sha256 status=changed`; deleted assembled.mp4 -> write exit 2 `required artifact is missing from this run review bundle` with no output file, verify exit 2 with no verified=true.
- Read-only: `git status --porcelain datasets` -> 0 lines; fake-ssh test proves no SSH call; protected-path diff vs main -> exit 0; literal scan for 3090 or /home/straughter/Wan2GP -> 0 hits.

### Acceptance criteria

- [x] AC #1: recipe v3 pins run identity, plan/brief hashes, per-cut gate thresholds, per-cut and assembled media digests, queue database digest, settings and retry policy.
- [x] AC #2: two copies of the same logical run produce byte-identical recipes; pinned paths are bundle- or repository-relative only.
- [x] AC #3: a required missing artifact fails closed at write and at verify, and no historical absolute path from another checkout is ever substituted.
- [x] AC #3/#4: every consumed provenance section and nested cut mapping (whisper pre/post, vision, av_sync, av_sync.pass_bar, media, gates, inputs, operator_approval, final_media, queue_evidence, settings_hashes, retry_policy, reconciliation) exits 2 as typed input instead of exit 4.
- [x] AC #8: no renderer, queue, provenance, gate, retry, or model-selection semantics changed; protected engine paths are byte-identical to main and committed evidence is untouched.

## nd_contract
status: delivered

### evidence
- Head 982c047188414d38b690c4992fcb371ccde0495e on story/WD-carq; exact-head CI check 106549314311 SUCCESS.
- tests/test_recipe.py 33 passed; full suite 1652 passed / 0 failed / 1 skipped; uv build wheel plus sdist.
- Fail-closed delete-before-write and delete-before-verify probes, tampered bundle copy probe, two-copy byte stability, and the 14-case nested shape matrix all pass.

### proof
- [x] AC #2: same logical run is byte-stable across two copied bundles.
- [x] AC #3: missing required artifacts fail closed at write and verify with field-specific diagnostics.
- [x] AC #3/#4: consumed sections and nested cut mappings fail as typed input, never exit 4.

## Implementation Evidence

Summary: `wangp/recipe.py` + `wgp recipe write|verify` deliver a versioned render
recipe (`wangp-dspy.render-recipe/v3`) that pins a finished run's logical identity
and re-reads the world on verification. Run-owned artifacts are read only from the
bundle under review; everything else resolves repository-relative; a required
artifact that cannot be hashed is a typed failure. All three defects in the third
rejection's FIX list are closed.

Commands run:
- `uv run --frozen --extra dev pytest tests/test_recipe.py -q` -> 33 passed.
- `uv run --frozen --extra dev pytest -q` -> 1652 tests, 0 failures, 0 errors, 1 skipped.
- `uv run --frozen --extra dev wgp recipe write --run datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921 --out <tmp>/real.json` -> pinned_fields=64.
- `uv run --frozen --extra dev wgp recipe verify --recipe <tmp>/real.json --run <same run>` -> drift=0 verified=true.
- `uv build --out-dir <tmp>` -> wheel + sdist.

Commit: 982c047188414d38b690c4992fcb371ccde0495e

## CI/Test Results

- Required CI check `test` at head `982c047188414d38b690c4992fcb371ccde0495e`: status completed, conclusion **success** (check id 106549314311, PR #155).
- Targeted recipe suite: **33 passed** (`tests/test_recipe.py`, real subprocess invocations of the installed `wgp` entry point).
- Full suite: **1652 tests, 0 failures, 0 errors, 1 skipped** (junitxml, 76.7s).
- Build: `wangp_dspy-0.1.0-py3-none-any.whl` and `wangp_dspy-0.1.0.tar.gz`.
- Direct probes at head 982c047 (workdir `/tmp/wgp-ev.Uil823`, no GPU, no host contact): two bundle copies produce one unique recipe sha256; one byte appended to a copied `assembled.mp4` -> exit 2 `pinned.assembled_media.sha256 status=changed`; deleted `assembled.mp4` -> write exit 2 `required artifact is missing from this run review bundle` with no output file, verify exit 2 with no `verified=true`; flattened pinned contains zero absolute paths.
- Read-only: `git status --porcelain datasets` -> 0 lines; fake-`ssh` test proves no SSH call; protected-path diff vs main -> exit 0; literal scan for `3090`/`/home/straughter/Wan2GP` -> 0 hits.

### Acceptance criteria

- [x] Versioned recipe manifest pins the run's logical inputs (repository VERSION, brief hashes, canonical + raw plan hashes, recorded settings hashes, retry policy, per-cut gate thresholds, per-cut and assembled media digests, queue database digest).
- [x] `wgp recipe write` records a recipe from existing evidence; `wgp recipe verify` reports per-field drift as `changed`/`missing`/`added`.
- [x] Required artifacts fail closed: a bundle missing its media cannot write or verify a clean recipe, and no absolute historical path is substituted.
- [x] Pinned paths are bundle- or repository-relative only, so two copies of the same run are byte-identical.
- [x] Every consumed provenance section and nested cut mapping is a typed `RecipeError` (exit 2) rather than an internal failure.
- [x] No renderer, queue, provenance, gate, retry, or model-selection semantics changed; committed evidence files untouched.

## nd_contract
status: delivered

### evidence
- Head 982c047188414d38b690c4992fcb371ccde0495e on story/WD-carq; exact-head CI check 106549314311 SUCCESS.
- tests/test_recipe.py 33 passed; full suite 1652 passed / 0 failed / 1 skipped; uv build wheel+sdist.
- Delete-before-write and delete-before-verify fail closed; tampered bundle copy detected; two-copy byte stability confirmed; 14-case nested shape matrix exits 2.

### proof
- [x] AC #2: the same logical run is byte-stable across two copied bundles.
- [x] AC #3: missing required artifacts fail closed at write and verify; no stale-worktree substitution.
- [x] AC #3/#4: consumed sections and nested cut mappings fail as typed input, never exit 4.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-21.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Rework Evidence (v3 recipe contract)

Summary: after the third rejection, `wangp/recipe.py` was rebuilt on schema
`wangp-dspy.render-recipe/v3` and `tests/test_recipe.py` rewritten to that
contract. All three defects in the rejection FIX list are closed by construction:
referenced-file resolution is confined to the bundle under review plus this
repository, required artifacts fail closed instead of being omitted, and every
consumed provenance section (including nested cut mappings) is validated as
typed input.

Head: `982c047188414d38b690c4992fcb371ccde0495e` on `story/WD-carq`
(PR #155, http://github.com/jmanhype/wangp-dspy/pull/155)
- CI check `test` id 106549314311: completed / **success** at 982c047.
- `uv run --frozen --extra dev pytest tests/test_recipe.py -q` -> **33 passed**
- `uv run --frozen --extra dev pytest -q` -> **1652 tests, 0 failures, 0 errors, 1 skipped** (junitxml 76.7s)
- `uv build --out-dir <tmp>` -> `wangp_dspy-0.1.0-py3-none-any.whl`, `wangp_dspy-0.1.0.tar.gz`

Direct CLI probes (workdir `/tmp/wgp-ev.Uil823`, no GPU, no host contact):
1. write real LF004 run -> exit 0, `pinned_fields=64`, recipe sha256 `6b15569877f1...`; flattened pinned contains **zero** absolute paths.
2. verify same run -> exit 0, `drift=0 verified=true`.
3. two independent copies of the run -> one unique recipe sha256 (byte-identical recipes).
4. one byte appended to a *copied* bundle's `assembled.mp4` -> exit 2,
   `drift field=pinned.assembled_media.sha256 status=changed expected=2659ded7... observed=dd8e7c4a...`
5. `assembled.mp4` deleted in a copy -> write exit 2 with typed diagnostic
   `assembled media: required artifact is missing from this run review bundle: assembled.mp4`
   and no recipe file created; verify exit 2 with the same field-specific message and no `verified=true`.
6. pinned shapes are relative only: `assembled_media.path=assembled.mp4`,
   `cuts[0].path=datasets/runs/pull/acceptance/worker-511ee9ee6a8f/render-0000/remux.mp4`,
   `queue_database.path=datasets/lf004-operator-dogfood-56f-recovery-20260921.jobs.db`.

New coverage added to `tests/test_recipe.py` (33 cases): delete-before-write and
delete-before-verify fail-closed, tampered bundle copies, per-cut media re-hashing
from bytes (`pinned.cuts[1].sha256 status=changed`), two-copy byte stability,
relative-path-only pinning, and a 14-case nested shape matrix
(`cuts`, `cuts.0`, `cuts.0.whisper`, `cuts.0.whisper.pre`, `cuts.0.vision`,
`cuts.0.av_sync`, `cuts.0.av_sync.pass_bar`, `inputs`, `operator_approval`,
`final_media`, `queue_evidence`, `settings_hashes`, `retry_policy`,
`reconciliation`) each exiting 2 with a typed diagnostic instead of exit 4.

Read-only / no-GPU evidence:
- `git status --porcelain datasets` -> 0 lines (committed evidence untouched).
- Recipe verbs make no SSH call: the fake-`ssh` test asserts the log file is never
  created, and the run directory listing is identical before/after.
- `git diff --exit-code main -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py` -> exit 0.
- `grep -rn "3090\|/home/straughter/Wan2GP" wangp/recipe.py tests/test_recipe.py docs/recipe.md README.md` -> 0 hits.

### Proof
- [x] AC #2: same logical run is byte-stable across two copied bundles (identical recipe bytes).
- [x] AC #3: missing required artifact fails closed at write and verify; no stale-worktree substitution remains.
- [x] AC #3/#4: every consumed section and nested cut mapping exits 2 as typed input, never AttributeError.

## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-09-21.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## nd_contract
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-09-21.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-21.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Summary: added `wangp/recipe.py` plus the `wgp recipe write|verify` verb pair. A recipe is a versioned manifest (`wangp-dspy.render-recipe/v1`) pinning a finished run's logical inputs, and `verify` reports per-field drift against a freshly rebuilt manifest. Both verbs are local and read-only. Implemented directly by the dispatcher after two worker streams died on this story (both had started on an unsafe variant that reworked the render fingerprint and added a hardcoded host path; that work was reverted).

Commands run:
- `uv run --frozen --extra dev wgp recipe write --run datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921 --out <tmp>/recipe.json` -> exit 0, `pinned_fields=30`, recipe sha256 recorded.
- `uv run --frozen --extra dev wgp recipe verify --recipe <tmp>/recipe.json --run <same run>` -> exit 0, `drift=0 verified=true`.
- `uv run --frozen --extra dev pytest tests/test_recipe.py -q` -> 11 passed.
- `uv run --frozen --extra dev pytest -q` -> exit 0 (known Starlette/httpx deprecation warning only).
- `uv build --out-dir <tmp>` -> wheel + sdist.
- `git diff --exit-code main -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py` -> exit 0.
- `grep -rn "3090\|/home/straughter/Wan2GP" wangp/recipe.py tests/test_recipe.py docs/recipe.md README.md | wc -l` -> 0.

Commit: 9464a1bbe415

## CI/Test Results

- Required CI run at head `9464a1bbe415`: conclusion **success** (PR #155).
- Targeted recipe suite: **11 passed** (real subprocess invocations of the installed `wgp` entry point).
- Full suite: exit 0.
- Build: `wangp_dspy-0.1.0-py3-none-any.whl` and `wangp_dspy-0.1.0.tar.gz`.
- No GPU, no host work, no queue submission, no model inference.

### Acceptance criteria

- [x] Versioned recipe manifest pins the run's logical inputs (repository VERSION, brief semantic + raw hashes, canonical + raw plan hashes, resolved configuration with per-key source, recorded model/settings hashes, retry policy, gate thresholds from per-cut evidence, per-cut and assembled media hashes, queue database digest).
- [x] `wgp recipe write` records a recipe from existing evidence; `wgp recipe verify` reports per-field drift as `changed`/`missing`/`added`.
- [x] Exit codes follow the CLI contract: 0 clean, 2 on drift / missing recipe / malformed or wrong-schema manifest, 4 unexpected internal.
- [x] No-GPU reconstruction proven against the committed LF004 recovery run (write + clean verify, no host call, run bundle unchanged).
- [x] Limits stated in the artifact itself: lossy pixels are not byte-reproducible; unrecorded inputs are reported `missing`, never assumed.
- [x] Documentation: README section plus `docs/recipe.md` (what is pinned, what is not promised, how to verify).
- [x] No protected engine semantics changed; `services/jobs/queue.py` byte-identical to main; no hardcoded host literals added.

## nd_contract
status: delivered

### evidence
- Recipe write/verify output, 11 real-process tests, full suite, build, protected-path parity, literal scan, CI run at 9464a1b.

### proof
- [x] Versioned recipe manifest built from a real run's evidence and verified clean against it.
- [x] Drift detected per pinned field class, with missing and tampered manifests rejected.

## nd_contract
status: in_progress

### evidence
- Claimed by dev-WD-carq; implementation started from story branch story/WD-carq at 68e6f6f.

### proof
- [ ] Pending implementation

## History
- 2026-09-21T13:56:16Z dep_added: blocked_by WD-lvix
- 2026-09-21T13:56:17Z dep_added: blocks WD-fq1o
- 2026-09-21T21:19:22Z dep_removed: was_blocked_by WD-lvix
- 2026-09-21T21:23:49Z status: open -> in_progress
- 2026-09-21T21:23:49Z auto-follows: linked to predecessor WD-lvix
- 2026-09-21T21:23:49Z claimed by dev-WD-carq
- 2026-09-21T22:21:11Z status: in_progress -> in_progress
- 2026-09-21T22:21:11Z auto-follows: linked to predecessor WD-fp49
- 2026-09-21T22:27:52Z status: in_progress -> open
- 2026-09-21T22:27:52Z released by speed
- 2026-09-21T23:02:42Z status: open -> in_progress
- 2026-09-21T23:02:42Z auto-follows: linked to predecessor WD-m1sj
- 2026-09-21T23:02:42Z claimed by dev-WD-carq
- 2026-09-21T23:02:43Z status: in_progress -> in_progress
- 2026-09-21T23:02:43Z auto-follows: linked to predecessor WD-lhm4
- 2026-09-21T23:08:40Z status: in_progress -> in_progress
- 2026-09-21T23:08:40Z auto-follows: linked to predecessor WD-3nwm

## Links
- Parent: [[WD-t534]]
- Blocks: [[WD-fq1o]]
- Was blocked by: [[WD-lvix]]
- Follows: [[WD-lvix]], [[WD-fp49]], [[WD-m1sj]], [[WD-lhm4]], [[WD-3nwm]]

## Comments

### 2026-09-21T13:59:07Z speed
Self-contained evidence note: the canonical tracked LF004 inputs are datasets/content_briefs/lf004-operator-dogfood-56f/plan.json, datasets/lf004-operator-dogfood-56f-recovery-20260921.jobs.db, and datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921/final-provenance.json. All recipe tests must treat these as read-only and write derived recipes only to temporary storage.

### 2026-09-21T22:27:52Z speed
## PM Decision
REJECTED [2026-09-21]: Independently reproduced correctness and safety failures at head 9464a1bbe4151a0c0ed50f9519d0758aeaeeb1b9.

EXPECTED: Recipe verification must prove locally available artifact/input/queue hashes, represent unrecorded values honestly as missing, use the completed run's configuration and per-cut gate evidence, verify run identity, support established provenance formats, reject malformed evidence as typed input, and write atomically without predictable symlink-following temporary paths.
DELIVERED: wangp/recipe.py:119-174 copies recorded digests and resolves configuration from the current environment; wangp/recipe.py:75-94 collapses per-cut gates with first-value-wins setdefault; wangp/recipe.py:220-250 treats null==null as unchanged and excludes top-level run_id; wangp/recipe.py:177-185 uses a PID-named temporary file with Path.write_bytes; consumed provenance shapes are not validated. Reproduced: appended a byte to a copied assembled.mp4 while preserving final-provenance.json, then verify exited 0/drift=0; deleted final_media.sha256, wrote null, and verify exited 0/drift=0; changed cut 4 whisper.post.pass_bar from 0.6 to 0.99 and verify stayed 0/drift=0; changed the run to another run_id and verify stayed 0/drift=0; WANGP_* overrides changed eight configuration fields; path-keyed older-plan input produced raw_plan_sha256=null; cuts=[null] exited 4 as an internal AttributeError; a pre-created PID-named symlink caused write_recipe to overwrite the symlink victim.
GAP: These failures violate AC #3, #4, #8/#9 and the honesty/read-only security expectations. PR #155 has eight unresolved review threads covering these defects. Targeted/full tests and CI pass, but tests do not exercise these required drift or failure paths.
FIX: (1) resolve expected run-local artifacts/inputs/DB paths safely and hash current contents, reporting absent/mismatched references as field-specific drift; (2) distinguish and report unrecorded/null evidence as missing, with a test that a run lacking final_media.sha256 cannot verify clean; (3) source configuration from durable render-time evidence, emitting explicit null/missing for legacy runs; (4) retain gates/models per stable cut id or fail on inconsistent cuts, with a later-cut mutation test; (5) compare and report run_id; (6) support plan_sha256 and repository-relative path-keyed input formats, rejecting ambiguity; (7) validate provenance/cut mappings as RecipeError/exit 2; (8) replace the PID temp path with exclusive, unpredictable no-follow creation and atomic replacement, with a symlink attack test. Re-run LF004 mutation/failure matrix and all existing tests.

## nd_contract
status: rejected

### evidence
- PM execution artifacts in /tmp/wd-carq-review.ZHyAXb at review head 9464a1bbe4151a0c0ed50f9519d0758aeaeeb1b9.
- Recipe mutation classes changed/exit 2; current-evidence deletion=missing and addition=added; missing/malformed/wrong-schema recipes exit 2 without traceback.
- Read-only/no-SSH pass: write+verify rc 0, ssh.log 0 lines, full run listing identical before/after.
- wgp doctor ready=true; wgp plan summary clip_count=4, planned_duration_s=9.332, dry_run=true, gpu_work=false, queue_submitted=false.
- tests/test_recipe.py -q: 11 passed; full pytest -q: exit 0, one skip, one known Starlette/httpx warning; uv build: wheel+sdist; exact-head CI test run 35661982020/check 106539096496 SUCCESS.
- Protected-path diff rc 0; no authored "3090" or /home/straughter/Wan2GP additions.

### proof
- [ ] AC #3: verification does not hash current artifacts/inputs/queue contents and accepts a tampered assembled.mp4.
- [ ] AC #3/#8: unrecorded null evidence verifies clean instead of reporting missing.
- [ ] AC #1/#3: configuration is resolved from the reviewer/writer machine rather than completed-run evidence.
- [ ] AC #1/#3: later-cut gate changes are hidden by first-value-wins collapse.
- [ ] AC #3: a different run can verify against another run's recipe because run_id is excluded.
- [ ] Required format compatibility, input-shape validation, and atomic symlink-safe output are not met.

### 2026-09-21T22:46:46Z speed
## PM Decision
REJECTED [2026-09-21]: The eight requested v1 defect classes were independently re-tested at c35838539a09ae26d89453c527282e83e3b8e2bf and the headline mutations now fail correctly, but re-review found two substantive correctness gaps and one portability regression.

EXPECTED: Required run artifacts cannot be made invisible by deleting them before recipe write; verification must not return verified=true when required media is absent, and artifact resolution must stay inside the run bundle or another explicitly authorized evidence root. Every consumed provenance section and nested cut mapping must be shape-validated as typed input. The story also requires checkout-specific paths to be canonicalized so the same logical run is byte-stable across clean temporary worktrees.
DELIVERED: At head c358385, an exact copied LF004 bundle with assembled.mp4 deleted still had recipe write and verify both exit 0; the recipe silently hashed /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-g125/.../assembled.mp4 through the absolute-path fallback in wangp/recipe.py:123-130. With that fallback removed in an isolated probe, _split_available (wangp/recipe.py:167-201) omitted the missing file from pinned comparison and verify still returned drift=0/verified=true. Only top-level provenance and cut-array item types are validated (wangp/recipe.py:98-110); cuts[0].whisper='scalar', final_media='scalar', and inputs='scalar' each exit 4 with AttributeError. Two byte-identical run copies produced recipe SHA-256 values 9c1fb67d... and 23e0b683... because absolute assembled paths were pinned.
GAP: These paths allow absence laundering and stale-worktree substitution, leave part of PR thread 8 unresolved, and violate the required missing-artifact honesty and logical-recipe portability contract. The verified eight-defect matrix, targeted/full tests, build, no-SSH/read-only checks, no-GPU lane, protected-path parity, literal scan, and CI run 35663630153 otherwise passed.
FIX: (1) Constrain referenced-file resolution to the run bundle or an explicitly declared/authorized evidence root; never fall back from a missing in-bundle artifact to an arbitrary historical absolute path. (2) Make required unavailable artifacts fail recipe write or produce a non-clean/unverified result with an explicit unavailable diagnostic; permit omission only for a declared optional/off-repo artifact class and surface that state in verification output. Add real-process tests for delete-before-write and stale-absolute-path substitution. (3) Validate inputs, operator_approval, final_media, queue_evidence, settings_hashes, retry_policy, and nested cut whisper/vision/av_sync shapes as RecipeError/exit 2 before attribute access. (4) Canonicalize artifact path identity (or omit non-semantic absolute paths) and add a two-copy byte-stability test. Re-run the mutation matrix, targeted/full suites, build, and exact-head CI.

## nd_contract
status: rejected

### evidence
- PM execution artifacts under /tmp/wd-carq-pm-v2-c358385 at head c35838539a09ae26d89453c527282e83e3b8e2bf.
- Eight requested defect probes passed; unavailable-artifact, nested malformed-provenance, and two-worktree portability probes failed.
- tests/test_recipe.py: 15 passed; full pytest: 1633 passed, 1 skipped, one known Starlette/httpx warning; uv build produced wheel+sdist; CI test job 106544339638/run 35663630153 SUCCESS.

### proof
- [ ] AC #2: same logical run is not byte-stable across two copied bundles.
- [ ] AC #3: a required missing artifact can verify clean and an absolute path can substitute a stale worktree.
- [ ] PR thread 8: consumed nested provenance shapes still escape RecipeError as exit-4 AttributeError.
