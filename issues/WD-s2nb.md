---
id: WD-s2nb
title: "Bug: CI workflow emits deprecated runtime warnings"
status: in_progress
priority: 0
type: bug
labels: [bug, ci, evidence, discovered-by-pm, delivered]
parent: WD-3nod
created_at: 2026-09-28T02:22:04Z
created_by: speed
updated_at: 2026-09-28T03:27:51Z
content_hash: "sha256:6378711f3474b7eda452c7b6a54bd08cfdc544ff95b3220bbbda9aa2818e5ed5"
blocks: [WD-fay0]
follows: [WD-qswf, WD-osfm, WD-28i5]
assignee: dev-WD-s2nb
---

## Description
## Context

## USER INTENT
CI must be clean and reproducible before an unavoidable runner migration, rather than relying on GitHub’s temporary Node 20 compatibility force-run or an `ubuntu-latest` label whose meaning changes on a future date.

## Observed defect
WD-qswf exact-head CI run `36350323341` and check run `108707648658` completed successfully but emitted these workflow-level defects:

```text
Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24:
actions/setup-python@v5, astral-sh/setup-uv@v6.
```

```text
The ubuntu-latest label will migrate to Ubuntu 26 beginning October 19, 2026.
```

The downloaded log also records Node deprecation diagnostics from the two setup actions:

- `[DEP0040] DeprecationWarning: The punycode module is deprecated.`
- `[DEP0169] DeprecationWarning: url.parse() behavior is not standardized and prone to errors.`

Current workflow state:

- `.github/workflows/ci.yml:18` uses `runs-on: ubuntu-latest`.
- `.github/workflows/ci.yml:22` uses `actions/setup-python@v5`.
- `.github/workflows/ci.yml:25` uses `astral-sh/setup-uv@v6`.
- `actions/checkout@v5` already declares `runs.using: node24` and is not named by the warning.

Verified replacement metadata:

- `actions/setup-python` tag `v7.0.0` declares `runs.using: 'node24'`.
- `astral-sh/setup-uv` tag `v10.2.0` declares `runs.using: "node24"`.

## Root Cause
The workflow uses mutable/current labels and two setup-action tags that still target Node 20 even though the runner forces them onto Node 24.

## Affected Components
- `.github/workflows/ci.yml`

## OUT OF SCOPE
- FastAPI/Starlette TestClient deprecation warning: owned separately by `WD-dc3w`; do not suppress or mix that dependency change here.
- Test logic, production code, build artifacts, release versioning, secrets, and new CI jobs.
- Replacing GitHub-hosted runners with a self-hosted GPU runner.

## DIFF BUDGET
- About 2 files and under 80 changed LOC: CI workflow plus evidence receipts.

## Boundary Map
PRODUCES:
- .github/workflows/ci.yml -> warning-clean CI runtime configuration
  spec: `runs-on: ubuntu-24.04`, `actions/setup-python@v7.0.0`, and `astral-sh/setup-uv@v10.2.0`.
- datasets/runs/ci-hygiene/node24-ci-runtime/ -> exact-head CI warning proof
  event: stores action metadata checks, workflow diff, check-run annotation JSON, downloaded log warning scan, run URL/conclusion, commit SHA, and PR identity.

CONSUMES:
- (existing): .github/workflows/ci.yml -> current test job steps `actions/setup-python@v5` and `astral-sh/setup-uv@v6`
  source: exact lines 22 and 25 at merged base `7275e44f56c0df99e74d2a8b762b162bde07f95b`.
- (existing): GitHub Actions metadata -> `runs.using` field in each referenced action’s `action.yml`
  source: `gh api repos/<owner>/<repo>/contents/action.yml?ref=<tag>` must resolve the declared runtime before the workflow is changed.

## Story Acceptance Criteria
1. [State] CI runs on explicit `ubuntu-24.04`, not the migrating `ubuntu-latest` label.
2. [State] CI pins `actions/setup-python@v7.0.0` and `astral-sh/setup-uv@v10.2.0`; `actions/checkout@v5` remains unchanged unless exact CI evidence proves it also emits a runtime warning.
3. [State] Before delivery, both replacement tags are verified against their upstream `action.yml` files as Node 24 actions.
4. [State] The exact PR-head CI run completes successfully.
5. [State] The exact-head check-run annotations contain no warning or notice for Node.js 20 forced compatibility, `ubuntu-latest` migration, punycode deprecation, or `url.parse()` deprecation; the downloaded run log contains none of those four deprecated-runtime strings.
6. [Unwanted] No test, Python dependency, production file, protected engine file, release version, secret, or unrelated workflow behavior changes.
7. [State] `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity from base `7275e44f56c0df99e74d2a8b762b162bde07f95b`, and `git diff --check` pass.

## Testing Requirements
- This is a real external integration: proof must come from an exact-head GitHub Actions run, not local YAML inspection alone.
- Parse/validate the final YAML locally.
- Verify both exact action tags and their `runs.using` metadata through the GitHub API.
- Download the exact-head run log and fetch check-run annotations; fail if either contains the deprecated-runtime strings.
- Exact-head CI must execute the existing undeselected test suite and build steps successfully.
- Coverage is not applicable to a YAML-only workflow change; the delivery must explicitly record that boundary instead of inventing a Python coverage number.
- Explicitly own any remaining FastAPI/Starlette warning as `WD-dc3w`; it must not be described as unrelated.

## Delivery Requirements
- Record before/after workflow lines, action metadata evidence, YAML validation, exact run and check-run IDs, annotation JSON, log warning counts, commit SHA, branch, and PR.
- Include `## Implementation Evidence`, `Summary:`, `Commands run:`, `SHA:`, `### CI/Test Results`, `### AC Verification`, and `LEARNINGS:`.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Created from WD-qswf PM discovery, CI run `36350323341`, check run `108707648658`, and live GitHub release/action metadata at merged base `7275e44f56c0df99e74d2a8b762b162bde07f95b`.

### proof
- [ ] Pending explicit runner/action pinning, metadata verification, exact-head CI run, annotation/log scans, and standard delivery gates.

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-27.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

Summary: CI now declares an explicit `ubuntu-24.04` runner and uses the exact Node 24 action tags `actions/setup-python@v7.0.0` and `astral-sh/setup-uv@v10.2.0`. `actions/checkout@v5` is unchanged. The only functional file changed is `.github/workflows/ci.yml`; all other changed files are evidence receipts under `datasets/runs/ci-hygiene/node24-ci-runtime/`.

### Workflow change
- Before at base `7275e44f56c0df99e74d2a8b762b162bde07f95b`: line 18 `runs-on: ubuntu-latest`, line 22 `actions/setup-python@v5`, line 25 `astral-sh/setup-uv@v6`.
- After: line 18 `runs-on: ubuntu-24.04`, line 22 `actions/setup-python@v7.0.0`, line 25 `astral-sh/setup-uv@v10.2.0`.

### Upstream action metadata (GitHub API)
- `actions/setup-python` tag `v7.0.0`, tag commit `5fda3b95a4ea91299a34e894583c3862153e4b97`: `action.yml` line 42 declares `runs.using: 'node24'`.
- `astral-sh/setup-uv` tag `v10.2.0`, tag commit `c18668ad3cf93ea998bef934396af7bb5c839dc7`: `action.yml` line 115 declares `runs.using: "node24"`.
- Raw API action files, tag refs, SHA-256 values, and normalized metadata are stored in `datasets/runs/ci-hygiene/node24-ci-runtime/upstream-actions/` and `upstream-action-metadata.json`.

### CI/Test Results
- Commands run:
  - `pvg issues show WD-s2nb --json`
  - `gh api -H 'Accept: application/vnd.github.raw' 'repos/actions/setup-python/contents/action.yml?ref=v7.0.0'`
  - `gh api -H 'Accept: application/vnd.github.raw' 'repos/astral-sh/setup-uv/contents/action.yml?ref=v10.2.0'`
  - `python3` YAML parse plus explicit workflow-value assertions
  - `gh pr create ...` and `gh run watch ... --exit-status`
  - `gh run view ... --job ... --log`
  - `gh api 'repos/jmanhype/wangp-dspy/check-runs/<id>/annotations'`
  - `pvg lint --backlog`
  - `uv run --frozen --extra dev wgp release verify`
  - `git diff --exit-code 7275e44f56c0df99e74d2a8b762b162bde07f95b -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
  - `git diff --check`
  - `pvg verify <all changed paths> --format=text`
  - `git push origin story/WD-s2nb`
- Exact workflow-changing PR-head run: `36370137115`, check/job `108764537585`, head `b978e818d3f8a3778f3ee74c005e3edc1739893e`, conclusion `success`. Its byte-exact downloaded log is committed gzip-preserving as `exact-head-job.log.gz`; decompressed SHA-256 is `0e3a9e35987627a7e40b59c1d2bbd96e37d342e6f03df1ba85d28d9e9c45debd`.
- Current final PR-head revalidation: run `36371988124`, check/job `108770076101`, head `103aee498639c590fd4dd888b160c90992ce15eb`, event `pull_request`, conclusion `success`, duration `23m8s`: https://github.com/jmanhype/wangp-dspy/actions/runs/36371988124
- Current-head outcomes derived from the complete pytest progress report: 2,107 passed, 1 existing skipped, 0 failed, 0 errors; existing build step passed for one sdist and one wheel.
- Exact warning/notice counts on current head `103aee498639c590fd4dd888b160c90992ce15eb`:
  - Downloaded log: Node.js 20 forced compatibility = 0; `ubuntu-latest` migration = 0; punycode deprecation = 0; `url.parse()` deprecation = 0.
  - Check-run annotations: total = 0; each of the four deprecated-runtime strings = 0; warning annotations = 0; notice annotations = 0.
  - GitHub workflow command markers: `##[warning]` = 0 and `##[notice]` = 0.
  - Remaining pytest warning count = 1: `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` This is explicitly owned by `WD-dc3w` and was not changed or suppressed here.
