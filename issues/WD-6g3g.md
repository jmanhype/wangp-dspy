---
id: WD-6g3g
title: "Director no-download source-pairing rework"
status: open
priority: 1
type: task
labels: [capability, evidence, director, external-integration]
parent: WD-3nod
created_at: 2026-09-26T20:53:07Z
created_by: speed
updated_at: 2026-09-26T20:53:07Z
content_hash: "sha256:835f1826e544a8265d56356de5757f0fa151ff5051de9c40f555c0d2938d6e48"
blocks: [WD-fay0]
---

## Description
## USER INTENT
The director lane needs a no-download source-selection rework that fixes the media-specific clip-1 failures without rewriting history, weakening a gate, or consuming another download. The operator needs either a checker-valid reworked director bundle or a fail-closed stop that leaves the matrix honest.

The rework emits a checker-valid bundle or a typed blocker; it never mutates the failed baseline.

## Embedded Evidence And Diagnosis
The immutable failed baseline is the accepted WD-dmf2 bundle. Its raw QC record contains:

- Screenplay clip 1 Whisper score `0.556` against pass bar `0.6`; the utterance was approximately 5.2 seconds of speech, but the produced clip cut speech to 3.5 seconds.
- Audio clip 1 SyncNet confidence `0.594741` against pass bar `1.0`; the selected speech-bearing video was paired with instrumental audio rather than its matching speech audio.
- Screenplay clip 1 SyncNet confidence `0.468897` against pass bar `1.0`; the visual was a static zoompan and therefore was not valid speech-motion evidence.
- Screenplay clip 2 Whisper `1.000` and SyncNet `1.10503` prove the existing thresholds are reachable; threshold weakening is prohibited and unnecessary.

The primary synchronized speech pair is the existing WD-cpow pair, already copied byte-identically into WD-dmf2:

- Speech guide: `datasets/runs/maestro-parity/WD-cpow/outputs/wd_cpow_vibevoice_raw.prepared.wav`, SHA-256 `e371ebe7ee1ce9964657b4f34f61d32fbff2a5345bdb90add6c3e7dba1ee2175`, measured duration `2.333333 s`, 24 kHz mono.
- Matching speech video: `datasets/runs/maestro-parity/WD-cpow/outputs/wd_cpow_vibevoice_revoice.mp4`, SHA-256 `1cdac314c38142e15af22e1122a3df8177a5e2027b9a7fcde5807e13c8c407d3`, 704x576 at 24 fps; video and audio both measure `2.333333/2.333 s`.

The instrumental `wd_rous_ace_generate.wav` (SHA-256 `6ee782ec4f8ea86fa531669ee1c762d7a5d9685ab7e08bf6dd74d84abf3868a9`) may be used only for an explicitly non-speech instrumental target. It must never be paired with a speech video for Whisper or SyncNet evidence.

Required local model identities are unchanged from WD-dmf2 and must be rehashed before any run:

- Whisper small: `9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794`
- Qwen vision text model: `3445102e9cde5d562508642c100a2f5ac3368a5a3f748442811d7a95daee3bec`
- Qwen vision projector: `add205b7bfdb3f71f6da36b0a82aa20928dd829a920878c602628cdfbebc5288`
- SyncNet v2: `961e8696f888fce4f3f3a6c3d5b3267cf5b343100b238e79b2659bff2c605442`

## REQUIRED OPERATOR INPUTS — NOT YET PROVIDED
This story authorizes nothing. Before execution the operator must supply verbatim scope, timestamp, approver, exact host and command boundary, rights boundary, stop/failure boundary, model identities above, and explicit approval for no-download rework execution. A run is blocked if any required input is absent; missing authorization is neither infeasibility nor success.

