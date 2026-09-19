---
id: WD-rij6
title: "LF003 full-gate four-cut chain-depth probe"
status: in_progress
priority: 0
type: feature
parent: WD-j9nx
created_at: 2026-09-19T13:07:14Z
created_by: speed
updated_at: 2026-09-19T14:57:39Z
content_hash: "sha256:5b4a56a4379eb31bf49fa8d7c0e552c39384c53ca3dd120898943c9968bbe40b"
assignee: dev-WD-rij6
follows: [WD-ice0, WD-clms]
labels: [delivered]
---

## Description
## Context (Embedded)

This is the operator-authorized next film-lane story after acceptance of the
LF003 “Borrowed Sunrise” two-cut candidate.

### Accepted entry artifact

- Repository baseline for this story: `35201a11bb1839fd5ba83739eed690227aabe199`.
- Run ID: `lf003-two-cut-vibevoice-rhostrong-20260918`.
- Premise: `lf-003`.
- Assembled artifact:
  `datasets/runs/pull/lf003-two-cut-vibevoice-rhostrong-20260918/assembled.mp4`.
- Assembled SHA-256:
  `1c1184fbcf504ffbc4657926e13d20c6dd039e41dcf54bfe6e61919032b21ad`.
- Acceptance bundle SHA-256:
  `df9012a3dcd2819d73ccacc9f7dbf9754c4a298a58869079424b46c611bdb361`.
- Source run records:
  - planned record SHA-256:
    `4c08dfe429499fc38bd20d0e9796b4d4d9ae06c4cd417bc1748b3b8c3969e502`
  - needs-review record SHA-256:
    `92180c776a820a58a3f725aa9e92308aba84f67c4dd1c1585853ba2537cbe996`
- Operator authorization: on 2026-09-19 the operator replied
  `i agree to everything you may continue on all fronts` after viewing the
  candidate. Treat this as acceptance of the two-cut entry artifact and
  authorization for the four-cut probe.

### Why this story exists

The original six-cut contract remains unmet. Historical depth-five evidence
predates the corrected native conditioning path. The current two-cut LF003 run
is the first mechanically eligible full-gate candidate under the current stack.
The next safe increment is exactly four cuts—not six and not latent carry yet.

## USER INTENT

Prove whether the current native-H3, VibeVoice, full-gate pipeline can preserve
identity, composition, speaker attribution, and audiovisual sync through cut 4
without changing premise, cast, style, duration policy, or QC thresholds.

## Goal

Produce a fresh, clean-checkout, no-prefix, one-queue, one-ledger four-cut
LF003 run through the repository-owned acceptance path, then submit the final
assembled artifact for operator review.

## Fixed inputs and constraints

1. Start from a clean checkout at a recorded commit. Do not use
   `completed_prefix`.
2. Use one durable job database and one append-only run ledger for all four
   cuts.
3. Keep fixed:
   - premise `lf-003`;
   - Tess and Rho cast/plates;
   - current style anchor;
   - native H3 audio carrier;
   - 56-frame/grid-aligned duration policy;
   - repository-owned VibeVoice supply;
   - current Ref2VA model and continuation profile.
4. Chain each cut from the predecessor’s decoded final frame through the
   existing repository seam.
5. Every cut must pass:
   - pre- and post-render Whisper at the production bar;
   - identity/composition vision;
   - three-frame mouth-box consensus;
   - blocking SyncNet audiovisual alignment;
   - conditioning and provenance checks.
6. Preserve every rejected attempt with its gate evidence. Do not weaken a
   threshold and do not reuse a deterministic replay as a new attempt.
7. Assemble all four gated cuts with repository-owned ffmpeg assembly.
8. Record the final artifact, every cut, every chain frame, bundle, jobs
   database, ledger, QC evidence, and repository identity with SHA-256 hashes.
9. If cut 3 or cut 4 fails continuity, create a separate numbered finding using
   those exact artifacts. Do not infer that latent carry is required from the
   older pre-correction runs.

## OUT OF SCOPE

- Six-cut acceptance: this story only probes depth four.
- Latent save/load or first-frame-preservation implementation: only a separate
  finding may be filed if current-gate artifacts justify it.
- Changing the accepted two-cut artifact or its history.
- Changing cast, premise, style, model, duration policy, Whisper/vision/SyncNet
  thresholds, or assembly environment.
- Direct `wgp` calls or side scripts that bypass `run_bundle()`,
  `render_for_job()`, repository staging, QC, or ledger emission.

## DIFF BUDGET

- Expected: run assets/evidence and at most small bundle/fixture adjustments.
- Source-code changes are not intended. If a production gap blocks the governed
  path, stop and file a separate finding rather than expanding this story.

## Boundary Map

PRODUCES:
- `datasets/runs/provenance/lf003-four-cut-fullgate-YYYYMMDD/manifest.json`
  -> complete content-addressed run manifest
- `datasets/lf003-four-cut-fullgate-YYYYMMDD.jobs.db` -> durable four-job queue
- `datasets/lf003-four-cut-fullgate-YYYYMMDD.runs.jsonl` -> append-only ledger
- `datasets/runs/pull/lf003-four-cut-fullgate-YYYYMMDD/assembled.mp4`
  -> operator-review candidate
- per-cut raw/remux videos, chain frames, QC evidence, and hashes

CONSUMES:
- existing: `scripts/run_acceptance.py` -> `run_bundle(bundle_path: str | Path,
  *, db_path: str | Path | None = None, ledger_path: str | Path | None = None,
  output_path: str | Path | None = None, host=None, vision_judge=None) -> dict`
- existing: `host/wangp_adapter.py` -> `WanGPAdapter.render_for_job(job:
  Mapping, **kwargs)` repository render seam
- existing: `predict/vibevoice.py` -> repository-owned dialogue supply/provenance
- existing: LF003 premise, plates, style reference, and accepted Rho/Tess inputs

## Acceptance Criteria

1. Operator acceptance of the prior two-cut artifact is recorded in the new
   provenance directory with the exact artifact hash, source ledger hashes,
   verbatim authorization message, and UTC timestamp.
2. A clean-checkout run records repository commit and clean-tree identity before
   execution.
3. Four newly rendered cuts execute through the repository queue and
   `render_for_job()` with no completed-prefix reuse.
4. Each cut preserves its intended speaker and chains from the predecessor’s
   decoded final frame.
5. Each cut passes pre/post Whisper, identity/composition vision, mouth-box
   consensus, SyncNet, and provenance gates.
6. Every rejected attempt and gate reason is preserved and hashed.
7. The final four-cut assembly is produced through the repository-owned assembly
   path and has codec/probe metadata and SHA-256 recorded.
8. The final status is submitted as `mechanically_eligible_operator_review_pending`
   unless a gate fails; no operator acceptance is claimed automatically.
9. If continuity fails at cut 3 or 4, a separate finding is filed with exact
   artifacts and no speculative latent-carry implementation occurs in this story.
10. The run evidence is committed or staged as repo-owned artifacts, with no
    secrets, remote-only paths, or unhashable inputs.

## Testing Requirements

- Live GPU integration is mandatory: four fresh Ref2VA renders through the
  repository path.
- No model-free substitute may claim acceptance.
- Verify all artifact hashes after pullback.
- Run the applicable evidence-preservation tests targeting the new artifacts.
- Run `git diff --check`.

## Skills To Use

- `pvg` for story governance.
- `video-render-qc` for final artifact/probe/contact-sheet inspection.

## Delivery Requirements

- Paste exact acceptance/queue commands and summaries.
- Provide cut-by-cut gate table.
- Provide final hashes and probe metadata.
- Include an AC verification table.
- Update the authoritative `nd_contract` through the pvg delivery workflow.

## nd_contract
status: new

### evidence
- Prior two-cut artifact was displayed to the operator and authorized with
  “i agree to everything you may continue on all fronts” on 2026-09-19.

### proof
- [ ] Pending implementation

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-19.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-09-19T13:07:35Z status: open -> in_progress
- 2026-09-19T13:07:35Z auto-follows: linked to predecessor WD-ice0
- 2026-09-19T13:07:35Z claimed by dev-WD-rij6
- 2026-09-19T14:57:39Z status: in_progress -> in_progress
- 2026-09-19T14:57:39Z auto-follows: linked to predecessor WD-clms

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-ice0]], [[WD-clms]]

## Comments
