---
id: WD-9rjd
title: "Verify release readiness from committed repository evidence"
status: closed
priority: 2
type: feature
labels: [release, external-integration, accepted]
parent: WD-t534
created_at: 2026-09-21T23:25:38Z
created_by: speed
updated_at: 2026-09-22T00:22:29Z
content_hash: "sha256:b26011b69e9c609cf26f5c0352e1d63a6bf1aff6d08c05764c13ab0b8407a131"
assignee: dev-WD-9rjd
follows: [WD-carq, WD-lvix]
closed_at: 2026-09-22T00:01:57Z
close_reason: "HEAD 8863df8; clean recipe diff; release verify and 4 negative probes passed; tests and GitHub check green; tree/tags unchanged"
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
## Rework Verification
Verdict: HOLDS — all three review findings are fixed at the rework head.
SHA: 1fd1a99f96baee53cd45833dcd613e4f8b6134b7

Commands:
- git rev-parse HEAD; git diff main..HEAD --name-only; git diff main..HEAD -- wangp/recipe.py
- Temporary-worktree probes: chmod 000 assembled.mp4; corrupt final-provenance.json; sensitive VERSION value; run human and JSON release verification.
- Code inspection: wangp/release.py, wangp/cli.py, tests/test_release.py.
- Clean worktree: wgp release verify and wgp release verify --json; git tag.
- uv run --frozen --extra dev pytest tests/test_release.py -q; uv run --frozen --extra dev pytest -q
- Temporary pre-fix worktree at 8863df8 with the new tests committed.
- gh api .../commits/1fd1a99.../check-runs; gh pr checks 156; git status --porcelain | wc -l

Observed:
- HEAD and changed-file set match exactly; wangp/recipe.py has no main..HEAD diff.
- Unreadable artifact exits 2, names assembled.mp4, reports recipe_schema failed, release=not_ready, no traceback.
- Malformed provenance exits 2 in both modes; human retains the failed check and release=not_ready; JSON retains release with ready=false and tag_created=false.
- Sensitive VERSION appears nowhere in outputs; both modes show <redacted-key>. Basis: release.py catches OSError/UnicodeError; CLI redacts failed and successful mappings/check values.
- Clean human/JSON exit 0 at 0.1.0 with tag_created=false; tag count/refs unchanged.
- Targeted: 5 passed. Full: 1657 collected, 1656 passed, 1 skipped. The three new subprocess regressions each fail against 8863df8.
- Exact-head CI test completed/success (106567311585); gh pr checks 156 passed.
- Final worktree status count: 0.

## Rework Evidence

- Finding 1 (unreadable artifact): `_recipe_check` now catches `RecipeError`, `OSError`, and `UnicodeError`, names the unreadable artifact, and raises a field-specific `recipe_schema` `ReleaseError` with exit 2. Real-process coverage chmods a copied required `assembled.mp4` to `000`, asserts the typed artifact diagnostic/no traceback, restores permissions, and proves byte/status identity.
- Finding 2 (missing/malformed evidence verdict): recipe-evidence failures now carry a `ReleaseVerification` with version, failed `recipe_schema`, `v0.1.0` guidance, `ready=false`, and `tag_created=false`. Real human and JSON subprocess runs on malformed copied provenance both show the failed check and `release=not_ready`/JSON release object while exiting 2.
- Finding 3 (redaction): CLI human check lines and JSON release payloads explicitly pass expected/observed values through `redact_sensitive`. Real copied-checkout tests inject a credential-shaped version value and require `<redacted-key>` in both output modes with no verbatim secret.
- Verification at head `1fd1a99f96baee53cd45833dcd613e4f8b6134b7`: targeted release suite 5 passed / 0 failed; full suite 1,656 passed / 1 skipped / 0 failed (known Starlette/httpx warning only); clean human and JSON commands exited 0 with version `0.1.0`, tag-ready `v0.1.0`, `tag_created=false`, and `git status --porcelain` line count 0.
- PR #156 exact-head check `106567311585` (`test`, run `35671036987`) completed with conclusion **success**. Story status and labels were not changed.

## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-21.

### proof
- [x] Story closed after accepted label was applied.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-21.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Summary: Added a read-only release boundary map: `verify_release(repository_root)` compares root/package/CLI versions, requires the exact changelog entry, builds the committed LF004 recipe in memory against `wangp-dspy.render-recipe/v3`, and reuses fail-closed repository identity. `wgp release verify [--json]` follows the established 0/2/4 CLI contract and reports tag-ready `v0.1.0` without creating a Git object, distribution, tag, or release. README links the appended release checklist.

