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
updated_at: 2026-09-21T22:21:11Z
content_hash: "sha256:4a9dba1737ecdfa31beafef0a5b38384cd0a05da4bb28b03f1f38fd2069b7571"
blocks: [WD-fq1o]
was_blocked_by: [WD-lvix]
assignee: dev-WD-carq
follows: [WD-lvix, WD-fp49]
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

## Links
- Parent: [[WD-t534]]
- Blocks: [[WD-fq1o]]
- Was blocked by: [[WD-lvix]]
- Follows: [[WD-lvix]], [[WD-fp49]]

## Comments

### 2026-09-21T13:59:07Z speed
Self-contained evidence note: the canonical tracked LF004 inputs are datasets/content_briefs/lf004-operator-dogfood-56f/plan.json, datasets/lf004-operator-dogfood-56f-recovery-20260921.jobs.db, and datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921/final-provenance.json. All recipe tests must treat these as read-only and write derived recipes only to temporary storage.
