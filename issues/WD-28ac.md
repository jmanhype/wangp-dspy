---
id: WD-28ac
title: "LTX dependency terminalization batch"
status: in_progress
priority: 1
type: task
labels: [video, evidence, external-integration, operator-decision]
parent: WD-3nod
created_at: 2026-09-29T07:05:33Z
created_by: speed
updated_at: 2026-09-29T07:13:46Z
content_hash: "sha256:73670c017f97acb3f4a124ce287e826b1740e03118eb4da251f330aa6574fe36"
blocks: [WD-fay0]
assignee: dev-WD-28ac
follows: [WD-23rs]
---

## Description
## Context

Seven video capability cells remain non-terminal `dependency_blocked` after the accepted WD-m7xw and WD-osfm runs:

- LTX-2.5: outpaint, repaint, recast, upscale
- LTX-2.3: outpaint, recast, upscale

These are exact missing-asset boundaries, not hardware-infeasibility verdicts and not inherited successes from each row's verified operations. The goal requires every affected cell to end at either checker-valid `host_run_verified` or an operator-approved terminal boundary.

HEAD-only metadata collection downloaded zero model bytes. The required unique assets are:

| Asset | Destination | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors` | `/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors` | 1,308,778,338 | `4647f4f18c87208f949b6f473d49af679ddd87532b40718480e5153852f1f1ba` |
| `ltx-2.3-22b-ic-lora-outpaint.safetensors` | `/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-ic-lora-outpaint.safetensors` | 1,308,756,416 | `76df7c1ccbe8d657e38f38e8defbc0755a8d57b1a2b34fcad1f6376f4ce289f0` |
| `ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors` | `/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors` | 1,308,778,338 | `748bca2d539cf2776abe801da96f06d6f31eec64f2354dea0f4b336292d3b837` |
| `ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors` | `/home/straughter/Wan2GP/ckpts/ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors` | 327,322,640 | `229e549af18993e1670ad5dac7d2d8d03bb558ae446ac4ee23f8ba1263783996` |
| `ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors` | `/home/straughter/Wan2GP/ckpts/ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors` | 19,447,662,547 | `f27d0effb85903172d976f1929dc0b3a204944ff014574eaab51cdc5e54f0f22` |

Total unique download volume: **23,701,298,279 bytes**. The batch is below the prior 60 GB ceiling but still requires explicit model-download and GPU-host authorization.

## USER INTENT

The operator wants the remaining LTX rows to have truthful terminal outcomes rather than ambiguous dependency blocks. Observable outcome: after authorization, the operator can run the canonical checker and receive an explicit pass/fail result for each of the seven affected cell bundles.

## Operator authorization status

**NOT AUTHORIZED.** No verbatim operator approval for this batch is present. Until recorded, this story must remain deferred and no worker may contact host `3090`, download any asset, mutate storage, or run a generation.

Authorization must explicitly approve:

- all five assets and exactly 23,701,298,279 download bytes;
- host `3090` and the governed Wan2GP execution path;
- only the seven named operations;
- no training, provider spend, unrelated mutation, threshold change, or protected-engine semantic change;
- reversible storage handling and deletion prohibition.

## OUT OF SCOPE

- WD-bw0h clean-machine H3 retry; it has a separate consumed-authorization boundary.
- LTX blend; it already has an accepted typed backend boundary.
- Any already verified LTX operation, existing media, native log, or provenance record.
- Any model or operation not named above.
- Training, registry publication, GUI work, or protected-engine changes.

## DIFF BUDGET

About 5 files and under 500 authored/evidence LOC, excluding native logs and media bytes.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/ltx-dependency-terminalization/model-assets.json -> exact five-asset `wangp-dspy.model-assets/v1` manifest with source, destination, size, SHA-256, license, and authorization linkage
- datasets/runs/maestro-parity/ltx-dependency-terminalization/ -> seven-operation download, host-run, media/gate, boundary, checker, and matrix-transition evidence
- docs/video-capabilities.md -> terminal updates for exactly the seven named dependency-blocked cells
- tests/test_ltx_dependency_manifest.py -> manifest totals, hashes, cell ownership, and fail-closed drift/authorization tests

CONSUMES:
- WD-m7xw: datasets/runs/maestro-parity/WD-m7xw/dependency-boundaries.md -> exact four LTX-2.5 missing-asset boundaries
  source: operation, native exit/stage, absent asset identity, and zero-output evidence; do not inherit successful-operation evidence.
- WD-osfm: datasets/runs/maestro-parity/WD-osfm/boundary-evidence.json -> exact three LTX-2.3 missing-asset boundaries
  source: records[].operation, dependency, dependency_source, failing_stage, log, and boundary fields.
- WD-23rs: scripts/verify_maestro_parity.py -> verify_bundle(bundle: Path) -> VerificationReport; verify_checker_receipt(...) -> VerificationReport
  source: canonical pass/fail and warning-ownership semantics; no second checker standard.
- WD-23rs: docs/maestro-parity-evidence-contract.md -> `wangp-dspy.maestro-parity-evidence/v1`
  source: authorization, provenance, native-log, output, gate, and reviewer requirements.

## Story Acceptance Criteria
1. [State] Before any network or host action, the live tracker records verbatim operator approval for all five assets, exactly 23,701,298,279 bytes, host `3090`, and the seven named operations; absent or partial approval fails closed.
2. [State] Each declared file is downloaded exactly once to its declared destination, then passes exact size and SHA-256 verification; the download report records zero undeclared bytes and no substitution from unrelated assets.
3. [State] Host preflight verifies SSH, disk headroom, GPU state, Wan2GP/tree identity, existing accepted LTX assets, and configured QC before any queue admission.
4. [State] Each of the seven named operations runs once through the governed queue/adapter path with exact argv, durable state, native logs, exit state, and either a real nonempty output or a typed terminal boundary; no operation inherits another cell's evidence.
5. [State] Every successful output is hash-bound, ffprobe-probed, visually represented, objectively gated, checker-validated, and independently reviewed; genuine runtime failures become exact operator-reviewed terminal boundaries rather than being relabelled as hardware infeasibility.
6. [State] Exactly the seven named `dependency_blocked` cells change in `docs/video-capabilities.md`; all other cells and rows remain byte-for-byte semantically unchanged.
7. [State] Focused manifest/checker tests, the undeselected full suite, `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity, `git diff --check`, and exact-head CI pass.