Commands run:
- `pvg verify wangp/release.py wangp/cli.py docs/recipe.md README.md tests/test_release.py --format=text` -> `VERIFY: PASSED (3 files scanned, 0 issues)`.
- `uv run --frozen --extra dev pytest tests/test_release.py -q` -> exit 0, `.. [100%]`, 2 passed.
- `uv run --frozen --extra dev pytest -q` -> exit 0; 1,654 tests collected, 1,653 passed, 1 skipped, 0 failed, 0 errors. Output retained the known pre-existing `StarletteDeprecationWarning` from `fastapi/testclient.py:1` (`httpx2` recommendation); no new warning or failure was introduced.
- `uv build --out-dir /tmp/wd-9rjd-build.c7H7dM` -> exit 0, built `wangp_dspy-0.1.0.tar.gz` and `wangp_dspy-0.1.0-py3-none-any.whl`.
- `uv run --frozen --extra dev wgp release verify` -> exit 0 and the human transcript below.
- `uv run --frozen --extra dev wgp release verify --json` -> exit 0 and the stable JSON transcript below.
- `gh api repos/jmanhype/wangp-dspy/commits/8863df869ffbfcdf4e1a4e00b27caeac888b8920/check-runs` -> exact-head `test` check 106562126535 completed/success.
- `git push origin story/WD-9rjd` -> pushed only story/WD-9rjd; PR #156 opened for CI (`https://github.com/jmanhype/wangp-dspy/pull/156`).
- Read-only snapshot of all tracked release inputs before/after both real-repository CLI modes -> identical SHA-256 `4dd745a9bcbd26ed246bedbe2a938c3db35260b59c5ef340a276a2419dfa1fce`; `git status --porcelain` count remained 0.

SHA: 8863df869ffbfcdf4e1a4e00b27caeac888b8920

### CI/Test Results

- Targeted: `2 passed` / 0 failed / 0 errors / 0 skipped, exit 0.
- Full: `1653 passed, 1 skipped, 0 failed, 0 errors`, exit 0. The only skip is the existing optional host/GPU-gated test; the only warning is the known Starlette/httpx deprecation cited above.
- Build artifacts:
  - `wangp_dspy-0.1.0.tar.gz` SHA-256 `fd34d0537bb12b43cae3c6ae869157078836e99bf9fe919e8bae455537e62f57`.
  - `wangp_dspy-0.1.0-py3-none-any.whl` SHA-256 `423095acb25a4e33061e2464979566ad4d8f8331b94ab9f7a5f1c69fe09ee7fd`.
- Exact-head CI: check-run id `106562126535`, name `test`, status `completed`, conclusion `success`, at SHA `8863df869ffbfcdf4e1a4e00b27caeac888b8920` (run `35669361289`).
- Human CLI transcript: `version=0.1.0`; all four checks pass; `tag-ready=v0.1.0`; `tag_created=false`; `v0.1.0 is tag-ready; no tag was created`; `release=ready`; exit 0.
- Stable JSON transcript (complete): `{"release":{"checks":[{"expected":"0.1.0","message":null,"name":"version","observed":{"VERSION":"0.1.0","pyproject.toml":"0.1.0","wangp.__version__":"0.1.0"},"source":"VERSION, pyproject.toml, wangp/__init__.py","status":"pass"},{"expected":"0.1.0","message":null,"name":"changelog","observed":"0.1.0","source":"CHANGELOG.md","status":"pass"},{"expected":"wangp-dspy.render-recipe/v3","message":null,"name":"recipe_schema","observed":"wangp-dspy.render-recipe/v3","source":"wangp/recipe.py, datasets/runs/pull/lf004-operator-dogfood-56f-recovery-20260921","status":"pass"},{"expected":"clean_tree=true changed_path_count=0 untracked_path_count=0","message":null,"name":"tree","observed":{"changed_path_count":0,"clean_tree":true,"commit_sha":"8863df869ffbfcdf4e1a4e00b27caeac888b8920","dirty_tree":false,"status_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","tracked_diff_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","untracked_content_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","untracked_path_count":0},"source":"services.director.run_ledger.repository_identity","status":"pass"}],"guidance":"v0.1.0 is tag-ready; no tag was created","ready":true,"tag":"v0.1.0","tag_created":false,"version":"0.1.0"}}`.
- No network/SSH and read-only integration proof: every real-process test runs under a Python audit hook rejecting `socket.connect`, `socket.getaddrinfo`, and `urllib.Request`, puts a logging fake `ssh` first on PATH, removes all `WANGP_*` host variables, and asserts the SSH log is never created. Each success/failure case compares pre/post hashes and Git status. The deliberate mismatch mutations and commits exist only in a temporary shared-object clone; the real repository remained clean and byte-identical.

### AC Verification

