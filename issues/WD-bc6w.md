---
id: WD-bc6w
title: "E2e: onboard a stranger to a stable no-GPU Wangp workflow"
status: open
priority: 2
type: feature
labels: [capstone, e2e]
parent: WD-8zod
created_at: 2026-09-21T13:54:13Z
created_by: speed
updated_at: 2026-09-21T13:54:13Z
content_hash: "sha256:c4494576fadfc40ee787b56bd374f156c1c93b3f2af77ece90bccd6cb8ed5a01"
blocked_by: [WD-i8w6, WD-k32a, WD-zkcu]
---

## Description
## USER INTENT
Observable outcome: a user can install the stabilized repository, produce a no-GPU plan, understand queue/review state, receive actionable failures, and verify a reproducible recipe in one continuous product experience. This capstone proves the epic from the user's perspective, not through isolated unit seams.

## Context (Embedded)
- This story runs only after repository documentation, stable CLI verbs, host configuration, diagnostics, and recipe/release verification are accepted.
- The end-to-end lane is deliberately no-GPU/no-network: dependency setup, committed-brief validation/planning, local doctor, queue status/review on a real database, unconfigured-host failure behavior, diagnostic rendering, recipe verification, and release-readiness reporting.
- A clean checkout is required because repository identity intentionally fail-closes on opaque untracked directories. The test must not weaken that rule.
- No accepted render artifact may be modified.

## OUT OF SCOPE
- Any new implementation feature or repair; a failure here reopens the owning child story rather than expanding the capstone.
- GPU rendering, remote host access, model inference/download, external/paid APIs, tagging, publishing, commit, or push.
- Mocking the CLI, queue, filesystem, subprocesses, plan, diagnostics, recipe, or version surfaces.

## DIFF BUDGET
- Roughly 2 authored files, under 250 authored changed LOC.

## Boundary Map
PRODUCES:
- tests/e2e/test_production_stability.py -> `test_stranger_onboarding_reaches_no_gpu_plan() -> None`
- tests/e2e/test_production_stability.py -> `test_unconfigured_host_and_failures_stay_actionable() -> None`
- tests/e2e/test_production_stability.py -> `test_recipe_and_release_are_verifiable_without_gpu() -> None`

CONSUMES:
- WD-i8w6: README.md -> quickstart contract
  spec: the exact tested clone-to-plan path and clean-tree troubleshooting.
- WD-i8w6: VERSION -> semantic version `0.1.0`
  spec: user-facing version/release consistency.
- WD-k32a: wangp/cli.py -> `main(argv: Sequence[str] | None = None) -> int`
  spec: subprocess entrypoint for brief validate, plan, doctor, status, and review.
- WD-zkcu: wangp/config.py -> `load_host_config(*, repository_root: Path | None = None, environ: Mapping[str, str] | None = None) -> HostConfig`
  spec: proves empty configuration remains explicit and no-GPU-safe.
- WD-h5br: wangp/diagnostics.py -> `render_diagnostic(diagnostic: FailureDiagnostic) -> str`
  spec: verifies primary output is actionable and traceback-free.
- WD-u85z: wangp/recipe.py -> `verify_render_recipe(recipe_path: Path, *, repository_root: Path) -> RecipeVerification`
  spec: proves committed LF004 logical recipe verification without GPU/host work.

## Required Outcomes
1. From a clean temporary worktree, following the tested README setup and quickstart validates the committed brief and produces four planned clips with explicit `gpu_work: false` and `queue_submitted: false`.
2. The same user session runs local `wgp doctor`, `wgp status`, and `wgp review` against a real queue database copy and receives useful output while database evidence remains unchanged.
3. With host configuration absent, the no-GPU path still succeeds and a host-dependent dry-run operation fails before SSH with a message naming the exact missing configuration keys and next command.
4. At least one real invalid brief and one real queue/preflight failure render typed actionable diagnostics with evidence references and safe resume hints; no primary traceback is shown.
5. LF004 recipe verification and release verification both work from repository-owned committed evidence, report version `0.1.0`, and make no network/GPU/host call.
6. The end-to-end test asserts all relevant exit codes and leaves accepted artifacts byte-for-byte unchanged.

## Testing Requirements
- E2e tests ONLY. No unit tests, no integration tests, no mocks of any kind.
- Exercise the actual installed/subprocess CLI, real clean git worktree, real filesystem, real SQLite queue copy, real diagnostics, real recipe/release verification, and actual process exit codes.
- Commands: `uv run --frozen --extra dev pytest tests/e2e/test_production_stability.py` and `uv run --frozen --extra dev pytest -q`.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must paste full end-to-end and full-suite output into notes.
- Developer must include an AC verification table and artifact before/after hashes for read-only evidence.
- Developer must use `pvg story deliver`.
- No GPU, SSH, network, model inference, commit, tag, push, or publish is authorized.

## nd_contract
status: new

### evidence
- Created 2026-09-21 as the mandatory epic capstone blocked by all production-stability implementation stories.

### proof
- [ ] Pending implementation


## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-21T13:54:13Z dep_added: blocked_by WD-i8w6
- 2026-09-21T13:54:13Z dep_added: blocked_by WD-k32a
- 2026-09-21T13:54:13Z dep_added: blocked_by WD-zkcu

## Links
- Parent: [[WD-8zod]]
- Blocked by: [[WD-i8w6]], [[WD-k32a]], [[WD-zkcu]]

## Comments
