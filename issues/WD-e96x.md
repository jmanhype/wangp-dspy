---
id: WD-e96x
title: "Finishing terminal disposition batch"
status: open
priority: 1
type: task
labels: [capability, finishing, evidence, external-integration]
parent: WD-3nod
created_at: 2026-09-26T20:53:07Z
created_by: speed
updated_at: 2026-09-26T20:53:07Z
content_hash: "sha256:493de39c75d8833042dba94afec49db9ff072a9ff57cb9db50fc589aca093d86"
---

## Description
## USER INTENT
The five remaining finishing cells must stop being an ambiguous backlog: run the corrected local FFmpeg film-grain graph once, and terminalize the neural and face gaps with honest, operator-approved missing-input or host-implementation boundaries rather than fabricated GPU or quality claims.

## Embedded Evidence And Scope
The five current planned cells in `docs/finishing-capabilities.md` are:

1. `ffmpeg` / `film_grain`
2. `ffmpeg` / `face_refinement`
3. `neural_frame_gen` / `interpolation`
4. `neural_frame_gen` / `spatial_upscale`
5. `neural_frame_gen` / `face_refinement`

WD-r4n8 corrected the FFmpeg graph but explicitly did not execute it. At current main, `services/finishing/pipeline.py::_film_grain_filter_graph(...)` downsamples to `ceil(width/size) x ceil(height/size)`, creates seeded held `allf=u` and reseeded `allf=t+u` branches, blends with `temporal_persistence`, scales with nearest neighbor, crops the exact frame, and adds the grain.

The immutable test source is `datasets/runs/maestro-parity/WD-r81u/inputs/source.mp4`, SHA-256 `e8b690774b0df7a73c85505ea507277d2745641b34f68c60c24855882da88859`, measured 480x832, 24 fps, duration `2.333333 s`. The film run must use current-head FFmpeg controls `strength=12.0`, `size=16`, `temporal_persistence=0.5`, and a recorded seed; it must not reuse WD-r81u's pre-correction plan.

Existing boundary evidence says:

- `neural-frame-gen-boundary-probe.txt` found no named `neural_frame_gen` implementation in WanGP; the separate H3 face refiner is a different backend and cannot be relabelled.
- The local no-GPU compiler returns typed `FINISH_NEURAL_PATH_UNAVAILABLE` and never falls back to FFmpeg/RIFE/Real-ESRGAN.
- The compass source has no human face; no track detector, normalized bounds, selected-track identity, rights, or consent exists.
- `predict/finishing.py::FaceTrack` requires non-empty `track_id`, `identity_label`, `source`, `license`, and `consent_ref` with `extra="forbid"`, so a valid consented track cannot be synthesized from the current source.

## REQUIRED OPERATOR INPUTS — NOT YET PROVIDED
This story grants no execution. The operator must separately authorize the exact local FFmpeg command/host/time boundary and explicitly approve terminal missing-input/host-boundary dispositions for the four non-run cells. No SSH, GPU, remote host, download, model use, or face input is authorized by story creation.

## OUT OF SCOPE
- Any model download, neural/GPU execution, remote SSH, provider account, new backend implementation, or substitution of FFmpeg/RIFE/Real-ESRGAN for `neural_frame_gen`.
- Inventing a face track, identity, license, consent reference, detector result, or human-faced source.
- Changing grain semantics, thresholds, queue/preflight/renderer/wiring semantics, or the already verified four finishing cells.
- Reusing WD-r81u's old `noise=alls=12:allf=t+u` output as evidence for the corrected graph.

## DIFF BUDGET
- About 2 authored files and under 250 changed LOC: `docs/finishing-capabilities.md` plus the current-head plan, local ffmpeg logs, lossless/final artifacts, measurements, typed refusals, and boundary records under `datasets/runs/maestro-parity/WD-mulc/`.
- Keep the aggregate bundle under 512 MiB and commit no model weights.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-mulc/ -> terminal five-cell finishing evidence bundle
  spec: operator decisions, current-head graph, immutable source/output hashes, ffmpeg transcripts, measured size/persistence evidence, typed neural refusals, face-input absence proof, checker results, and exact matrix citations.
- docs/finishing-capabilities.md -> terminal five-cell finishing matrix updates
  event: mark only ffmpeg film grain `host_run_verified` on real evidence and mark the other four cells with operator-approved unsupported missing-input/host-boundary labels that do not claim hardware infeasibility.

CONSUMES:
- WD-r81u: datasets/runs/maestro-parity/WD-r81u/ -> immutable source, no-face review evidence, and neural/face boundary records
  source: reuse SHA-256 `e8b690774b...` read-only; cite `missing-required-inputs.md` and `neural-frame-gen-boundary-probe.txt` without relabelling their meaning.
  (existing): services/finishing/pipeline.py -> corrected `_film_grain_filter_graph(request, width, height, frame_rate) -> str`
  spec: current graph encodes ceil-grid size, held/reseeded seeded noise branches, persistence blend, nearest-neighbor expansion, exact crop, and addition; do not alter it.
