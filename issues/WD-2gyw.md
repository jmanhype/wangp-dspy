---
id: WD-2gyw
title: "Video breadth generation evidence"
status: in_progress
priority: 1
type: feature
labels: [capability, evidence, external-integration]
parent: WD-3nod
created_at: 2026-09-24T14:14:06Z
created_by: speed
updated_at: 2026-09-25T14:15:04Z
content_hash: "sha256:079df7f4cc2b926e7f94927cd07f39520e747b278dde1ef66baa239a07a31740"
blocks: [WD-bxhc, WD-r81u, WD-dmf2, WD-fay0]
assignee: dev-WD-2gyw
follows: [WD-cpow]
---

## Description
## USER INTENT
The eleven `planned` family/preset rows in `docs/video-capabilities.md` must reach evidence-backed terminal dispositions without pretending that planning breadth is generation breadth. The rows are `minimax_h3/standard`, `minimax_h3/h3_vdn_hybrid_attention`, `minimax_h3/taomate_three_step`, `minimax_h3/kfi_frames_injection`, `minimax_h3/h3_outpaint`, `minimax_h3/h3_audio_refinement`, `ltx/2.5`, `ltx/2.3`, `scail/2`, `wan/2gp`, and `hunyuan/standard`.

Progress is grouped and checkpointed independently by model family so completed families are never rolled back because another family fails: MiniMax H3 standard; the five specialized H3 presets; LTX 2.5/2.3; SCAIL 2; Wan 2gp; and Hunyuan standard. The initial feasibility expectation, not a verdict, is that `minimax_h3/standard` and `wan/2gp` are the likeliest candidates on the existing H3/Wan2GP render path. Every H3 specialized preset and every LTX, SCAIL, and Hunyuan row is at risk until its exact model requirement and an authorized attempt are recorded.

Every currently `planned` executable family/operation cell must end as `host_run_verified` from a real authorized bundle under `datasets/runs/maestro-parity/WD-2gyw/`, or as `unsupported_on_this_hardware` with recorded infeasibility evidence. The four pre-existing typed backend boundaries — LTX blend, SCAIL outpaint, SCAIL upscale, and Hunyuan outpaint — remain explicitly non-hardware implementation boundaries; they must not be relabelled as hardware infeasibility.

## REQUIRED OPERATOR INPUTS — NOT YET PROVIDED
- Per-family/preset and per-batch GPU/render-host authorization has NOT been given by this story.
- Model-download approval has NOT been given by this story.
- A complete model manifest with each family/preset identity, immutable hash or version, source, license and explicit acceptance, parameter count or equivalent size, quantization where applicable, and declared VRAM requirement is required and has NOT been supplied.
- The bundle must record authorization verbatim, including scope, timestamp, approver, exact command boundary, render-host identity, measured 24 GiB VRAM ceiling, model/download approval, and failure/stop boundary.
- Missing authorization, missing download approval, or a missing model manifest is a blocked input. It is not infeasibility and must never become `unsupported_on_this_hardware`.

## No-Fabrication Rule
Vendor documentation, capability lists, configuration, normalized settings, deterministic plans, durable planning records, model manifests, unit tests, dry-runs, reconstruction output, queue planning, and absence of an attempt are never generation evidence. `host_run_verified` requires actual emitted video bytes from an authorized run. `unsupported_on_this_hardware` requires recorded evidence: an actual authorized refusal or failed attempt tied to the model requirement, or a recorded requirement — parameter count, quantization, or declared VRAM — that provably exceeds the measured 24 GiB host capacity. A missing model, missing authorization, disk shortage, unrelated worker bug, or typed backend rejection never qualifies as hardware infeasibility.

Any multi-clip, reference-conditioned, or continuity claim must record a concrete identity anchor and hashes, not prose: ordered clip IDs; every reference and source SHA-256; recipe seed and canonical settings hash; operation and overlap/window policy; model and LoRA hashes; every emitted clip and assembled output SHA-256; and the assembly/recipe digest. A continuity assertion without these matching values fails.

