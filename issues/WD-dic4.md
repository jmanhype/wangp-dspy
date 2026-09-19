---
id: WD-dic4
title: "Codex Skill Router calibration"
status: closed
priority: 0
type: epic
created_at: 2026-09-19T02:48:59Z
created_by: speed
updated_at: 2026-09-19T02:54:10Z
content_hash: "sha256:df258bdf4f83172d6bc19d4fcd94712a3e837946048d6902a491ce039f918efa"
closed_at: 2026-09-19T02:54:10Z
close_reason: "All child stories accepted; Skill Router symptom-specific calibration met the epic outcomes."
labels: [accepted]
---

## Description
## Description
Calibrate the accepted local Codex Skill Router after live dogfooding. A fresh-session verification prompt containing diagnostic Supabase symptoms plus router-test meta-language ranked the broad supabase skill above supabase-rls-frontend-debugging.

## Epic Outcomes
- Symptom-specific skills outrank broad same-domain skills when a prompt contains detailed diagnostic symptoms.
- Short domain-only prompts still receive useful broad-domain suggestions.
- Ranking remains local, deterministic, private, and fail-open.

## OUT OF SCOPE
- Jev or network inference.
- Embeddings.
- Automatic skill execution.
- Reopening or modifying the accepted MVP story's historical evidence.

## nd_contract
status: new

### evidence
- Fresh Codex process on 2026-09-19 injected: supabase score 0.82, supabase-rls-frontend-debugging score 0.7407.
- Direct diagnostic prompt previously ranked supabase-rls-frontend-debugging first, proving the ranking is prompt-sensitive.

### proof
- [ ] Calibration task demonstrates corrected ordering on a meta-language diagnostic prompt without breaking short prompts.

## Acceptance Criteria
1. A regression test reproduces the live meta-language diagnostic ranking case.
2. The specific Supabase RLS debugging skill outranks the broad Supabase skill for that case.
3. Existing router behavior and fail-open guarantees remain covered by the test suite.
4. pvg verify reports zero issues.

## Design
Adjust local scoring only; no network or persistence changes.

## History

## Links

## Comments


## Acceptance Criteria


## Design


## Notes
## nd_contract
status: accepted

### evidence
- Child WD-o1xf accepted and closed on 2026-09-19.
- Live meta-language diagnostic now ranks supabase-rls-frontend-debugging above broad supabase, while short domain prompts retain broad-domain suggestions.

### proof
- [x] Symptom-specific skills outrank broad same-domain skills for detailed diagnostic prompts.
- [x] Short domain-only prompts still receive useful broad-domain suggestions.
- [x] Ranking remains local, deterministic, private, and fail-open.

## History
- 2026-09-19T02:54:10Z status: open -> closed

## Links


## Comments
