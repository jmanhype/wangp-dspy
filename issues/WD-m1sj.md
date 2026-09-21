---
id: WD-m1sj
title: "uv build cannot produce a wheel: duplicate qc/audio_critic package declaration"
status: open
priority: 1
type: task
parent: WD-t534
created_at: 2026-09-21T15:24:25Z
created_by: speed
updated_at: 2026-09-21T15:24:25Z
content_hash: "sha256:eff43307dce58356e16256a59934b726df6d5ae2d3980fad891bc0c7b3b7f373"
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


## History


## Links
- Parent: [[WD-t534]]

## Comments