## OUT OF SCOPE
- A GUI, registry publication, training run, new renderer, or provider account.
- Adding model families/presets or operations beyond the eleven named rows and their existing matrix cells.
- Reusing an image, music, voice, SFX, finishing, or install artifact as this lane's video evidence.
- Silently dropping a row/cell, weakening a QC gate, changing the WD-651z contract, or converting the four typed backend boundaries into hardware verdicts.
- Changing queue admission, renderer policy, preflight, wiring, or `scripts/run_film.py` semantics.

## DIFF BUDGET
- Authored text is about 2 files and under 350 changed LOC: `docs/video-capabilities.md` plus manifests/diagnostics under `datasets/runs/maestro-parity/WD-2gyw/`.
- Generated evidence is bounded to the shortest governed clip needed for each required verdict, its references, logs, measurements, and metadata; no model weights are committed. Record aggregate bundle size and keep it under 4 GiB unless recorded authorized-failure diagnostics are larger.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-2gyw/ -> `wangp-dspy.maestro-parity-evidence/v1` video family bundles
  spec: independently reviewable sub-bundles grouped by model family/preset and operation, with authorization, exact argv, commit/dirty state, model and LoRA provenance, reference hashes, queue attempt, output hashes, ffprobe metadata, QC/assembly linkage, 24 GiB infeasibility evidence where applicable, identity anchor, and reviewer verdict.
- docs/video-capabilities.md -> evidence-backed terminal family/operation matrix
  event: update exactly the eleven named rows from bundle contents, cite each verdict's exact bundle record, preserve the four distinct typed backend boundaries, and drop no row or cell.

CONSUMES:
- WD-651z: docs/maestro-parity-evidence-contract.md -> `wangp-dspy.maestro-parity-evidence/v1`
  source: sole canonical authorization, provenance, hash, metadata, gate, disposition, and reviewer field contract; this lane must not duplicate or weaken it.
- WD-651z: scripts/verify_maestro_parity.py -> `verify_bundle(bundle: Path) -> VerificationReport`
  event: the accepted checker must exit zero for every generation bundle and every contract-defined unsupported-hardware disposition bundle used to flip this matrix.
- (existing): docs/video-capabilities.md -> current eleven-row video matrix
  source: exact family/preset identities, operation/reference rules, LoRA/timecode contract, and the four typed backend rejections.
- (operator): explicit per-batch GPU authorization, model-download approval, complete model manifest, and render-host identity -> verbatim authorization and host-capacity record
  source: future operator input; not supplied by story creation.

## Story Acceptance Criteria
1. [State] Given explicit authorization, download approval, a complete model manifest, and a successful run, a video cell flips to `host_run_verified` only when its emitted video bytes, model/LoRA/reference provenance, queue attempt, output hashes, ffprobe metadata, QC result, and assembly/recipe linkage are present in a family bundle that passes the accepted WD-651z checker.
2. [Unwanted] Given absent, blank, partial, mismatched, or unauthorized input or evidence, the affected family/cell remains non-verified and is neither dropped nor silently flipped to verified.
3. [State] A family/cell becomes `unsupported_on_this_hardware` only from an authorized captured refusal/failed attempt or a recorded parameter/quantization/VRAM requirement that provably exceeds the measured 24 GiB host capacity, with that proof checker-validated according to the accepted WD-651z disposition contract.
4. [State] LTX blend, SCAIL outpaint, SCAIL upscale, and Hunyuan outpaint are recorded as distinct typed backend/operation boundaries with exact failure diagnostics; none is represented as `host_run_verified` or `unsupported_on_this_hardware`.
5. [State] Every currently `planned` executable cell in all eleven rows reaches `host_run_verified` or `unsupported_on_this_hardware`; every targeted row/cell remains present and cites the exact bundle/evidence record from which its disposition came.
6. [State] Every multi-clip or continuity claim records the complete identity anchor and all source/reference/output/assembly hashes and recipe values named in the No-Fabrication Rule, and the bundle fails if those values do not match.
7. [State] Family groups can be completed and reviewed independently: a completed `minimax_h3/standard`, Wan, or other family bundle remains valid evidence while a later family is blocked, fails, or is proven unsupported.
8. [Unwanted] No GUI, publication, training run, unauthorized download, extra row/cell, model-weight commit, reused foreign artifact, QC-gate bypass, or protected engine change occurs; `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py` remain unchanged from accepted base `40f8c2b373dec1c84ca5a596c821b740934af6fb`.

