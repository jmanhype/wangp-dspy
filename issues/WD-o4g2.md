---
id: WD-o4g2
title: "wgp multishot: deterministic tensor shape error on long urban/neon prompts — [1, 24, 37, 1, 40, 2, 22, 2] invalid for input of size 3196800"
status: closed
priority: 2
type: bug
labels: [wgp, upstream, 3090]
created_at: 2026-08-24T19:01:47Z
created_by: speed
updated_at: 2026-08-24T19:23:05Z
content_hash: "sha256:1c35712f28c8a4b99f4e8fc9bd9c33d9f08d893a6dbd56362572f8bf767e7ff0"
closed_at: 2026-08-24T19:23:05Z
close_reason: "Fixed in adapter 5586a77: 720p snaps to H3 480x832 grid; regression tested. Root cause: odd latent dim at portrait; fork keyframes code innocent."
---

## Description
Live WD-mhr2 batch finding (2026-08-24, reproduced 2/2 attempts, deterministic): the neon-rain intent (rain on neon streets at midnight, reflections rippling as a lone figure walks past glowing signs) reliably kills the render: wgp exits 0 with 0/1 tasks (1 skipped) and stdout tail '[MULTISHOT ERROR] shape [1, 24, 37, 1, 40, 2, 22, 2] is invalid for input of size 3196800' plus 'NVFP4: linear fallback'. Our adapter's WD-d3b9 guard catches it as a typed failure (exit-0-but-no-video class). Other intents (lighthouse, kaiju) at similar frame counts render fine — suggests prompt-length- or content-dependent tensor sizing in the Wan2GP multishot path, likely upstream in Wan2GP not wangp-dspy. Repro: WD_MHR2_INTENT=<neon rain string> scripts/run_cycle.py. Next: capture the failing settings.json + brief, check prompt token length vs the working intents, report upstream to Wan2GP.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-24T19:23:05Z status: open -> closed

## Links


## Comments

### 2026-08-24T19:23:04Z speed
ROOT CAUSE (empirical, direct repro + full traceback): portrait 720x1280 is off H3 latent grid — VAE 160x90 latents, 90/patch_w2=45 odd, patchify packed reshape expects 44*2 -> deterministic RuntimeError. NOT the fork's keyframes code (innocent); stock patchify + unsupported resolution. FIXED in adapter: 720p snaps to 480x832 grid with loud notice (5586a77, regression test green, full suite green). Fork WIP snapshotted cb84f4f first. No upstream PR needed — fix belongs in our settings layer.
