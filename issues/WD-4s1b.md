---
id: WD-4s1b
title: "ADOPT: claim-fields for beat-grid/lyric-boundary checks"
status: in_progress
priority: 2
type: task
parent: WD-j9nx
created_at: 2026-08-27T18:21:37Z
created_by: speed
updated_at: 2026-08-27T18:26:16Z
content_hash: "sha256:d22e81bedc058d8c5027df2b0e20a1bff0d27ab02e85bd9097526770e6b7dd4d"
assignee: dev-WD-4s1b
follows: [WD-gq8y, WD-4jpr, WD-4k56]
labels: [delivered]
---

## Description
ADOPT: claim-fields for beat-grid/lyric-boundary checks (hookBeat pattern). Implements the hookBeat claim-field doctrine from shuohao-skills (docs/extraction/shuohao-skills/changelog-design-rationale.md, section C — declarations vs claims; GLM verdict ADOPT). Soft narrative intents become machine-checkable CLAIM fields on shot/cut records that a deterministic validator replays against the audio beat grid. Doctrine (verbatim rationale): hookBeat [scene,beat] CLAIMS the hook location; the gate checks the claim. 说明给人读，认领给机器查 — descriptions are for humans, claims are for machines to check; continuity becomes a gate, not self-discipline (changelog-design-rationale.md L17-18, L47; upstream CHANGELOG:482-500). Our application: wangp-dspy cut/shot records carry soft timing intentions (where a cut should land relative to lyric phrases) but nothing machine-checkable. This story adds: (1) a claims schema on cut/shot records — each cut claims its intended landing point as a lyric phrase boundary reference (phrase id + offset within phrase); (2) a DETERMINISTIC validator: given a beat grid (timestamped phrase boundaries) + a cut list, verify each cut lands on a claimed lyric phrase boundary within tolerance — zero-model, typed violations, loud skip when optional inputs absent (skip loudly, never silently — same axiom as no-names gate and skeleton sign-off); (3) CLI or test-hook integration so a cut list can be validated pre-render without any LLM. Components: 1. Claims schema (new module under predict/ or gates/, e.g. gates/beat_claims.py): dataclasses for BeatGrid (phrases with start/end timestamps), CutClaim (cut id, claimed phrase ref, offset, tolerance), and the record shape cut/shot entries use. Documented in docs/ with file:line refs into the extraction doc. 2. Deterministic validator validate_beat_claims(grid, cuts, default_tolerance) -> list[str]: every cut claims an existing phrase; claimed landing time = phrase.start + offset; |actual_cut_time - claimed_landing| <= tolerance per cut; violations returned as typed strings, raises typed BeatClaimValidationError when invalid. NO LLM calls anywhere. 3. CLI or test-hook: scripts/check_beat_claims.py (pattern: scripts/check_names.py) — takes a beat-grid JSON + cut-list JSON, prints per-cut PASS/FAIL report, exit 0 clean / 1 violations / 2 usage error. 4. Doc: short note under docs/ citing changelog-design-rationale.md (section C, file:line refs).

## Acceptance Criteria
- [ ] a) TDD suite for the validator: valid claims pass; unknown phrase ref rejected; offset outside phrase bounds rejected; cut outside tolerance rejected (boundary cases at exactly tolerance and just beyond); empty grid / empty cuts handled distinctly (typed, loud); all deterministic, zero-model. b) Claims schema documented + checked in (schema doc with field semantics + example records). c) CLI works on grid+cuts JSON files (and/or stdin); non-zero exit + clear per-cut report on violations, zero exit when clean, distinct usage-error exit. d) Doc checked in under docs/ citing the extraction doc (file:line refs). e) Full test suite green + implementation captured (PR trail, evidence).
## Design


## Notes


## History
- 2026-08-27T18:22:55Z status: open -> in_progress
- 2026-08-27T18:22:55Z auto-follows: linked to predecessor WD-gq8y
- 2026-08-27T18:22:55Z claimed by dev-WD-4s1b
- 2026-08-27T18:26:15Z status: in_progress -> in_progress
- 2026-08-27T18:26:15Z auto-follows: linked to predecessor WD-4jpr
- 2026-08-27T18:26:16Z status: in_progress -> in_progress
- 2026-08-27T18:26:16Z auto-follows: linked to predecessor WD-4k56

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-gq8y]], [[WD-4jpr]], [[WD-4k56]]

## Comments
