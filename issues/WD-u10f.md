---
id: WD-u10f
title: "j9nx-0: extract signatures/ layer (ProfileSelectorSignature, RenderQCSignature) from module files"
status: closed
priority: 2
type: task
labels: [refactor, architecture]
parent: WD-j9nx
created_at: 2026-08-24T14:54:35Z
created_by: speed
updated_at: 2026-08-24T14:57:43Z
content_hash: "sha256:ee5b67c46a522e606c9ae7904edd1c43d1ed0f9a3ef080375bd26edb72d6776e"
assignee: jmanhype-glm
follows: [WD-5zti]
closed_at: 2026-08-24T14:57:43Z
close_reason: "PR #20 merged: signatures/ layer extracted (profile.py, qc.py), modules import from it, 237 tests green, no behavior change."
led_to: [WD-xzqp]
---

## Description
Per repo-structure research (2026-08-24, Firecrawl + GitHub API): all real-world DSPy app layouts separate signatures/ (I/O contracts) from modules/ (logic) — dspy-cli makes it a REQUIRED directory; upstream dspy keeps signatures/ as its own layer. wangp-dspy currently embeds ProfileSelectorSignature inside predict/profile_selector.py and RenderQCSignature inside evaluate/render_qc.py. Extract to signatures/ package; modules import from it. Low churn now, annoying later (GEPA per-predictor optimization in j9nx-4 targets signature-bearing predictors). Acceptance: signatures/ package exists with the two Signatures; modules import from signatures/; full suite green; no behavior change.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-24T14:55:20Z status: open -> in_progress
- 2026-08-24T14:55:20Z auto-follows: linked to predecessor WD-5zti
- 2026-08-24T14:55:20Z claimed by jmanhype-glm
- 2026-08-24T14:57:43Z status: in_progress -> closed

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-5zti]]
- Led to: [[WD-xzqp]]

## Comments
