---
id: WD-bw0h
title: "Clean-machine H3 generated artifact"
status: deferred
priority: 1
type: feature
labels: [install, evidence, external-integration, operator-decision]
parent: WD-3nod
created_at: 2026-09-28T13:32:24Z
created_by: speed
updated_at: 2026-09-30T15:30:18Z
content_hash: "sha256:752f92834c8a553d39ec23673d12a5f3c5b5e999dc449be393b0ba37cf3ae1d4"
blocks: [WD-fay0]
follows: [WD-0zj8, WD-isg9, WD-dc3w, WD-p587, WD-23rs]
---

## Description
## Context

## USER INTENT
A stranger should be able to start from a clean disposable checkout/workspace, run one documented command, and reach a real generated H3 artifact through the governed Wangp engine. The operator has now authorized exactly one no-new-download attempt.

## Operator authorization
Verbatim operator input:

> Approve

Recorded at `2026-09-28T13:20:11Z` in response to the three-way authorization question. This story uses the approval for exactly one no-new-download H3 generated-artifact attempt on host `3090`.

Authorized boundary:

- One clean disposable workspace and checkout.
- One real H3 standard create operation through the governed queue/adapter path.
- Zero model downloads or provider spend.
- Reuse only the four hash-verified local H3 assets listed below.
- No training, registry publication, GUI, tag creation, protected-engine semantic change, threshold change, or unrelated host mutation.
- Reversible, hash-verified storage relocation to `/mnt/bulk-hdd` is allowed only for superseded model bytes that are not in the authorized manifest; deletion is prohibited.

## Embedded host/model state
Merged main: `6ac1023b522726705d3ea560216f211003a1d4bd`.

Host `3090` currently has approximately `19.1 GB` free on `/`, below Wangp's `50 GB` remote preflight floor, while `/mnt/bulk-hdd` has approximately `295 GB` free. The GPU is idle with roughly `23.97 GiB` free.

Authorized no-download model manifest:

| Asset | Destination | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| H3 rank8 int8 ConvRot | `/home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA-pruned_rank8_int8_convrot.safetensors` | 21,057,674,787 | `30ff400f974b11a1ef13d216c5d9f6439a9c10322a3988b0374a39672ce286f0` |
| H3 video VAE | `/home/straughter/Wan2GP/ckpts/MiniMax-H3-video_vae_fp16.safetensors` | 5,207,806,512 | `455010492bb59a9cc7b8f1ee23905b22a10079f89490adbf820a1728efcaea6b` |
| H3 audio VAE | `/home/straughter/Wan2GP/ckpts/MiniMax-H3-audio_vae_fp32.safetensors` | 605,429,308 | `37dddc2f3e6d5d5139d823d5ea283bbf304dadcb885b1ccda818aa13dade5ea2` |
| Qwen3-VL layer50 int8 | `/home/straughter/Wan2GP/ckpts/Qwen3-VL-32B-Instruct/Qwen3-VL-32B-Instruct-layer50_quanto_bf16_int8.safetensors` | 26,723,791,903 | `4df8fc5237746b3b058745d6ec8fe1e54a9721bdc663d35d2d1806952672f301` |

All four hashes were measured live on `2026-09-28`. Two superseded non-rank8 H3 checkpoints are present and not referenced by this manifest:

- `/home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA-pruned_int8_convrot.safetensors` (`22,144,108,396` bytes)
- `/home/straughter/Wan2GP/ckpts/MiniMax-H3-Ref2VA-pruned_int8_convrot.safetensors` (`22,144,108,397` bytes)

They may be relocated to `/mnt/bulk-hdd/straughter/model-offload/wangp-3090/` only after full size/hash verification and only by a reversible move.