- WD-651z: docs/maestro-parity-evidence-contract.md -> `wangp-dspy.maestro-parity-evidence/v1`
  source: canonical authorization, hash, gate, disposition, and reviewer semantics; absence of an implementation is not hardware infeasibility.
- WD-651z: scripts/verify_maestro_parity.py -> `verify_bundle(bundle: Path) -> VerificationReport`
  event: checker exit 0 is required for the successful film-grain bundle and any disposition the contract accepts as terminal boundary evidence.

## Story Acceptance Criteria
1. [State] Before execution, the bundle records verbatim operator approval for the exact local FFmpeg run and explicit terminal-disposition decisions for neural/face gaps; no run starts while either approval is absent.
2. [State] The film-grain request is regenerated at the story's recorded repository commit with backend `ffmpeg`, immutable source SHA-256 `e8b690774b0df7a73c85505ea507277d2745641b34f68c60c24855882da88859`, strength `12.0`, size `16`, temporal persistence `0.5`, and a new output path; its graph contains ceil/downsample by 16, both seeded `allf=u` and `allf=t+u` branches, `all_opacity=0.5`, nearest-neighbor x16 expansion, crop to `480x832`, and addition to `[0:v]`.
3. [State] One authorized local FFmpeg execution preserves the source unchanged, records exact argv/exit/stdout/stderr, emits the lossless intermediate and final H.264 output, hashes both, and measures matching duration/dimensions/fps/pixel format plus before/after decoded-frame evidence.
4. [State] A deterministic measurement on the lossless grain intermediate proves the declared controls from actual pixels: grain support is `16x16` within the pre-registered tolerance, held/reseeded mixture behavior is consistent with temporal persistence `0.5`, and the analyzer inputs, algorithm parameters, matrices, and output hashes are retained.
5. [State] The exact graph replay is deterministic for the same source/seed on the same FFmpeg build: replay hashes or decoded-frame hashes match, and any codec-level nondeterminism is measured rather than assumed away.
6. [Unwanted] `neural_frame_gen` interpolation and spatial upscale terminalize only as operator-approved unsupported host-implementation boundaries backed by the typed `FINISH_NEURAL_PATH_UNAVAILABLE` result and zero-hit named-implementation evidence; no FFmpeg/RIFE/Real-ESRGAN output is relabelled and no hardware-infeasibility claim is made.
7. [Unwanted] The two face-refinement cells terminalize only as operator-approved unsupported missing-required-input records proving the source has no human face and every `FaceTrack` source/license/consent/identity/bounds input is absent; no synthetic consent, detector result, or identity claim is created.
8. [State] `docs/finishing-capabilities.md` mechanically updates exactly the five named cells with exact bundle citations; the four existing verified cells and all other backend dispositions remain unchanged.
9. [Unwanted] No GPU process, CUDA backend, SSH command, network/model download, dependency change, source overwrite, or protected engine change occurs; `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py` remain unchanged.
10. [State] The canonical checker accepts the film-grain success evidence and every terminal boundary disposition; backlog lint has 0 errors, full pytest JUnit has `errors=0` and `failures=0`, release verification reports `release=ready` and `tag_created=false`, and diff/protected-file checks pass.

## Testing Requirements
- Real local-process integration MANDATORY with no mocks: execute the exact current-head FFmpeg graph, capture both stages, and run the measurement analyzer against emitted bytes.
- Run no-GPU typed-request probes for neural interpolation and spatial upscale and retain exit 2 plus `FINISH_NEURAL_PATH_UNAVAILABLE`; prove no media was emitted.
- Re-verify the existing no-face frame, zero-hit named-implementation evidence, and mandatory `FaceTrack` fields; do not perform SSH or host discovery.
- Invoke the WD-651z checker on the successful and disposition evidence; parse the final matrix for exactly the five intended transitions and no collateral changes.
- Run `pvg lint --backlog`; `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-mulc-full.xml`; `uv run --frozen --extra dev wgp release verify`; `git diff --check`; and protected-file parity against the recorded base.

## Delivery Requirements
- Paste operator decisions, current-head plan/graph identity, ffmpeg command and output tails, source/intermediate/final hashes, ffprobe summaries, measurement matrices, deterministic replay result, typed refusals, face-input evidence, checker result, matrix transition, lint/JUnit/release/parity outputs, and bundle size.
- If local-ffmpeg authorization or terminal-disposition approval is absent, record only that blocker and leave all five cells planned.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored on 2026-09-26 from the current five planned finishing cells, accepted WD-r4n8 corrected graph, WD-r81u immutable source/boundary evidence, and current `FaceTrack` validation contract.

### proof
- [ ] Pending explicit local-ffmpeg authorization and operator-approved terminal dispositions.

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-3nod]]

## Comments