## Testing Requirements
- Integration tests are mandatory with no mocked network, host, model, queue, generation, media, or checker behavior.
- Add real fail-closed tests for absent authorization, partial asset approval, wrong hash/size, undeclared download bytes, and manifest drift.
- Run the canonical checker on every produced success or terminal-boundary bundle.
- Run focused tests, the undeselected full suite with parsed JUnit, lint, release verification, protected parity, diff check, and exact-head CI.

## Delivery Requirements
- Record verbatim authorization, exact command and argv, commit/tree identity, asset hashes and bytes, host/storage state, queue state, native logs, output hashes/metadata/gates, bundle sizes, PR, CI, and AC table.
- Include `LEARNINGS:`.
- If download, preflight, generation, or checking fails, stop and record the typed boundary; never substitute an existing output.

## MANDATORY SKILLS
- pvg
- tool-systematic-debugging

## nd_contract
status: new

### evidence
- Current matrix audit at main `2c20caa1`: exactly seven `dependency_blocked` cells remain in the two LTX rows.
- WD-m7xw and WD-osfm record the exact absent assets and fail-closed offline behavior.
- HEAD-only metadata measured five unique assets totaling 23,701,298,279 bytes with the SHA-256 values above; zero model bytes were downloaded.

### proof
- [ ] Pending explicit operator authorization, exact download verification, governed seven-operation run, terminal matrix transition, checker proof, and standing gates.

## Acceptance Criteria


## Design


## Notes
Observable outcome: after authorization and execution, the operator can run the canonical checker on each of the seven affected cell bundles and it returns an explicit pass/fail result with exact provenance or boundary evidence.
## nd_contract
status: in_progress

### evidence
- Local manifest-prep boundary active at worktree HEAD 2c20caa1 on story/WD-28ac.
- No host/3090 contact, model-byte download, HEAD request, Hugging Face curl, storage mutation, queue/render action, or capability-matrix edit will occur.
- Preparing only the exact five-asset model manifest, fail-closed JSON tests, and a not_authorized local authorization template.

### proof
- [ ] Pending local manifest/test artifact and exact-head CI; this remains not delivered while operator authorization is absent.

## History
- 2026-09-29T07:05:34Z dep_added: blocks WD-fay0
- 2026-09-29T07:05:34Z status: open -> deferred
- 2026-09-29T07:07:31Z status: deferred -> open
- 2026-09-29T07:07:37Z status: open -> in_progress
- 2026-09-29T07:07:37Z auto-follows: linked to predecessor WD-23rs
- 2026-09-29T07:07:37Z claimed by dev-WD-28ac

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-23rs]]

## Comments