## OUT OF SCOPE
- Any model download, substitute model, provider API, training, GUI, publication, or second render.
- Any change to `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, or `scripts/run_film.py`.
- Director or consent matrix closeout.
- Deleting any artifact or unverified model.

## DIFF BUDGET
- About 7 files and under 500 authored/evidence LOC: clean-proof installer mode or helper, model manifest/authorization bundle, host scripts, docs, tests, and run receipts.

## Boundary Map
PRODUCES:
- install.sh -> one-command generated clean-proof mode
  spec: from an absent workspace, installs the selected source into isolated tool/cache/HOME state, clones a disposable checkout, verifies the authorized manifest/host, submits exactly one H3 job through the governed path, retrieves the artifact and evidence, and exits with a checker-valid result or typed failure.
- datasets/runs/maestro-parity/clean-generated/model-assets.json -> exact four-asset `wangp-dspy.model-assets/v1` manifest
  event: every entry carries source URL, destination, exact size, SHA-256, license, and no-download/use authorization.
- datasets/runs/maestro-parity/clean-generated/ -> complete generated-artifact evidence bundle
  event: stores operator authorization, storage relocation proof, clean workspace identity, exact command, resolved commit/dirty state, tool versions, host/model hashes, preflight, queue/job/retry state, native argv/log, output hash, ffprobe metadata, contact sheet/first frame, objective gate, canonical checker result, and reviewer decision.
- docs/install.md and README.md -> generated-proof command without weakening the no-GPU refusal proof
  event: clearly distinguish no-GPU install/plan, typed refusal, and this separately authorized generated-artifact mode.

CONSUMES:
- WD-0zj8: install.sh -> existing isolated `--clean-proof <dir>` no-GPU implementation
  source: extend the established isolated HOME/cache/tool/checkout behavior rather than creating a second installer.
- WD-0zj8: scripts/record_clean_machine_refusal.py -> typed `HOST_CONFIGURATION_INCOMPLETE` and `MODEL_MANIFEST_REQUIRED` refusal behavior
  source: preserve the no-authorization path unchanged; the new mode must supply complete explicit inputs before host contact.
- (existing): datasets/runs/maestro-parity/WD-isg9/model-assets.json -> accepted four-asset H3 manifest schema and exact hashes
  source: reuse the asset identities and destinations exactly; do not download or substitute bytes.
- (existing): host/wangp_adapter.py -> governed render transport and Wan2GP adapter
  spec: use the existing adapter/queue seams; no direct filesystem shortcut may replace governed execution.

## Story Acceptance Criteria
1. [State] Before host contact, all four authorized model files exist with exact size and SHA-256; the evidence records zero network download bytes.
2. [State] If storage preparation is needed, only superseded non-manifest model bytes are reversibly moved to `/mnt/bulk-hdd`; before/after hashes match, source links are removed only after verified copy, remote free space reaches at least 50 GB, and no deletion occurs.
3. [State] The documented one-command mode starts from an absent isolated workspace, installs into isolated tool/cache/HOME paths, clones a clean checkout, resolves and records its commit with a clean tree, and requires no manual editing inside that workspace.
4. [State] Host/model preflight passes SSH, model hashes, disk headroom, GPU idle state, and configured QC availability before queue admission.
5. [State] Exactly one H3 standard create job is admitted through the governed path with exact argv, native log, durable queue/retry state, exit success, and a real nonempty generated artifact.
6. [State] The artifact is retrieved, hash-verified, probed, visually framed/contact-sheeted, and passes an operation-appropriate objective gate; the canonical evidence checker exits zero.
7. [Unwanted] No undeclared download, second generation, provider spend, protected-engine change, threshold change, training, unrelated process action, or deletion occurs.
8. [State] Focused clean-install/generated-proof tests, the undeselected full suite, `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity from `6ac1023b`, and `git diff --check` pass.

## Testing Requirements
- Real-process integration is mandatory with no mocked installer, SSH, model, queue, generation, media, or checker behavior.
- Preserve and rerun the accepted no-GPU clean-proof typed-refusal test.
- Add a real generated-proof test or recorded replay that proves the one-command mode cannot reach generation with absent authorization/config/manifest.
- Record clean workspace identity and ensure the operator's normal configuration/checkout remains unchanged.
- Probe output with ffprobe and mechanically derive the objective gate.
- Run the canonical checker on the generated bundle.
- Run exact-head CI, undeselected full suite, lint, release, protected parity, and diff gates.

## Delivery Requirements
- Record every authorization boundary, storage move, model hash, command, workspace/commit identity, queue state, native log path, output hash/metadata/gate, bundle size, commit SHA, PR, and CI result.
- Include `## Implementation Evidence`, `Summary:`, `Commands run:`, `SHA:`, `### CI/Test Results`, `### AC Verification`, and `LEARNINGS:`.
- If any preflight/model/generation/checker step fails, stop and record the typed boundary; never substitute an existing artifact.

## MANDATORY SKILLS
- pvg
- tool-systematic-debugging

## nd_contract
status: new

### evidence
- Created from operator authorization at `2026-09-28T13:20:11Z`, merged main `6ac1023b522726705d3ea560216f211003a1d4bd`, live host state, and accepted WD-0zj8/WD-isg9 patterns.