## Testing Requirements
- Before generation, record verbatim authorization/download approval and verify exact argv, commit/dirty state, family/preset, model identity/source/hash/license/parameter count/quantization/declared VRAM, reference and LoRA hashes, operation, seed, overlap/window policy, dimensions, steps, fps, and output target.
- For every emitted clip and assembled result, record SHA-256 and measured ffprobe dimensions, duration, frame rate, stream layout, and audio properties; retain the queue/job/retry identity, exact failure tails, objective QC inputs/thresholds/measured values, and reviewer decision.
- For every hardware-infeasible disposition, record the measured host capacity and either the authorized refusal/failure output or the model requirement arithmetic that exceeds it; invoke the accepted WD-651z checker in its unsupported-evidence mode and do not flip the cell if that mode is unavailable or fails.
- Parse the final matrix and prove all eleven row identities, every planned-cell transition, every citation, the four unchanged backend boundaries, no dropped cells, and no row left `planned`.
- Standing gates: `pvg lint --backlog` reports 0 errors and 0 review findings; `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-2gyw-full.xml` has parsed JUnit `errors=0` and `failures=0`; `uv run --frozen --extra dev wgp release verify` reports `release=ready`/`tag_created=false`; and `git diff --exit-code 40f8c2b373dec1c84ca5a596c821b740934af6fb -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`.
- Also run `git diff --check`, record aggregate bundle size, and record every family/cell transition and infeasibility calculation.

## Delivery Requirements
- Paste authorization provenance without inventing approval, exact command and failure tails, model/host requirement arithmetic, hashes, ffprobe metadata, queue identities, identity anchors, checker output, lint result, parsed JUnit counters, release fields, protected-file parity, bundle size, and the final eleven-row matrix.
- If required operator input remains absent, report the affected family as blocked on that input; do not substitute plans, dry-runs, normalized settings, vendor claims, or unsupported assertions for generation evidence.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored on 2026-09-24 from the eleven planned rows and typed backend boundaries in `docs/video-capabilities.md:37-87`; operator GPU/download approvals and the complete model manifest remain outstanding.

### proof
- [ ] Pending implementation and explicit operator authorization.

## Acceptance Criteria


## Design


## Notes
## MANDATORY SKILLS
- pvg

Observable outcome: an explicitly authorized future run emits hashed breadth-case video artifacts and metadata under datasets/runs/maestro-parity/WD-2gyw/; no GPU batch is authorized by this story and no generation result is claimed without that bundle.

## History
- 2026-09-24T14:14:06Z dep_added: blocks WD-bxhc
- 2026-09-24T14:14:06Z dep_added: blocks WD-r81u
- 2026-09-24T14:14:07Z dep_added: blocks WD-dmf2
- 2026-09-24T14:14:08Z dep_added: blocks WD-651z
- 2026-09-24T14:14:09Z dep_added: blocks WD-fay0
- 2026-09-24T14:39:54Z dep_removed: no_longer_blocks WD-651z
- 2026-09-25T14:15:04Z status: open -> in_progress
- 2026-09-25T14:15:04Z auto-follows: linked to predecessor WD-cpow
- 2026-09-25T14:15:04Z claimed by dev-WD-2gyw

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-bxhc]], [[WD-r81u]], [[WD-dmf2]], [[WD-fay0]]
- Follows: [[WD-cpow]]

## Comments
