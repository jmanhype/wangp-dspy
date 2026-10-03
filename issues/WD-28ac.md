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
updated_at: 2026-10-03T08:11:11Z
content_hash: "sha256:d6ae68b334dea782d6749299e08770a90fa3e9d562a3d23d60da9c1997732683"
blocks: [WD-fay0]
follows: [WD-23rs, WD-p587, WD-1s5s, WD-cuzw, WD-he8i]
was_blocked_by: [WD-1s5s, WD-cuzw]
assignee: dev-WD-28ac
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
## Authorized Execution Start

- Worktree: /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-28ac
- HEAD: cd57dfc53d41fa73b94f7426c9c76e58360b20dc
- Authorization source: live tracker comment recorded at 2026-09-29T23:17:30Z, verbatim operator input "Authorize".
- Authorized scope: exactly five manifest assets totaling 23701298279 bytes, host 3090, governed Wan2GP path, and only LTX-2.5 outpaint/repaint/recast/upscale plus LTX-2.3 outpaint/recast/upscale.
- No unrelated model, training, provider spend, protected-engine semantic change, threshold change, merge, or acceptance is authorized.

## nd_contract
status: in_progress

### evidence
- Local artifacts committed at cd57dfc53d41fa73b94f7426c9c76e58360b20dc on story/WD-28ac:
  - datasets/runs/maestro-parity/ltx-dependency-terminalization/model-assets.json
  - datasets/runs/maestro-parity/ltx-dependency-terminalization/operator-authorization.template.json
  - tests/test_ltx_dependency_manifest.py
- Manifest contains exactly the five story assets, canonical schema, source/destination/size/SHA-256/license data, and total 23701298279 bytes. Its canonical-JSON SHA-256 linkage in the authorization template is 7f159b99bdd3a688763c5c3d4188f5672ecff9af8003d2c5f76ab783fa31ceb1.
- Authorization template remains status=not_authorized with operator_approval=null; no approval is claimed.
- Focused test: /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest tests/test_ltx_dependency_manifest.py -q => 11 passed.
- Undeselected full suite with parsed JUnit: /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest -q -ra --junitxml=/tmp/wd28ac_full.junit.xml => tests=2138 failures=0 errors=0 skipped=1 time=844.556s. The sole skip is the pre-existing live-host gate tests/test_jobs_integration_3090.py:20 requiring WANGP_3090=1; no host was contacted.
- pvg verify changed files --include-tests => VERIFY: PASSED (1 files scanned, 0 issues).
- pvg lint --backlog => scanned 152 issues; 0 errors, 0 review findings.
- wgp release verify => version/checks pass, release=ready, tag_created=false.
- Protected parity: git diff --exit-code origin/main -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py => exit 0. git diff --check => pass.
- PR: https://github.com/jmanhype/wangp-dspy/pull/217
- Exact-head CI at cd57dfc53d41fa73b94f7426c9c76e58360b20dc: https://github.com/jmanhype/wangp-dspy/actions/runs/36538874449 => success, CI/test 24m37s.
- Boundary honored: no SSH/3090 contact, model-byte download or HEAD request, Hugging Face curl, storage mutation, queue admission/render/retrieval, docs/video-capabilities.md change, or protected-engine edit.