- Coverage: N/A. This is a CI YAML/runtime-pin change with no Python implementation change; no Python coverage number is invented.
- Local YAML parse: PASS (1 job; `ubuntu-24.04`; setup-python `v7.0.0`; setup-uv `v10.2.0`).
- `pvg lint --backlog`: PASS, 147 issues scanned, 0 errors, 0 review findings.
- `wgp release verify`: PASS with `release=ready` and `tag_created=false`.
- Protected-file parity from `7275e44f56c0df99e74d2a8b762b162bde07f95b`: PASS, exit 0, no protected-file diff.
- `git diff --check`: PASS, exit 0.
- `pvg verify <all changed paths> --format=text`: PASS, 0 issues.

### Commit
- Branch: `story/WD-s2nb`
- SHA: `103aee498639c590fd4dd888b160c90992ce15eb`
- Workflow implementation commit: `b25a84c7` (`ci(WD-s2nb): pin Node 24 runtime`)
- PR: https://github.com/jmanhype/wangp-dspy/pull/211
- Push: branch pushed to `origin/story/WD-s2nb`; PR remains open and is not merged.

### AC Verification
| AC # | Requirement | Evidence | Status |
|---|---|---|---|
| 1 | Explicit `ubuntu-24.04` runner | `.github/workflows/ci.yml:18`; YAML parse receipt | PASS |
| 2 | Exact setup tags; checkout unchanged | `.github/workflows/ci.yml:21-25`; diff has only the three requested runtime lines | PASS |
| 3 | Upstream tags verified as Node 24 | GitHub API raw `action.yml` receipts and `upstream-action-metadata.json` | PASS |
| 4 | Exact PR-head CI success | Final PR head `103aee49...`, run `36371988124`, check `108770076101`, conclusion success | PASS |
| 5 | No four deprecated-runtime warnings/notices | Final downloaded log and annotation scan all count 0 | PASS |
| 6 | No out-of-scope file change | Base-to-head names are only `.github/workflows/ci.yml` and CI evidence receipts; protected parity exit 0 | PASS |
| 7 | Standard gates pass | `pvg lint --backlog`, release verify `release=ready`/`tag_created=false`, protected parity, and `git diff --check` all exit 0 | PASS |

LEARNINGS:
- Fetching and parsing each exact tag's upstream `action.yml` before editing kept the runtime claim tied to primary metadata rather than release notes.
- GitHub job logs can contain harmless trailing spaces; gzip-preserving the downloaded bytes keeps the evidence byte-identical while allowing `git diff --check` to remain clean.
- Committing CI evidence naturally advances the PR head, so the current head was rerun and independently scanned rather than presenting the earlier successful workflow-changing head as the final-head result.
- The only remaining warning is the known Starlette/httpx TestClient deprecation, and the evidence names `WD-dc3w` as owner without mixing dependency changes into this story.

## nd_contract
status: delivered

### evidence
- Functional diff, upstream API metadata, YAML validation, exact-head run/check IDs, annotations, downloaded-log scan, test/build counts, SHA, branch, and PR are recorded above and under `datasets/runs/ci-hygiene/node24-ci-runtime/`.

### proof
- [x] AC #1: CI declares `ubuntu-24.04`.
- [x] AC #2: CI pins setup-python `v7.0.0` and setup-uv `v10.2.0`; checkout `v5` remains unchanged.
- [x] AC #3: Both exact upstream tags declare `runs.using: node24`.
- [x] AC #4: Exact final PR-head run `36371988124` succeeded.
- [x] AC #5: Log and annotations each contain zero occurrences of all four deprecated-runtime defects.
- [x] AC #6: Only the requested workflow change plus evidence receipts are present; protected files and other behavior are unchanged.
- [x] AC #7: Lint, release verification, protected parity, `git diff --check`, and `pvg verify` pass.

## History
- 2026-09-28T02:22:04Z dep_added: blocks WD-fay0
- 2026-09-28T02:22:34Z status: open -> in_progress
- 2026-09-28T02:22:34Z auto-follows: linked to predecessor WD-osfm
- 2026-09-28T02:22:34Z claimed by dev-WD-s2nb
- 2026-09-28T03:27:51Z status: in_progress -> in_progress
- 2026-09-28T03:27:51Z auto-follows: linked to predecessor WD-28i5

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-qswf]], [[WD-osfm]], [[WD-28i5]]

## Comments