## OUT OF SCOPE
- Editing, deleting, regenerating, or appending inside `datasets/runs/maestro-parity/WD-dmf2/`; it is immutable baseline evidence.
- Any model download, dependency change, provider account, training, publication, GUI, extra capability row/cell, rights bypass, or threshold change.
- Replacing a failed speech gate with an instrumental/non-applicable disposition, static zoompan, trimmed transcript, fixture, or prose explanation.
- Changing `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, or `scripts/run_film.py`.

## DIFF BUDGET
- About 2 authored files and under 250 changed LOC: `docs/director-capabilities.md` plus manifests, scripts, logs, measurements, and evidence under `datasets/runs/maestro-parity/WD-gqlc/`.
- Keep the aggregate new bundle under 2 GiB unless an authorized failure log is larger. Do not copy model weights or mutate WD-dmf2.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/WD-gqlc/ -> checker-valid no-download director rework bundle
  spec: immutable baseline hash, authorization, zero-download preflight, model hashes, source-pair derivation, new request/plan/output hashes, queue attempts, raw Whisper/vision/mouth-box/SyncNet evidence, mechanically derived gates, checker result, and reviewer decision.
- docs/director-capabilities.md -> evidence-backed director-row updates
  event: update only cells supported by this bundle, cite the exact record, and leave every failed or unauthorized cell unchanged.

CONSUMES:
- WD-dmf2: datasets/runs/maestro-parity/WD-dmf2/ -> immutable failed baseline, raw QC, planned-produced map, model identities, and gate derivation
  source: copy inputs by hash into a new namespace; never mutate the predecessor bundle.
- WD-cpow: datasets/runs/maestro-parity/WD-cpow/ -> synchronized speech audio/video pair and measured stream metadata
  source: use SHA-256 `e371ebe7...` and `1cdac314...` as the primary speech pair; do not pair the speech video with instrumental audio.
- WD-651z: docs/maestro-parity-evidence-contract.md -> `wangp-dspy.maestro-parity-evidence/v1`
  source: canonical authorization, provenance, hash, disposition, gate, and reviewer fields; do not duplicate or weaken it.
- WD-651z: scripts/verify_maestro_parity.py -> `verify_bundle(bundle: Path) -> VerificationReport`
  event: invoke the accepted checker and require exit 0 before any `host_run_verified` transition.

## Story Acceptance Criteria
1. [State] Before execution, the bundle records verbatim operator authorization and proves the WD-dmf2 bundle is immutable by recording its base commit/content identity and a clean before/after parity check for `datasets/runs/maestro-parity/WD-dmf2/`; all new bytes are written only under this story's namespace.
2. [Unwanted] A no-download preflight proves zero planned and actual network/model-download bytes, rejects any absent or hash-mismatched model listed above before queue admission, and records no dependency, provider, or model-fetch mutation.
3. [State] The speech source plan preserves the complete measured utterance: the selected speech guide and speech video have matching identities/durations, and the produced speech window is at least the measured full-utterance duration; the 5.2-second-to-3.5-second cut cannot recur.
4. [State] Audio-mode evidence uses the WD-cpow synchronized speech pair as the primary source; instrumental audio is used only for a declared non-speech target and never with a speech video.
5. [State] Screenplay clip-1 evidence uses motion-bearing speech video; a static zoompan visual is rejected as incapable of supporting the speech SyncNet gate.
6. [State] Every applicable reworked clip records raw pre/post Whisper, identity-vision action/speaker scores, three-frame mouth-box consensus, and multicrop SyncNet evidence. The unchanged bars are Whisper `>=0.6`, identity action/speaker `>=0.7`, mouth center spread `<=0.03` normalized on each axis, SyncNet confidence `>=1.0`, and absolute offset `<=10` frames at 25 fps.
7. [Unwanted] Objective-gate values are mechanically derived from the raw QC evidence rather than hardcoded; any failed, inapplicable, unauthorized, missing, or reviewer-pending gate leaves the affected row/cell unchanged and the checker fail-closed.
8. [State] A successful delivery has checker exit `0`, every applicable objective gate `pass`, and an explicit approved reviewer decision; `docs/director-capabilities.md` changes only mechanically from the bundle and cites the exact new evidence record.
9. [Unwanted] No threshold, queue, preflight, renderer, wiring, or protected engine semantic changes; no WD-dmf2 mutation; no fabricated score, approval, hardware verdict, or inherited WD-cpow/WD-dmf2 output claimed as this story's output.

## Testing Requirements
- Real integration MANDATORY with no mocks: authorized no-download host execution, exact command tails, source and output hashes, queue admission/exit, raw media metadata, all QC inputs/outputs, checker transcript, and matrix-transition proof.
- Verify all copied source hashes before and after execution, including the synchronized pair and any WD-dmf2 input reused.
- Mechanically compare raw QC fields to each objective gate; do not substitute a derived summary for raw evidence.
- Run `pvg lint --backlog`; `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-gqlc-full.xml` with parsed JUnit `errors=0` and `failures=0`; `uv run --frozen --extra dev wgp release verify` with `release=ready` and `tag_created=false`; protected-file parity against the recorded base; `git diff --check`; and the WD-651z checker.

## Delivery Requirements
- Paste authorization, base identity, zero-download/model preflight, source-pair table, commands, queue transitions, hashes, metadata, raw gate tables, derivation rule, checker result, reviewer decision, lint/JUnit/release/parity outputs, bundle size, and final matrix delta.
- If authorization, rights, a hash-matched model, a synchronized source, or a required gate input is absent, stop and record that exact blocker without flipping a cell.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored on 2026-09-26 from immutable WD-dmf2 raw QC, the synchronized WD-cpow pair, current WD-fay0/WD-t0il scope records, and the operator-supplied scout diagnosis embedded above.

### proof
- [ ] Pending explicit operator authorization and no-download rework execution.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-09-26T20:53:08Z dep_added: blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]

## Comments
