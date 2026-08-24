---
id: WD-j9nx
title: "DSPy-native video-gen pipeline"
status: open
priority: 2
type: epic
created_at: 2026-08-22T04:04:21Z
created_by: speed
updated_at: 2026-08-24T14:59:20Z
content_hash: "sha256:967b5ba2400c3939bd6cd6e375c3f0ed04830eb13f8c770b05d7baf6eabde55e"
---

## Description
## Acceptance Criteria (operator-view, 2026-08-24)

The epic is DONE when all of the following hold:

1. **One call, one artifact chain.** A single pipeline invocation
   (`Pipeline.forward(intent)`) carries an intent through
   briefs -> profile -> assemble -> render -> QC without any manual
   glue between stages, producing: the rendered video, a typed QC
   verdict, and a replayable evidence trail for the run.
2. **Typed failure at every boundary.** Each stage transition fails
   loudly with a typed error naming the stage — no silent no-ops
   (the WD-yyj9 class of bug is structurally excluded).
3. **Proven on the real GPU.** At least one full e2e run on the 3090
   through the PIPELINE (not the adapter alone) that ends in a
   keeper-trackable verdict (WD-mhr2).
4. **The pipeline is optimizable.** metrics/ + train/val datasets
   exist; a recorded baseline (LabeledFewShot) and at least one GEPA
   compile exist with side-by-side comparison — improvement OR a
   documented plateau with evidence (WD-txt9).
5. **Repo structure matches the research-agreed layout**:
   signatures/ (contracts), predict/, evaluate/, host/, datasets/,
   metrics/, training/, compiled/ — capability folders + app-repo
   artifacts.
6. **Every child story closed with its own evidence** (green tests,
   merged PR, real-run artifacts where GPU-bound) — no paper-only
   closures.

NOT in scope (explicitly): autonomous publishing, UI, fine-tuning
model weights (BootstrapFinetune is a later lever if prompt-only
plateaus).

## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments
