---
id: WD-s2nb
title: "Bug: CI workflow emits deprecated runtime warnings"
status: open
priority: 0
type: bug
labels: [bug, ci, evidence, discovered-by-pm]
parent: WD-3nod
created_at: 2026-09-28T02:22:04Z
created_by: speed
updated_at: 2026-09-28T02:22:04Z
content_hash: "sha256:d90511c474940d23c91d2624e77cb38ad6b112ec8034a7fbd7c0f993355df27b"
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


## History


## Links
- Parent: [[WD-3nod]]

## Comments