| AC | Result | Evidence |
| --- | --- | --- |
| 1 | PASS | `wangp/release.py:139-159` is local/read-only and reports version `0.1.0`; `tests/test_release.py:90-116` proves clean clone and real-repository success plus no network/SSH/read-only behavior. |
| 2 | PASS | `wangp/release.py:65-88` compares `VERSION`, pyproject metadata, and `wangp.__version__` with expected/observed values; `tests/test_release.py:123-148` proves a typed version mismatch. |
| 3 | PASS | `wangp/release.py:91-102` requires the exact root heading; `tests/test_release.py:126-148` proves the missing current-entry class. |
| 4 | PASS | `wangp/release.py:105-119` builds committed LF004 evidence in memory and checks v3 without writing a recipe; `tests/test_release.py:128-148` proves v4 is rejected. |
| 5 | PASS | `wangp/release.py:122-155` consumes `repository_identity`, reports all tree counts, and preserves `RepositoryIdentityError` as a failed tree verdict; dirty/untracked integration is at `tests/test_release.py:150-158`. |
| 6 | PASS | Human and stable JSON output at `wangp/cli.py:323-354` names `v0.1.0`, `tag_created=false`, and no-tag guidance; exact transcripts are recorded above. |
| 7 | PASS | `wangp/cli.py:323-343` maps `ReleaseError` to diagnostic output and exit 2 without traceback; parser wiring is at `wangp/cli.py:427-433`; unexpected failures retain the existing exit-4 path. |
| 8 | PASS | `tests/test_release.py:119-158` is real subprocess integration with no mocks and covers clean human/JSON plus version, changelog, recipe-schema, and dirty-tree failures. |
| 9 | PASS | `README.md:136-149` links the command and boundaries to `docs/recipe.md:88-110`, including exit codes and clean-tree troubleshooting. |
| 10 | PASS | Targeted suite 2 passed, full suite 1653 passed/1 skipped, build succeeded, and exact-head CI succeeded. `git diff main..HEAD --name-only` contains only README.md, docs/recipe.md, wangp/cli.py, wangp/release.py, and tests/test_release.py; no renderer, queue, provenance, retry, QC, diagnostic, or recipe semantics file changed. |
| 11 | PASS | The actual human and JSON commands were run in the clean real repository with the complete transcripts above; repository hashes were unchanged and the audit/fake-ssh test proves no remote endpoint was contacted. Reviewer confirmation can reproduce the same local commands. |

## nd_contract
status: delivered

### evidence
- Head `8863df869ffbfcdf4e1a4e00b27caeac888b8920` on `story/WD-9rjd`; pushed only to that branch; PR #156.
- Targeted release suite: 2 passed / 0 failed. Full suite: 1653 passed / 1 skipped / 0 failed. Build: wheel and sdist succeeded. Exact-head CI check `106562126535`: completed/success.
- Read-only input digest before and after both real CLI modes: `4dd745a9bcbd26ed246bedbe2a938c3db35260b59c5ef340a276a2419dfa1fce`. Network audit hook and fake SSH recorded no call. No tag, Git release object, distribution publication, main push, GPU, model inference, SSH, or render-host work occurred.

### proof
- [x] AC #1: Local read-only command reports `0.1.0`, performs no network/SSH/GPU call, and writes no repository artifact.
- [x] AC #2: All three version sources are compared with field-specific expected/observed diagnostics.
- [x] AC #3: The exact current-version root changelog entry is required.
- [x] AC #4: Committed LF004 evidence proves v3 recipe compatibility without a recipe output; unsupported schema fails.
- [x] AC #5: Existing repository-identity discipline is consumed; dirty/untracked state and fail-closed identity errors remain typed tree failures.
- [x] AC #6: Human and deterministic JSON outputs prove every check, value, verdict, tag guidance, and `tag_created:false`.
- [x] AC #7: Typed verification failures exit 2 without traceback; unexpected internals retain exit 4.
- [x] AC #8: Real-process tests cover clean success and all four required mismatch classes with no mocks.
- [x] AC #9: README links the documented release checklist, no-tag boundary, and clean-tree troubleshooting.
- [x] AC #10: Targeted suite, full suite, build, and exact-head CI are green; protected semantic files are unchanged.
- [x] AC #11: Actual clean-checkout human/JSON commands, byte-identity evidence, and no-network/no-SSH evidence are recorded for reviewer reproduction.

## History
- 2026-09-21T23:25:44Z dep_added: blocks WD-fq1o
- 2026-09-21T23:28:18Z status: open -> in_progress
- 2026-09-21T23:28:18Z auto-follows: linked to predecessor WD-carq
- 2026-09-21T23:28:18Z claimed by dev-WD-9rjd
- 2026-09-21T23:54:18Z status: in_progress -> in_progress
- 2026-09-21T23:54:18Z auto-follows: linked to predecessor WD-lvix
- 2026-09-22T00:01:57Z status: in_progress -> closed
- 2026-09-22T00:01:57Z dep_removed: no_longer_blocks WD-fq1o

## Links
- Parent: [[WD-t534]]
- Follows: [[WD-carq]], [[WD-lvix]]

## Comments