### proof
- [ ] Pending storage preparation, clean one-command implementation, real H3 generation, checker, and standing gates.

## Acceptance Criteria


## Design


## Notes
## Authorized Attempt Boundary (RETRY STOPPED)

STOPPED: the sole authorized clean-machine H3 retry exited 4 with
`STORAGE_PREPARATION_FAILED` / `cannot create offload root` after clean isolated
install/clone/sync, clean workspace recording, successful SSH disk probing, and
before relocation, model identity preflight, queue admission, offline wrapper
setup, rendering, retrieval, media gates, or canonical checking.

Evidence:
- Exact operator authorization corrected and committed: `Authorize` at `2026-09-29T23:17:30Z`.
- Authorization correction commit: `44c8d82dbfd4bebd7b337d9b60446b2357030613`.
- Clean clone resolved commit: `44c8d82dbfd4bebd7b337d9b60446b2357030613`.
- Clean clone status: empty (`repository-status.txt`, 0 bytes).
- Failure bundle: `datasets/runs/maestro-parity/clean-generated/failed-retry/`.
- Failure record SHA-256: `7d8320174c0d621cd32b4013acaddb81e92fc72a9d2af3eeabed76f5d987a6d5`.
- Boundary bundle count/size: 20 files, 20,349 bytes.
- No retry, second generation, artifact substitution, model download/read/render, queue admission, provider spend, training, relocation, deletion, protected-engine change, or threshold change followed.
- The remote mkdir return code/stderr was not retained by the recorder; host recontact is prohibited by the one-attempt boundary.

Local preflight before the sole attempt:
- Local tool/version checks passed.
- Four-asset manifest semantic comparison against accepted WD-isg9 manifest passed.
- Generated workspace was absent; local disk had about 53 GiB available.
- Installer dry-run passed.
- `uv run --frozen --extra dev pytest -q tests/test_clean_generated_proof.py tests/test_install.py` — 12/12 PASS.
- `pvg verify scripts/record_clean_generated_proof.py tests/test_clean_generated_proof.py --format=text --include-tests` — PASS, 0 issues.

WD-bw0h remains in_progress/not delivered because ACs 1-6 and 8 do not have generated-artifact success evidence.

## Boundary Map Repair (dispatcher)

PRODUCES:
- scripts/record_clean_generated_proof.py -> clean-generated recorder for authorization, workspace identity, fail-closed evidence, and generated bundle receipts
- tests/test_clean_generated_proof.py -> real regressions for recorder behavior, workspace path serialization, exact authorization input, and fail-closed host tampering

This is a structural declaration repair only. It does not alter WD-bw0h status, consume or grant a new host attempt, or claim the real generated artifact.

## Local Repair Evidence (NOT DELIVERED)

### Root cause and repair
- Read the recorded failure bundle at `datasets/runs/maestro-parity/clean-generated/failed-attempt/`: exit 4, `UNEXPECTED_GENERATED_PROOF_FAILURE`, `TypeError: Object of type PosixPath is not JSON serializable`.
- Reproduced locally without invoking installer/generated mode: `record(..., {"workspace": Path, "checkout": Path})` raised the same `TypeError`.
- Root cause: `record_clean_generated_proof.record()` passed values directly to `json.dumps()`, while `workspace.json` intentionally carried `Path` workspace/checkout values.
- Added regression `test_workspace_record_serializes_paths_without_permissive_json_values`; it failed before the fix with the recorded `PosixPath` TypeError and now verifies string serialization plus rejection of unsupported non-JSON objects.
- Fix commit `840a48a213435f79c97961dbd3c536ec654d3c15` recursively converts only `Path` values (inside mappings/sequences) before JSON encoding; it does not add permissive `default=str`.

### Exact-head CI finding and follow-up repair
- First PR CI at `840a48a213435f79c97961dbd3c536ec654d3c15` failed `tests/test_runtime_host_wiring.py::test_active_runtime_has_no_operator_host_defaults` because this story recorder embedded operator host values in active runtime code.
- Follow-up fix commit `64897225cd219af5407c80235f664d11ac1f9eca` removes that runtime default and requires the exact tracked operator-authorization payload; the runtime host config is sourced from `allowed_host`.
- Added `test_generated_mode_rejects_tampered_host_before_workspace`, proving a changed host target still exits 4 with `CLEAN_GENERATED_INPUT_INVALID` before the proof workspace is created.

