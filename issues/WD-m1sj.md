---
id: WD-m1sj
title: "uv build cannot produce a wheel: duplicate qc/audio_critic package declaration"
status: in_progress
priority: 1
type: task
parent: WD-t534
created_at: 2026-09-21T15:24:25Z
created_by: speed
updated_at: 2026-09-21T17:45:39Z
content_hash: "sha256:78c432f890ded2036f9f541fceedd518b33c797a29072562149507fa819f312a"
follows: [WD-lhm4]
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

## Links
- Parent: [[WD-t534]]
- Follows: [[WD-lhm4]]

## Comments
