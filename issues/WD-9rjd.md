---
id: WD-9rjd
title: "Verify release readiness from committed repository evidence"
status: in_progress
priority: 2
type: feature
labels: [release, external-integration]
parent: WD-t534
created_at: 2026-09-21T23:25:38Z
created_by: speed
updated_at: 2026-09-21T23:28:18Z
content_hash: "sha256:5128201c5943fd0858534e68bdba493e36ba41fd16270c4ad7fcc686ed83fe74"
blocks: [WD-fq1o]
assignee: dev-WD-9rjd
follows: [WD-carq]
---

## Description
## USER INTENT
Observable outcome: an operator can run one local, read-only `wgp` command in a clean checkout and learn whether repository versioning, the root changelog, the accepted recipe contract, and clean-tree discipline all agree -- and, when they do, see the exact tag-ready `v<VERSION>` name without the tool performing a release.

## Context (Embedded)
- Baseline is main `9eba0e7`. WD-carq delivered and merged `wangp/recipe.py`, `wgp recipe write|verify`, `docs/recipe.md`, and `tests/test_recipe.py`, but `wangp/release.py` is absent and `wgp --help` lists only `doctor`, `brief`, `plan`, `status`, `review`, and `recipe`.
- Repository hygiene already exists from WD-3nwm: root `VERSION` is `0.1.0`, `pyproject.toml` declares project version `0.1.0`, `CHANGELOG.md` has a root `## [0.1.0]` entry, and `README.md`, `CONTRIBUTING.md`, `LICENSE`, and `THIRD_PARTY_NOTICES.md` are present.
- The accepted recipe contract is `wangp.recipe.RECIPE_SCHEMA == "wangp-dspy.render-recipe/v3"`. The real read-only builder is `wangp.recipe.build_recipe(run: str | Path, repository_root: str | Path, *, context_configuration: Mapping[str, Any] | None = None, environ: Mapping[str, str] | None = None) -> dict[str, Any]`; it can exercise the committed LF004 review evidence without writing a recipe file.
- Clean-tree discipline must reuse `services.director.run_ledger.repository_identity(repo_root: Optional[os.PathLike[str] | str] = None) -> dict`, whose result includes `clean_tree`, `dirty_tree`, `changed_path_count`, and `untracked_path_count`. Its fail-closed treatment of unsafe untracked content must not be weakened.
- External-integration boundary: all evidence is repository-owned and local. No secret, API key, client ID, remote endpoint, package index, or paid service is required; blocked-by config sub-task: none.
- The verifier is advisory release readiness. It must not create a Git object or distribution, and it must not claim that a tag was created, pushed, verified remotely, or published.

## OUT OF SCOPE
- Creating a tag or release branch, committing, pushing, building/publishing a distribution, or using PyPI credentials: this story only decides whether the exact checkout is ready; any release action requires separate operator authorization.
- Network access, GPU work, SSH/host contact, model inference, or model download: release readiness is deliberately local and offline; lands never in this story.
- Changing renderer, queue, provenance, retry, QC, diagnostic, or recipe-drift semantics: this story consumes accepted contracts; such changes require separate authorization.
- Modifying accepted LF004 evidence or historical run artifacts: verification is read-only; no follow-up may rewrite evidence.
- Bumping the version or authoring new release notes: the current `0.1.0` repository contract is the input, not a deliverable; a future release-preparation story owns intentional changes.

## DIFF BUDGET
- Roughly 5 files, under 400 authored changed LOC.

## Boundary Map
PRODUCES:
- wangp/release.py -> `ReleaseError(ValueError): field-specific typed release verification failure`
- wangp/release.py -> `verify_release(repository_root: Path) -> ReleaseVerification`
- wangp/cli.py -> stable `wgp release verify [--json]` wiring with human and deterministic JSON output
- docs/recipe.md -> appended release-checklist section covering each check, output, exit codes, and no-tag boundary
- README.md -> release-verification command and link to the release checklist
- tests/test_release.py -> real-process success and typed-failure coverage for `wgp release verify`

CONSUMES:
- WD-3nwm: VERSION -> semantic version `0.1.0`
  spec: root source compared with package metadata; disagreement is a typed `version` failure.
- WD-3nwm: pyproject.toml -> `[project] version = "0.1.0"`
  spec: package metadata compared with root `VERSION` and the CLI package version.
- WD-3nwm: CHANGELOG.md -> root release entry `## [0.1.0]`
  spec: release verification requires an entry for the current version.
- WD-lhm4: wangp/cli.py -> `main(argv: Sequence[str] | None = None) -> int`
  spec: the new verb follows the established 0/2/4 exit-code and stable-JSON contracts.