### Merge, commits, PR, CI
- Merged `origin/main` exactly at `a382f747f31735c9eaa5eecb4bb6e1581b3403de` via merge commit `2f4e7c69571245ec9e515360f10c496f669bd356`.
- Branch: `story/WD-bw0h`; final local head and pushed head: `64897225cd219af5407c80235f664d11ac1f9eca`.
- PR: https://github.com/jmanhype/wangp-dspy/pull/215
- Exact-head CI run `36519763680` at `64897225cd219af5407c80235f664d11ac1f9eca`: completed successfully in 23m53s (`test`, build distributables, and all job steps passed).

### Local gates at final head
- `uv run --frozen --extra dev pytest -q tests/test_clean_generated_proof.py tests/test_install.py` — PASS, 11/11.
- `uv run --frozen --extra dev pytest -q tests/test_readme_quickstart.py::test_clean_checkout_install_plan_then_typed_generation_refusal` — PASS, 1/1.
- `uv run --frozen --extra dev pytest -q tests/test_runtime_host_wiring.py::test_active_runtime_has_no_operator_host_defaults` — PASS, 1/1.
- `uv run --frozen --extra dev python -m compileall -q scripts/record_clean_generated_proof.py tests/test_clean_generated_proof.py` — PASS.
- `pvg verify scripts/record_clean_generated_proof.py tests/test_clean_generated_proof.py --format=text --include-tests` — PASS, 2 files, 0 issues.
- `pvg lint --backlog` — PASS, 150 scanned, 0 errors, 0 review findings.
- `uv run --frozen --extra dev wgp release verify --json` — PASS, `ready=true`, `tag_created=false`, clean tree at `64897225`.
- Protected-file parity against `6ac1023b` for `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py` — PASS (empty diff).
- `git diff --check` — PASS.

### Explicit boundary
- This local repair did NOT run the clean-generated command or retry generation, contact host 3090/SSH, preflight models, move storage, admit a queue job, download model bytes, render/retrieve/admit anything, modify protected engine files, or fabricate generated evidence.
- WD-bw0h remains claimed/in_progress and is NOT delivered or accepted; the real H3 generated-artifact ACs remain unmet because the one authorized host attempt was already consumed.

## nd_contract
status: in_progress

### evidence
- Local repair commits: `840a48a213435f79c97961dbd3c536ec654d3c15`, `64897225cd219af5407c80235f664d11ac1f9eca`.
- PR: https://github.com/jmanhype/wangp-dspy/pull/215
- Exact-head CI success at `64897225cd219af5407c80235f664d11ac1f9eca`: run `36519763680`.

### proof
- [x] Local `PosixPath` serialization regression and fail-closed rejection coverage pass.
- [x] Focused recorder/installer and available static/diff/release/protected-parity gates pass.
- [x] Exact-head CI passes at the final PR head.
- [ ] Real H3 generated artifact and canonical generated-evidence checker remain intentionally unclaimed; the authorized attempt is consumed.

## Authorized Attempt Boundary (STOPPED)

STOPPED: the single authorized clean-generated command exited 4 with
`UNEXPECTED_GENERATED_PROOF_FAILURE` after local clean install/clone/sync and
before host contact. Root cause recorded from the fail-closed path: a
`PosixPath` workspace value reached JSON serialization. No retry, existing-artifact
substitution, SSH, model preflight, storage relocation, queue admission, Wan2GP
render, provider spend, training, protected-engine change, threshold change, or
deletion followed.

Evidence:
- Producing implementation commit: `eddff6bc8bf77fb7fa8d711a44beacbb314e4b2c`
- Evidence commit: `223cb563bc242d7a17b544efc74094021a621d80`
- Clean clone resolved commit: `eddff6bc8bf77fb7fa8d711a44beacbb314e4b2c`
- Clean clone status: empty (`repository-status.txt`, 0 bytes)
- Failure SHA-256: `f2314ba2c7b53a040bb43f5a595555140578e58a8c061e61c33ea4918a6566bf`
- Boundary bundle: `datasets/runs/maestro-parity/clean-generated/failed-attempt/`
- Boundary proof: `remote-scripts`, `storage`, `preflight`, `queue.db`, `host-logs`, `outputs`, and `checker` were absent.
- Model bytes read/downloaded/rendered: 0; package installation did download locked dependencies, explicitly distinct from model bytes.

Focused tests before the authorized command:
- `uv run --frozen --extra dev pytest -q tests/test_clean_generated_proof.py` — 5/5 PASS
- `uv run --frozen --extra dev pytest -q tests/test_clean_generated_proof.py tests/test_install.py` — 9/9 PASS
- `uv run --frozen --extra dev pytest -q tests/test_readme_quickstart.py::test_clean_checkout_install_plan_then_typed_generation_refusal` — 1/1 PASS
- `pvg verify ... --format=text` — PASS
- `pvg lint --backlog` — PASS, 150 scanned, 0 errors, 0 review findings