### proof
- [x] Local manifest preparation and fail-closed JSON coverage exist at cd57dfc5 with passing focused, full-suite, lint, release, protected-parity, diff, and exact-head CI evidence.
- [ ] NOT DELIVERED: operator authorization for all five assets, exactly 23701298279 bytes, host 3090, and the seven operations remains absent; downloads, host work, matrix terminalization, acceptance, and merge remain blocked.

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
- 2026-09-29T08:16:37Z status: in_progress -> open
- 2026-09-29T08:16:37Z released by speed
- 2026-09-29T08:16:39Z status: open -> deferred
- 2026-09-29T23:17:51Z status: deferred -> open
- 2026-09-29T23:18:01Z status: open -> in_progress
- 2026-09-29T23:18:02Z auto-follows: linked to predecessor WD-p587
- 2026-09-29T23:18:02Z claimed by dev-WD-28ac
- 2026-09-30T14:49:05Z status: in_progress -> open
- 2026-09-30T14:49:05Z released by speed
- 2026-09-30T14:51:37Z status: open -> deferred
- 2026-09-30T17:56:46Z dep_added: blocked_by WD-1s5s
- 2026-09-30T19:29:46Z dep_removed: was_blocked_by WD-1s5s
- 2026-09-30T20:00:02Z dep_added: blocked_by WD-cuzw
- 2026-10-01T23:49:42Z dep_removed: was_blocked_by WD-cuzw
- 2026-10-03T06:57:56Z status: deferred -> open
- 2026-10-03T06:57:56Z status: open -> in_progress
- 2026-10-03T06:57:56Z auto-follows: linked to predecessor WD-1s5s
- 2026-10-03T06:57:56Z auto-follows: linked to predecessor WD-cuzw
- 2026-10-03T06:57:56Z claimed by dev-WD-28ac
- 2026-10-03T07:44:32Z status: in_progress -> open
- 2026-10-03T07:44:32Z released by speed
- 2026-10-03T08:11:11Z status: open -> in_progress
- 2026-10-03T08:11:11Z auto-follows: linked to predecessor WD-he8i
- 2026-10-03T08:11:11Z claimed by dev-WD-28ac

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Was blocked by: [[WD-1s5s]], [[WD-cuzw]]
- Follows: [[WD-23rs]], [[WD-p587]], [[WD-1s5s]], [[WD-cuzw]], [[WD-he8i]]

## Comments

### 2026-09-29T08:16:39Z speed
Parked as operator-gated after local preparation. PR 217 head cd57dfc53d41fa73b94f7426c9c76e58360b20dc has exact-head CI success and the five-asset fail-closed manifest/tests, but no operator approval exists. No network/host/model action is authorized by this status change.

### 2026-09-29T23:17:30Z speed
OPERATOR AUTHORIZATION at 2026-09-29T23:17:30Z. Verbatim user input: Authorize. Interpreted scope from the immediately prior authorization request: WD-28ac five-asset LTX dependency batch, exactly 23,701,298,279 bytes, on host 3090, only the seven named LTX operations, with exact manifest hashes and no unrelated mutation.

### 2026-09-29T23:22:07Z speed
Dispatch note: operator authorization is recorded, but host-3090 execution is queued behind the WD-bw0h one-attempt clean-machine H3 run to prevent overlapping host/GPU mutations. Do not interpret the wait as lost approval.

### 2026-09-30T14:49:05Z speed
BLOCKED: Authorized host-3090 preflight passed SSH, tree identity, 34 existing accepted LTX assets, GPU idle, and host QC probes, but the destination filesystem has 17865703424 bytes free versus 23701298279 required (shortfall 5835594855). The largest declared asset is 19447662547 bytes, 1581959123 bytes larger than all free space. All five target assets remain absent. Moving/removing an unrelated asset or redirecting the declared destination was not authorized, so zero model bytes were downloaded and zero operations were admitted. Evidence and local gates are committed at fced67e1293dc2dbbdf3f29c8b615f6357012ab6; exact-head CI run 36728749388 passed. Distinct reversible-storage authorization is required before retry.

### 2026-09-30T14:50:25Z speed
CORRECTION to the prior BLOCKED comment: the live integration test exercised the configured qc_available check kind, but it does not assert a healthy QC result and the status was not captured. The durable preflight evidence proves host Python, ffmpeg, and ffprobe executable probes; it does not claim QC health. The storage boundary and zero-download/zero-admission decision are unchanged.

### 2026-09-30T14:51:37Z speed
Parked on measured destination-storage boundary after authorized preflight. Root filesystem has 17,865,703,424 bytes free versus 23,701,298,279 declared bytes; largest asset exceeds free space alone. /mnt/bulk-hdd has headroom, but moving unrelated assets or redirecting declared destinations requires a distinct operator-approved reversible storage plan. No model bytes downloaded, queue admitted, operation attempted, matrix cell changed, or unrelated host mutation occurred. PR 217 head fced67e1293dc2dbbdf3f29b8b615f6357012ab6a has exact-head CI success.

### 2026-09-30T15:30:18Z speed
Proposed shared storage remediation requiring operator authorization: after the two superseded H3 checkpoints are hash-verified and reversibly moved to /mnt/bulk-hdd/straughter/model-offload/wangp-3090, root free space should rise by about 44.28GB, enough for the exact 23.70GB LTX manifest plus output/workspace margin. Re-run host preflight before any download; if either H3 checkpoint is absent, hashes differ, target creation fails, or post-move root free space remains insufficient, stop typed. No LTX retry is authorized by this proposal.

### 2026-09-30T19:53:26Z speed
WD-1s5s storage-remediation packet is accepted and merged at main 498a9cb4c994033064161cace2a98165c0a1dbb2. Its stale-space projection does not authorize the exact five-asset/23701298279-byte LTX batch; that download/host batch still requires explicit operator approval.

### 2026-10-02T00:22:32Z speed
WD-cuzw storage offload is accepted/merged at main b5b7e35b131de72e541bec508fcac19fced895f3. Recorded remote free is 48494047232 bytes, which exceeds the exact 23701298279-byte five-asset LTX manifest by 24792764953 bytes before download. This storage fact does not authorize downloads or host execution; WD-28ac remains deferred pending explicit model-download and GPU-host approval.

### 2026-10-02T00:27:01Z speed
Read-only execution-readiness audit at merged main b5b7e35b131de72e541bec508fcac19fced895f3: existing story/WD-28ac head and origin head remain fced67e1293dc2dbbdf3f29c8b615f6357012ab6; PR 217 remains OPEN with exact-head CI success at that older head. A local three-way merge-tree simulation against current main reported exit 0 and no conflict markers. The branch contains the exact five-asset model manifest, not-authorized operator template, and prior preflight boundary. GitHub currently reports PR mergeability UNKNOWN, so after operator approval the worker must merge/rebase current main and rerun exact-head CI before execution. No host contact, download, model access, queue action, or authorization change occurred.

### 2026-10-03T06:57:55Z speed
OPERATOR AUTHORIZATION at 2026-10-03T06:57:55Z. Verbatim user input: Authorized. Scope is the immediately preceding blocked-goal request: WD-28ac on host 3090, exactly five LTX assets totaling 23701298279 download bytes, only the seven named operations, governed queue/adapter execution, no training/provider spend/unrelated mutation/threshold change/protected-engine change, and reversible storage handling with deletion prohibition. Record this verbatim authorization in the story branch before any network or host action.

### 2026-10-03T07:44:02Z speed
BLOCKED: Authorized download failed closed at the first declared asset. Observed size 1308778338 matches, but SHA-256 515e4e139001ac6282357a5b35372e42e98b3affd5fcc886a52242abeed19559 does not match 4647f4f18c87208f949b6f473d49af679ddd87532b40718480e5153852f1f1ba. A downloader defect also issued an undeclared URL-effectiveness GET that timed out after 172109 payload bytes. The partial is preserved at /home/straughter/Wan2GP/ckpts/ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors.WD-28ac.partial; no promotion, retry, deletion, queue admission, operation, output, or matrix change occurred. Distinct operator decisions are required for the source/hash discrepancy, undeclared bytes, and preserved partial before retry.

### 2026-10-03T07:44:31Z speed
BOUNDARY ARTIFACTS committed and pushed at 1672679ef6985ce16c5b87e409e5911b83e29c08 on story/WD-28ac. Focused tests: /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest tests/test_ltx_dependency_manifest.py tests/test_ltx_download_boundary.py -q => 16 passed. Boundary evidence paths: 15 present, 0 missing. pvg verify changed boundary files --include-tests => PASSED. git diff --check => PASS. Protected-file parity versus origin/main => PASS. No retry, deletion, promotion, queue admission, operation, output, or matrix transition.

### 2026-10-03T08:05:29Z speed
Exact-head CI for boundary commit 1672679ef6985ce16c5b87e409e5911b83e29c08 passed: run 37107341722, job 111158348210, duration 20m14s, https://github.com/jmanhype/wangp-dspy/actions/runs/37107341722. PR 217 remains open and mergeable. Story is released/open pending distinct operator decisions on the source/hash discrepancy, 172109 undeclared bytes, and preserved partial; no retry is authorized.

### 2026-10-03T08:07:38Z speed
Read-only post-boundary audit: repository-wide local evidence search found no prior occurrence of observed SHA-256 515e4e139001ac6282357a5b35372e42e98b3affd5fcc886a52242abeed19559; it found only the declared expected SHA-256 4647f4f18c87208f949b6f473d49af679ddd87532b40718480e5153852f1f1ba. This does not resolve upstream state and does not authorize retry. Preserve the remote partial unchanged pending a distinct operator decision on metadata audit, hash discrepancy, 172109 undeclared payload bytes, and retry/disposition.
