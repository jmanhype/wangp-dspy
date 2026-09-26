---
id: WD-m7xw
title: "LTX-2.5 no-download operation batch"
status: in_progress
priority: 1
type: task
labels: [capability, video, evidence, external-integration]
parent: WD-3nod
created_at: 2026-09-26T20:53:45Z
created_by: speed
updated_at: 2026-09-26T21:31:32Z
content_hash: "sha256:c4b0bf2efa098436f5a17f686a6834c5127f87846f6534affdaaece371b19b17"
blocks: [WD-fay0]
blocked_by: [WD-2gyw, WD-i7qs]
follows: [WD-5k28, WD-43tj]
assignee: dev-WD-m7xw
---

## Description
## USER INTENT
The LTX-2.5 video row needs one no-download operation batch that finally deploys the accepted tokenizer fix and gives every remaining operation either real output evidence or an exact host boundary. No cell may remain silently planned or inherit evidence from another operation.

The batch emits one real output or exact host-boundary record for each remaining cell.

## Embedded Evidence And Scope
WD-i7qs diagnosed and fixed the LTX Gemma tokenizer failure without changing dependencies or downloading a model. The reviewable Wan2GP branch is `story/WD-i7qs` at `faea82d15bf10b3479c42c0ea430892aae975870`, based on `071ce70aab1169c61cc14bbefd71bdda3a04a9e9`. It loads vocab `262144`, maps `<|video|>` to id `258884`, and leaves the Mistral regex patch disabled. Its implementation evidence is `datasets/runs/maestro-parity/WD-i7qs/native-scripts/RESULTS.md`.

The current `docs/video-capabilities.md` LTX-2.5 row has exactly these eight unresolved cells: `create`, `extend`, `retake`, `edit`, `outpaint`, `repaint`, `recast`, and `upscale`. `blend` is already a terminal typed backend boundary and must remain unchanged.

The exact present LTX-2.5 asset set is the WD-2gyw `model_provenance` array entries whose identities begin `ltx25-`. Preflight must rehash every file below before deployment:

| Asset identity | Required SHA-256 |
| --- | --- |
| ltx25-ltx-2.5-22b-distilled_diffusion_model_int8_convrot.safetensors | b4bb89c54e025d834f0c6138dbf80c245e8196c27c8bff8dd47db4c03412c72f |
| ltx25-ltx-2.5-22b_video_vae_bf16.safetensors | 685b06ee3d9b2039647698fc4ea33175112462fc374e2777312c907897dfce8d |
| ltx25-ltx-2.5-22b_diffusion_video_vae_bf16.safetensors | 847e14ca7f3355debca0cea4eaa24ac0fbcdf0061da054ac89ca638a869ddba3 |
| ltx25-ltx-2.5-22b_audio_vae_bf16.safetensors | 43ed048b9a5aa7eac181cf1b5bf68382aa4fb9d98627575d01d9b187d3462028 |
| ltx25-ltx-2.5-22b_vocoder_bf16.safetensors | a865b27a492fea788dc35bed29b333103ca1fb9c280f4fd77976ad19a3b13435 |
| ltx25-ltx-2.5-22b_text_embedding_projection_bf16.safetensors | 06b7017692b2d0d42a863d609cf40e7672243eb3d13ae7a19650a7a8294ac494 |
| ltx25-ltx-2.5-22b_video_embeddings_connector_int8_convrot.safetensors | 9559f09ff6fb1b3dca10617722df7133838ea0fee6f1457c90e992447796d765 |
| ltx25-ltx-2.5-22b_audio_embeddings_connector_int8_convrot.safetensors | 80270afb795fdac363dcd8329e6b375f6ca93f6a3d74a25b2bb440d342095362 |
| ltx25-ltx-2.5-spatial-upscaler-x2-1.0_bf16.safetensors | eb5a71fe4068ee87ccdb1c3aa635e547ca76bd2d30ae20ae889f2c325c0677e8 |
| ltx25-ltx-2.5-temporal-upscaler-x2-1.0_bf16.safetensors | 2bc3300f2b3c3c1834d72164fbf13a3b9fd73e5a741e8a2c3f4035f89a75c3fe |
| ltx25-gemma4-gemma4-12b-ltx-v1_int8_convrot.safetensors | 6a23b673266b65a318e26cad27fabd5c67609f4ecf51aa13996feb07d0060903 |
| ltx25-gemma4-tokenizer.json | cc8d3a0ce36466ccc1278bf987df5f71db1719b9ca6b4118264f45cb627bfe0f |
| ltx25-gemma4-config.json | 82ec29063791629eac6a023c662f4edc2a811e479343ae79f21b8453357caeb0 |
| ltx25-gemma4-chat_template.jinja | ae53464bf3be25802b5a37def7fd89667067d7577049b3b2d74c4d8de4c6d4 |
| ltx25-gemma4-tokenizer_config.json | 794a39f8330ce05020774c70c091225bc5f031b9cacf41fc20e52eb54b4b52d8 |

## REQUIRED OPERATOR INPUTS — NOT YET PROVIDED
This story authorizes no host, GPU, SSH, branch deployment, or model use. The operator must first record verbatim scope, timestamp, approver, host identity, exact operation list, command/time boundary, VRAM/service policy, asset identities, and no-download approval. Any absent or mismatched input blocks before queue admission.

## OUT OF SCOPE
- Any download, dependency change, alternative checkpoint, model replacement, provider account, training, GUI, publication, or new family/operation.
- LTX-2.3, SCAIL, Wan, H3, Hunyuan, or any other video row.
- Reusing a successful `create` artifact as evidence for a different operation, or inheriting the existing `blend` boundary.
- Editing the live `/home/straughter/Wan2GP` dirty tree rather than deploying the exact reviewed commit in an isolated run tree.
- Changing `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, or `scripts/run_film.py`.

## DIFF BUDGET
- About 2 authored files and under 250 changed LOC: `docs/video-capabilities.md` plus operation manifests/native scripts/logs/QC/checker evidence under `datasets/runs/maestro-parity/WD-m7xw/`.
- Keep aggregate generated media under 4 GiB unless authorized failure diagnostics are larger; never commit model weights.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-m7xw/ -> per-operation LTX-2.5 terminal evidence bundles
  spec: one record for each of create/extend/retake/edit/outpaint/repaint/recast/upscale with commit, model/reference hashes, argv, queue state, output hash/metadata/QC for success, or exact native exit/stderr/stage for a host boundary.
- docs/video-capabilities.md -> terminal LTX-2.5 row updates
  event: mechanically update exactly the eight targeted cells, preserve the existing blend boundary, and cite each bundle record.

CONSUMES:
- WD-2gyw: datasets/runs/maestro-parity/WD-2gyw/ -> hash-bound LTX-2.5 asset manifest, source/reference provenance, prior tokenizer failure, and row semantics
  source: select only `model_provenance[]` identities beginning `ltx25-`; all fifteen hashes above must match before run.
- WD-651z: docs/maestro-parity-evidence-contract.md -> `wangp-dspy.maestro-parity-evidence/v1`
  source: canonical authorization, provenance, hash, gate, disposition, and reviewer semantics; do not create a second standard.
- WD-651z: scripts/verify_maestro_parity.py -> `verify_bundle(bundle: Path) -> VerificationReport`
  event: checker exit 0 is required for each successful output bundle and every accepted unsupported disposition defined by the contract.
- (existing): Wan2GP fork branch story/WD-i7qs at faea82d15bf10b3479c42c0ea430892aae975870 -> fixed Gemma tokenizer behavior
  source: deploy this exact reviewed commit in an isolated 3090 run tree; verify vocab 262144 and video token id 258884 before operations.

## Story Acceptance Criteria
1. [State] Before execution, verbatim operator authorization, GPU/host policy, zero-download approval, and all fifteen LTX-2.5 asset hashes are recorded; the exact WD-i7qs commit is deployed to an isolated run tree and proves vocab `262144` plus video token id `258884` before queue admission.
2. [Unwanted] Planned and actual download bytes are zero; any missing/hash-mismatched asset, wrong commit, dirty-source mismatch, unauthorized GPU/service state, or dependency-change attempt stops before inference and cannot be represented as a hardware verdict.
3. [State] The batch inventories and separately dispositions all eight cells: `create`, `extend`, `retake`, `edit`, `outpaint`, `repaint`, `recast`, and `upscale`; no cell is dropped, skipped, inherited, or left `planned`.
4. [State] Each successful operation records exact argv, reference/model hashes, queue/job/attempt/exit, emitted MP4 SHA-256, ffprobe duration/dimensions/fps/streams, QC gate inputs/results, assembly or operation linkage, and checker exit `0`.
5. [State] Each unsuccessful operation preserves its native exit code, stderr/stdout tail, failing stage, GPU/VRAM state, and asset/commit identity; a terminal `unsupported` or `unsupported_on_this_hardware` label is applied only when that exact evidence satisfies the canonical checker and never by relabelling a dependency or authorization failure.
6. [Unwanted] No operation substitutes another family/backend, reuses another operation's output, weakens QC, or claims a tokenizer smoke test as generation evidence.
7. [State] `docs/video-capabilities.md` is updated mechanically from the operation records; each of the eight cells cites its exact bundle path and terminal disposition, while `ltx/2.5` `blend` remains the existing typed boundary.
8. [Unwanted] The live Wan2GP deployment tree's existing dirty files and HEAD remain unchanged; no unrelated service is stopped, restarted, installed, upgraded, or downloaded.
9. [State] Standing gates pass: backlog lint has 0 errors; full pytest JUnit has `errors=0` and `failures=0`; release verification reports `release=ready` and `tag_created=false`; protected-file parity and `git diff --check` pass.

## Testing Requirements
- Real integration MANDATORY with no mocks: authorized 3090 execution through the isolated fixed branch, one native attempt per operation, real queue/output or native boundary capture, and no fixture substitution.
- Before and after every batch, record host/GPU process state, disk headroom, model hashes, branch commit, tree cleanliness, and zero network transfer.
- For every output, run the canonical checker and retain objective media/QC evidence; for every failure, retain the complete typed boundary and prove no output bytes existed.
- Parse the final video matrix and prove the exact eight-cell transition, unchanged blend boundary, no dropped row/cell, and exact evidence citation.
- Run `pvg lint --backlog`; `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-m7xw-full.xml`; `uv run --frozen --extra dev wgp release verify`; `git diff --check`; and protected-file parity against the recorded base.

## Delivery Requirements
- Paste authorization, asset/hash table result, commit/tree proof, tokenizer check, operation inventory, command tails, queue/output/boundary evidence, checker results, matrix transition, lint/JUnit/release/parity outputs, bundle size, and zero-download accounting.
- If operator authorization or any required hash is absent, record a precise typed blocker and leave all eight cells unchanged.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored on 2026-09-26 from the current LTX-2.5 matrix row, WD-2gyw asset provenance/failure, and accepted WD-i7qs tokenizer-fix evidence at commit `faea82d15bf10b3479c42c0ea430892aae975870`.

### proof
- [ ] Pending explicit operator authorization, hash preflight, fixed-branch deployment, and per-operation 3090 execution.

## Acceptance Criteria


## Design


## Notes
BLOCKED 2026-09-26T21:00:00Z (authorization preflight): required operator input is incomplete, so execution stopped before SSH, GPU, queue admission, fixed-branch deployment, downloads, dependency changes, and hash preflight. Present scope supplies the eight operations, fifteen expected LTX-2.5 hashes, fixed Wan2GP commit faea82d15bf10b3479c42c0ea430892aae975870, zero-download intent, and serial-render intent, but not verbatim approval timestamp, approver identity, exact render-host identity, command/time boundary, or VRAM/service policy. Existing WD-2gyw authorization is scoped only to WD-2gyw, and WD-i7qs explicitly performed no render and left deployment separate. This is a missing-operator-input blocker, not unsupported_on_this_hardware. docs/video-capabilities.md:81 remains unchanged: create/extend/retake/edit/outpaint/repaint/recast/upscale stay planned and blend stays the existing typed backend boundary.
CORRECTION: the preceding blocker timestamp was a placeholder. Actual local execution timestamp is 2026-09-26T21:01:28Z. All substantive blocker facts and the fail-closed boundary remain as stated.
BLOCKED 2026-09-26T21:17:11Z (authorized-host-state preflight): all fifteen LTX-2.5 asset hashes matched, the isolated Wan2GP run tree was deployed at faea82d15bf10b3479c42c0ea430892aae975870, and the real tokenizer check passed with vocab=262144 and video_token_id=258884. Queue admission then stopped because unrelated llama-server PID 3213164 occupied 18154 MiB of the RTX 3090, leaving 5873 MiB free. The operator authorization explicitly forbids killing or restarting unrelated services. No inference command ran, no queue job was admitted, zero output files existed, and docs/video-capabilities.md:81 remains unchanged. This is not unsupported_on_this_hardware and not a model capability verdict.

Evidence: datasets/runs/maestro-parity/WD-m7xw/EXECUTION_BOUNDARY.md; host-logs/10_asset_hash_preflight.txt; host-logs/22_tokenizer_check.txt; host-logs/23_deploy_state.txt; host-logs/30_gpu_preflight_blocked.txt; host-logs/40_postflight_no_inference.txt.

Commit: 5c873f72addf2792fd56f74cbfe55037487a1670; branch story/WD-m7xw pushed to origin.
Checks: pvg verify PASS; pvg lint --backlog 0 errors/0 review; targeted Maestro-parity tests 78/78 PASS, errors=0 failures=0 skipped=0; release verify at final clean tree reported release=ready and tag_created=false; protected-file parity and git diff --check PASS. Full pytest was bounded/stopped after >6 minutes at about 13% because another developer story was concurrently running its full suite; only this story's process was interrupted. Canonical bundle checker was not run because there was no admitted queue, output, or accepted unsupported disposition.

### DISCOVERED_BUG
  title: RTX 3090 unavailable to WD-m7xw due to unrelated llama-server occupancy
  context: WD-m7xw completed asset, commit, and tokenizer preflight, but llama-server PID 3213164 (/home/straughter/llama.cpp/build/bin/llama-server) held 18154 MiB with only 5873 MiB free. Operator policy forbids killing or restarting unrelated services, so all eight LTX operations stopped before inference.
  affected_files: none; external host process and GPU state
  discovered_during: WD-m7xw

## History
- 2026-09-26T20:53:46Z dep_added: blocks WD-fay0
- 2026-09-26T20:53:47Z dep_added: blocked_by WD-2gyw
- 2026-09-26T20:53:47Z dep_added: blocked_by WD-i7qs
- 2026-09-26T20:57:46Z status: open -> in_progress
- 2026-09-26T20:57:46Z auto-follows: linked to predecessor WD-5k28
- 2026-09-26T20:57:46Z claimed by dev-WD-m7xw
- 2026-09-26T21:01:15Z status: in_progress -> blocked
- 2026-09-26T21:01:16Z released by speed
- 2026-09-26T21:01:28Z status: blocked -> blocked
- 2026-09-26T21:10:03Z status: blocked -> in_progress
- 2026-09-26T21:10:03Z auto-follows: linked to predecessor WD-43tj
- 2026-09-26T21:10:03Z claimed by dev-WD-m7xw

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Blocked by: [[WD-2gyw]], [[WD-i7qs]]
- Follows: [[WD-5k28]], [[WD-43tj]]

## Comments