Full suite, release, protected parity, PR creation, exact-head CI, checker, and
delivery were intentionally not claimed because the authorized command stopped
before generation and the operator boundary forbids retry/substitution.


## History
- 2026-09-28T13:32:27Z dep_added: blocks WD-fay0
- 2026-09-28T13:33:26Z status: open -> in_progress
- 2026-09-28T13:33:26Z auto-follows: linked to predecessor WD-dc3w
- 2026-09-28T13:33:26Z claimed by dev-WD-bw0h
- 2026-09-28T14:37:04Z status: in_progress -> open
- 2026-09-28T14:37:04Z released by speed
- 2026-09-29T03:29:34Z status: open -> in_progress
- 2026-09-29T03:29:34Z auto-follows: linked to predecessor WD-p587
- 2026-09-29T03:29:34Z claimed by dev-WD-bw0h
- 2026-09-29T06:58:59Z status: in_progress -> open
- 2026-09-29T06:58:59Z released by speed
- 2026-09-29T06:59:01Z status: open -> deferred
- 2026-09-29T23:17:31Z status: deferred -> open
- 2026-09-29T23:17:50Z status: open -> in_progress
- 2026-09-29T23:17:50Z auto-follows: linked to predecessor WD-23rs
- 2026-09-29T23:17:50Z claimed by dev-WD-bw0h
- 2026-09-29T23:46:16Z status: in_progress -> open
- 2026-09-29T23:46:16Z released by speed
- 2026-09-29T23:46:28Z status: open -> deferred

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-0zj8]], [[WD-isg9]], [[WD-dc3w]], [[WD-p587]], [[WD-23rs]]

## Comments

### 2026-09-29T06:36:58Z speed
Integration-only update: merged current main 2c20caa15b12b783188d5e707e0d29dda4f5eeb7 into story/WD-bw0h after WD-23rs. No host contact, generated-command retry, model access, storage mutation, protected-engine edit, or delivery occurred.

### 2026-09-29T06:52:23Z speed
Integration CI update: story/WD-bw0h head 6900884acd6baa3d978d30dd4aae92401b8f75e8 (merge of local repair 64897225 into main 2c20caa1) completed GitHub Actions run 36531998230 successfully in 14m43s. This remains code readiness only: WD-bw0h is still in_progress/not delivered, the consumed clean-generated host attempt was not retried, and no host contact/model/storage/render action occurred.

### 2026-09-29T06:59:02Z speed
Parked as operator-gated: local repair and integration CI are complete at PR 215 head 6900884acd6baa3d978d30dd4aae92401b8f75e8, but the prior one-attempt authorization was consumed before host contact. A new explicit operator authorization is required before claim/retry; no host or model action is authorized by this status change.

### 2026-09-29T23:17:30Z speed
OPERATOR AUTHORIZATION at 2026-09-29T23:17:30Z. Verbatim user input: Authorize. Interpreted scope from the immediately prior authorization request: WD-bw0h clean-machine H3 retry at head 6900884acd6baa3d978d30dd4aae92401b8f75e8, using the existing four-model no-download manifest and only the governed one-attempt boundary.

### 2026-09-29T23:46:28Z speed
Authorized retry consumed and stopped fail-closed at STORAGE_PREPARATION_FAILED: cannot create offload root. Boundary evidence is preserved on PR 215 at head 2dfe36863e29eef02af0ea330d13d331bafdc00e. No model read/download/render, queue admission, relocation/deletion, artifact substitution, or second attempt occurred. A fresh operator authorization is required before another host attempt; this note parks the story without claiming completion.

### 2026-09-30T15:30:18Z speed
Proposed distinct storage remediation requiring operator authorization: on host 3090, verify current existence/size of the two superseded H3 checkpoints MiniMax-H3-FL2VA-pruned_int8_convrot.safetensors and MiniMax-H3-Ref2VA-pruned_int8_convrot.safetensors; create/repair a user-writable /mnt/bulk-hdd/straughter/model-offload/wangp-3090 root; record pre-move SHA-256; copy each to the offload root and verify byte size/hash before replacing/removing the original by reversible move; record post-move hashes and leave a restoration path. No deletion, unrelated asset mutation, model download, or retry is authorized by this proposal.
