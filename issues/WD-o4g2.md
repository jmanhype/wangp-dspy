---
id: WD-o4g2
title: "wgp multishot: deterministic tensor shape error on long urban/neon prompts — [1, 24, 37, 1, 40, 2, 22, 2] invalid for input of size 3196800"
status: open
priority: 2
type: bug
labels: [wgp, upstream, 3090]
created_at: 2026-08-24T19:01:47Z
created_by: speed
updated_at: 2026-08-24T19:01:47Z
content_hash: "sha256:40f8840ae3e47ebef23745ae0b73582ec9d028ffe8f44cd10c7ef84b9db3eae1"
---

## Description
Live WD-mhr2 batch finding (2026-08-24, reproduced 2/2 attempts, deterministic): the neon-rain intent (rain on neon streets at midnight, reflections rippling as a lone figure walks past glowing signs) reliably kills the render: wgp exits 0 with 0/1 tasks (1 skipped) and stdout tail '[MULTISHOT ERROR] shape [1, 24, 37, 1, 40, 2, 22, 2] is invalid for input of size 3196800' plus 'NVFP4: linear fallback'. Our adapter's WD-d3b9 guard catches it as a typed failure (exit-0-but-no-video class). Other intents (lighthouse, kaiju) at similar frame counts render fine — suggests prompt-length- or content-dependent tensor sizing in the Wan2GP multishot path, likely upstream in Wan2GP not wangp-dspy. Repro: WD_MHR2_INTENT=<neon rain string> scripts/run_cycle.py. Next: capture the failing settings.json + brief, check prompt token length vs the working intents, report upstream to Wan2GP.

## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments
