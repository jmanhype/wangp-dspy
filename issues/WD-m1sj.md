---
id: WD-m1sj
title: "uv build cannot produce a wheel: duplicate qc/audio_critic package declaration"
status: in_progress
priority: 1
type: task
parent: WD-t534
created_at: 2026-09-21T15:24:25Z
created_by: speed
updated_at: 2026-09-21T17:46:12Z
content_hash: "sha256:0b6bd43c35795261bc6b0037dce6e616e2dfb975ad67247c853a765c95e8c8d3"
follows: [WD-lhm4, WD-3nwm]
labels: [delivered]
---

## Description
## Symptom
`uv build` cannot produce a wheel, so the repository has no distributable artifact even though `uv build --sdist` succeeds.

## Measured evidence
- `uv build --sdist` exits 0 and produces `wangp_dspy-0.1.0.tar.gz` (sha256 `d3a7d0e3f0a727bc4861221e7b2534b7fae41b64e71f6562f641368aaeb0cac4` at head 58ff84d + exclusion fix).
- Wheel building fails: `pyproject.toml` `[tool.hatch.build.targets.wheel].packages` lists both `qc` and `qc/audio_critic`, so `qc/audio_critic/__init__.py` is added twice.

## Impact
Blocks any packaging or installation path that requires a wheel: PyPI/GitHub release artifacts, Pinokio-style installers, and pip installs from a built distribution. This is a prerequisite for the "turn the repo into the product" epic, since a product a stranger cannot install is not a product.

## Scope
Resolve the duplicate package declaration so both `uv build --sdist` and `uv build --wheel` succeed, and add a CI check that builds both artifacts. Do not change any runtime or gate semantics.

## Out of scope
- Publishing to any index.
- Installer/Pinokio parity work (separate story).
- Licences of third-party fixtures (already handled in WD-3nwm).

## nd_contract
status: new

### evidence
- Discovered during independent acceptance of WD-3nwm, which built an sdist to test a third-party notice claim.

### proof
- [ ] Pending: wheel builds successfully and CI verifies both artifacts.

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence

Summary: `uv build` now produces both a wheel and an sdist, and the installed `wgp` entry point runs outside the source checkout. The duplicate/nested package declarations were removed and the shipped package list corrected (it must include `wangp` and `scripts`), fixing the packaging defect and the installed-CLI startup failure together.

Commands run:
- `uv build` at head `faeac0c9092952f78e5c5944f0dabf4e805b4db2` -> exit 0, exactly one wheel and one sdist.
- `uv venv <tmp>/venv` and `uv pip install --python <tmp>/venv/bin/python <wheel>` -> exit 0.
- `cd /tmp && <tmp>/venv/bin/wgp doctor` with `PYTHONPATH` and `WANGP_SSH_TARGET` unset -> exit 0, `ready=yes`, imports resolved from the venv site-packages.
- `git diff --exit-code main -- services/ qc/ host/ predict/` -> exit 0.

Commit: 5dadcdafc680ee41999079e55bd085dd2e73439c

## CI/Test Results

- Run 35631378806 at story head `faeac0c9092952f78e5c5944f0dabf4e805b4db2`: `test` completed, conclusion **success**.
- Run 35633778277 at main `5dadcdafc680ee41999079e55bd085dd2e73439c` after squash merge: completed, conclusion **success**.
- CI now builds both artifacts and asserts exactly one wheel and one sdist (`.github/workflows/ci.yml`).
- Wheel sha256 `ac8dcb9903b824a4be9fcb6850fbb31ee4ba4b81798fb53efc1839f04b91cc0c`; sdist sha256 `d7ccbe167290ff74f27d261ad1c216ff1396ba3bc7df601d7e13072295d1e497`.
- Independent PM acceptance of WD-lhm4 reproduced the wheel build and the installed `wgp doctor` run in a throwaway venv and marked the installed-command finding FIXED.

### Acceptance criteria

- [x] AC1: `uv build` produces a wheel without the duplicate-package failure (exit 0, wheel hash recorded above).
- [x] AC2: `uv build` produces an sdist (exit 0, sdist hash recorded above).
- [x] AC3: CI verifies both artifacts (runs 35631378806 and 35633778277 both success; workflow asserts one wheel and one sdist).
- [x] AC4: the installed package is usable, not just the source tree (wheel installed in a venv outside the repo; `wgp doctor` exit 0 from a foreign cwd).
- [x] AC5: no engine or gate semantics changed (`git diff --exit-code main -- services/ qc/ host/ predict/` exit 0).

Disclosed, NOT part of this bug: a wheel-installed `wgp plan` still requires a git checkout for repository identity (exit 4 from a non-repo cwd), recorded as a discovered defect in WD-lhm4.

## nd_contract
status: delivered

### evidence
- Build, install, and CI evidence above; three independent parties (developer, dispatcher, PM acceptor) reproduced the wheel build.

### proof
- [x] Wheel builds successfully and CI verifies both artifacts.

## Implementation Evidence

Summary: The `uv build` wheel failure is fixed. The duplicate/nested package declarations were removed from `[tool.hatch.build.targets.wheel].packages`, and the wheel now ships the packages the CLI needs (`wangp`, `scripts`), so both a wheel and an sdist build and the installed `wgp` entry point runs outside the source checkout. Fix landed via WD-lhm4 / PR #152, merged to main as `5dadcdafc680ee41999079e55bd085dd2e73439c`.

Commands run:
- `uv build` (at head `faeac0c9092952f78e5c5944f0dabf4e805b4db2`) -> exit 0, produced exactly one wheel and one sdist.
- `uv venv <tmp>/venv && uv pip install --python <tmp>/venv/bin/python <wheel>` -> exit 0.
- `cd /tmp && <tmp>/venv/bin/wgp doctor` with `PYTHONPATH` and `WANGP_SSH_TARGET` unset -> exit 0, `ready=yes`, with `wangp` and `scripts` resolved from the venv site-packages.
- `gh run list` at `faeac0c` -> run 35631378806, conclusion success; on main after merge -> run 35633778277, conclusion success.
- `git diff --exit-code main -- services/ qc/ host/ predict/` -> exit 0 (no engine change).

Artifacts (head faeac0c):
- wheel `wangp_dspy-0.1.0-py3-none-any.whl` sha256 `ac8dcb9903b824a4be9fcb6850fbb31ee4ba4b81798fb53efc1839f04b91cc0c`
- sdist `wangp_dspy-0.1.0.tar.gz` sha256 `d7ccbe167290ff74f27d261ad1c216ff1396ba3bc7df601d7e13072295d1e497`
- fix commit on the story branch: `faeac0c9092952f78e5c5944f0dabf4e805b4db2`; merged commit on main: `5dadcdafc680ee41999079e55bd085dd2e73439c`

### Acceptance-criteria verification

| Acceptance criterion | Evidence | Status |
|---|---|---|
| `uv build` produces a wheel | `uv build` exit 0; wheel hash recorded above | PASS |
| `uv build` produces an sdist | `uv build` exit 0; sdist hash recorded above | PASS |
| CI verifies both artifacts | `.github/workflows/ci.yml` builds both and asserts exactly one wheel and one sdist; runs 35631378806 (story head) and 35633778277 (main) both success | PASS |
| Installed package usable, not just source tree | wheel installed into a throwaway venv outside the repo; `wgp doctor` exit 0 from `/tmp` with `PYTHONPATH` unset, imports resolved from site-packages | PASS |
| No engine or gate semantics changed | `git diff --exit-code main -- services/ qc/ host/ predict/` exit 0 | PASS |

Residual, disclosed and NOT part of this bug: a wheel-installed `wgp plan` still needs a git checkout for repository identity (exit 4 from a non-repo cwd). Recorded as a discovered defect in WD-lhm4; it is a gateway/ledger semantics question, not a packaging failure.

## nd_contract
status: delivered

### evidence
- Build, install, and CI evidence above; independent PM acceptance of WD-lhm4 marked the installed-`wgp` finding FIXED after building and installing the wheel itself.

### proof
- [x] Pending: wheel builds successfully and CI verifies both artifacts.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-21.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Delivery Evidence — satisfied by reference to WD-lhm4 / PR #152

This bug's acceptance criterion is "wheel builds successfully and CI verifies both artifacts". That is now true on `main` and was verified independently by three parties.

Fix location: the duplicate package declaration was removed and the wheel list corrected in PR #152 (`pyproject.toml`, now `packages = ["wangp", "predict", "evaluate", "host", "signatures", "qc", "services", "scripts"]`), which also had to fix the root cause of the installed-`wgp` startup failure (`scripts` was not packaged; the gateway import is now lazy).

Evidence:
- `uv build` produces BOTH artifacts. At head `faeac0c` (PR #152): wheel `wangp_dspy-0.1.0-py3-none-any.whl` sha256 `ac8dcb9903b824a4be9fcb6850fbb31ee4ba4b81798fb53efc1839f04b91cc0c`; sdist `wangp_dspy-0.1.0.tar.gz` sha256 `d7ccbe167290ff74f27d261ad1c216ff1396ba3bc7df601d7e13072295d1e497`. I reproduced the build myself before merge.
- The wheel installs into a throwaway virtualenv outside the repository and `wgp doctor` runs from a foreign working directory with `PYTHONPATH` unset, resolving `wangp` and `scripts` from that venv's site-packages. Verified by me and independently by the PM acceptor for WD-lhm4.
- CI now builds both artifacts and asserts exactly one wheel and one sdist (`.github/workflows/ci.yml`), so the AC "CI verifies both artifacts" is met. Required CI green at `faeac0c` (run 35631378806) and on main after merge `5dadcda` (run 35633778277).
- Independent verdict: the WD-lhm4 acceptor marked finding 1 (installed `wgp` works from a wheel) FIXED after building and installing the wheel itself, and explicitly noted that the packaging overlap with WD-m1sj was necessary and correctly left open here until now.

Residual, disclosed and NOT part of this bug: a wheel-installed `wgp plan` still requires a git checkout for repository identity (exits 4 from a non-repo cwd). That is a gateway/ledger semantics question recorded in WD-lhm4 as a discovered defect, not a packaging failure.

No tracker state for other stories was changed.

## History
- 2026-09-21T17:45:39Z status: open -> in_progress
- 2026-09-21T17:45:39Z auto-follows: linked to predecessor WD-lhm4
- 2026-09-21T17:45:49Z status: in_progress -> in_progress
- 2026-09-21T17:45:49Z auto-follows: linked to predecessor WD-3nwm

## Links
- Parent: [[WD-t534]]
- Follows: [[WD-lhm4]], [[WD-3nwm]]

## Comments
