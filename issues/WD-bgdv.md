---
id: WD-bgdv
title: "Clean-machine H3 generated artifact"
status: open
priority: 1
type: feature
labels: [install, evidence, external-integration, operator-decision]
parent: WD-3nod
created_at: 2026-09-28T13:27:31Z
created_by: speed
updated_at: 2026-09-28T13:27:31Z
content_hash: "sha256:2badc43601f750e79f4c5f7261b46af2638c06c6cb7b06e288d06f5818ba638a"
blocks: [WD-fay0]
follows: [WD-0zj8, WD-isg9]
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
- datasets/runs/maestro-parity/WD-clean-generated/model-assets.json -> exact four-asset `wangp-dspy.model-assets/v1` manifest
  event: every entry carries source URL, destination, exact size, SHA-256, license, and no-download/use authorization.
- datasets/runs/maestro-parity/WD-clean-generated/ -> complete generated-artifact evidence bundle
  event: stores operator authorization, storage relocation proof, clean workspace identity, exact command, resolved commit/dirty state, tool versions, host/model hashes, preflight, queue/job/retry state, native argv/log, output hash, ffprobe metadata, contact sheet/first frame, objective gate, canonical checker result, and reviewer decision.
- docs/install.md and README.md -> generated-proof command without weakening the no-GPU refusal proof
  event: clearly distinguish no-GPU install/plan, typed refusal, and this separately authorized generated-artifact mode.

CONSUMES:
- WD-0zj8: install.sh -> existing isolated `--clean-proof <dir>` no-GPU implementation
  source: extend the established isolated HOME/cache/tool/checkout behavior rather than creating a second installer.
- WD-0zj8: scripts/record_clean_machine_refusal.py -> typed `HOST_CONFIGURATION_INCOMPLETE` and `MODEL_MANIFEST_REQUIRED` refusal behavior
  source: preserve the no-authorization path unchanged; the new mode must supply complete explicit inputs before host contact.
- WD-isg9: datasets/runs/maestro-parity/WD-isg9/model-assets.json -> accepted four-asset H3 manifest schema and exact hashes
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


## History
- 2026-09-28T13:27:34Z dep_added: blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-0zj8]], [[WD-isg9]]

## Comments