- WD-carq: wangp/recipe.py -> `RECIPE_SCHEMA: str` and `build_recipe(run: str | Path, repository_root: str | Path, *, context_configuration: Mapping[str, Any] | None = None, environ: Mapping[str, str] | None = None) -> dict[str, Any]`
  spec: release compatibility recognizes the accepted `wangp-dspy.render-recipe/v3` contract from committed LF004 evidence without writing a recipe.
- (existing): services/director/run_ledger.py -> `repository_identity(repo_root: Optional[os.PathLike[str] | str] = None) -> dict`
  spec: returns `clean_tree`, `dirty_tree`, `changed_path_count`, and `untracked_path_count`; unsafe untracked content remains fail-closed typed input.

## Required Outcomes
1. `wgp release verify [--json]` runs entirely against the supplied repository checkout, performs no network/GPU/host call, writes no repository artifact, and reports the current version as `0.1.0`.
2. Version readiness compares root `VERSION`, `pyproject.toml` package metadata, and the packaged CLI version; every disagreement is reported under a field-specific `version` check with expected and observed values.
3. Changelog readiness requires a root `CHANGELOG.md` entry for exactly the current version and reports a field-specific `changelog` failure when that entry is absent.
4. Recipe readiness proves compatibility with the accepted `wangp-dspy.render-recipe/v3` contract using repository-owned committed LF004 evidence, without creating a recipe output, and reports unsupported or unknown schema state under `recipe_schema`.
5. Tree readiness consumes the existing repository-identity discipline and reports a field-specific `tree` failure for any dirty or untracked state; it must not ignore opaque untracked directories or suppress `RepositoryIdentityError`.
6. On a clean, agreeing checkout, human output names the exact tag-ready guidance `v0.1.0` and states that no tag was created; `--json` emits deterministic, secret-free fields sufficient to prove every check, value, failure, and final verdict.
7. Typed verification failures exit `2` and identify the failing check/source rather than printing a traceback; only unexpected internal failures exit `4`, matching doctor/recipe CLI behavior.
8. Real-process tests reproduce clean success and the four required failure classes: version mismatch, missing current-version changelog entry, unsupported recipe schema, and dirty tree.
9. README links the verified command to the appended `docs/recipe.md` release checklist, including the no-tag/no-publish boundary and clean-tree troubleshooting.
10. Targeted release tests, the full suite, and the required CI check are green at the exact delivery head; renderer, queue, provenance, and QC semantics remain unchanged.

11. Manual verification/smoke test: the reviewer runs the actual `wgp release verify` and `wgp release verify --json` commands in a clean checkout, inspects the release checklist/linkage, and confirms that no remote endpoint is contacted; this local repository-owned verification is the real integration boundary.
## Testing Requirements
- Unit: none authorized; release verification must be exercised as real integration, not through mocks or in-process monkeypatching.
- Integration: MANDATORY (no mocks). Invoke the installed `wgp` entry point with `subprocess` in a clean temporary Git worktree at the delivery head and assert successful human and JSON output, version `0.1.0`, tag guidance `v0.1.0`, and exit code 0.
- Mismatch integration: MANDATORY (no mocks). In a deliberate temporary copy, change only root `VERSION` to a different value while package metadata remains `0.1.0`; assert exit 2 and a field-specific version expected/observed diagnostic.
- Failure matrix integration: MANDATORY (no mocks). Using isolated temporary copies/worktrees, reproduce missing current-version changelog entry, unsupported recipe schema, and dirty/untracked tree; each must exit 2 with its named check and no primary traceback.
- Read-only integration: MANDATORY (no mocks). Hash or otherwise record the checked repository-owned inputs before and after success and every failure and prove their bytes/listings are unchanged; all derived state must remain outside the repository in temporary storage.
- Commands: `uv run --frozen --extra dev pytest tests/test_release.py` and `uv run --frozen --extra dev pytest -q`.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must paste complete targeted-suite, full-suite, CLI transcript, and exact-head CI output into story notes.
- Developer must include an AC verification table mapping every required outcome to code, test, command output, and read-only evidence.
- Developer must record before/after hashes or equivalent byte-identity evidence for all repository-owned release inputs.
- Developer must use `pvg story deliver`.
- No GPU, SSH, network, model inference/download, commit, tag, push, publish, or PyPI credential use is authorized.

## nd_contract
status: new

### evidence
- Created 2026-09-21 from main 9eba0e7: recipe verification is accepted, `wangp/release.py` is absent, `wgp --help` has no release verb, and the root version/changelog/package surfaces all report 0.1.0.

### proof
- [ ] Pending implementation
## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-21T23:25:44Z dep_added: blocks WD-fq1o
- 2026-09-21T23:28:18Z status: open -> in_progress
- 2026-09-21T23:28:18Z auto-follows: linked to predecessor WD-carq
- 2026-09-21T23:28:18Z claimed by dev-WD-9rjd

## Links
- Parent: [[WD-t534]]
- Blocks: [[WD-fq1o]]
- Follows: [[WD-carq]]

## Comments
