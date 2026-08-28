---
id: WD-cz6a
title: "S2: speaker diarization for multi-speaker <d> attribution"
status: open
priority: 1
type: task
parent: WD-j9nx
created_at: 2026-08-28T04:16:07Z
created_by: speed
updated_at: 2026-08-28T04:16:07Z
content_hash: "sha256:696d56ffd80ecc2c80ee643c8328b5c4e60b74e35279e38a7b98c5c3fbc82034"
---

## Description
## Description

S2 of the film lane (epic WD-j9nx, master sequence Phase 2). The repo CONSUMES out-of-repo speaker-diarization output: a versioned JSON timeline schema (per-speaker segments), a deterministic validator with typed per-rule rejections, and a deterministic converter producing `<d>Name</d>` speaker-attribution blocks compatible with the G5 prompt contract (S1) — the upstream data source for S3's `<d>` speaker gate.

BINDING (operator rule, carried from epic): faster-whisper/pyannote NEVER in repo code paths (license + rule). Diarization EXECUTION is an out-of-repo tool producing JSON; the repo ships only the schema + validator + converter + CLI that consume it. No runner scripts, no model imports, no requirements changes.

Maestro `audio_analysis.py:675-780` is IDEA-ONLY reference (non-commercial license — never vendor; adapt the idea clean-room).

Spec/plan pair (authored by orchestrator, #9 templates): docs/specs/s2-diarization.md + docs/plans/s2-diarization.md. Implementer follows the plan's T0-T6 exactly; judgment calls not answered there = STOP and report.

## Acceptance Criteria

- [ ] Timeline schema validator (TDD RED-first): rules R1-R6 each have valid-acceptance + typed-rejection tests naming the rule id; unknown top-level keys rejected
- [ ] Conversion to speaker-attribution blocks: deterministic (double-run byte-equality proven by test), 1:1 order-preserving mapping, defensive re-validation (single authority)
- [ ] Attribution rendering emits exactly the `<d>Name</d>` shape G5 accepts (regex-proven; zero bracketed/parenthesized labels)
- [ ] Full suite green at final head: count >= 442 (baseline 442 at d10af46); tail line in PR description
- [ ] CLI surface `scripts/check_diarization.py`: exit 0 + summary on valid, exit 1 + typed rule error on invalid, `--convert` flag; verified manually AND by subprocess test
- [ ] Binding grep gate: `grep -rn "faster_whisper\|pyannote" --include="*.py" predict/ host/ scripts/ tests/` → ZERO matches, recorded in PR
- [ ] PR-only flow: branch feat/wd-s2-diarization off main @ d10af46, explicit staging, no force-push; stable head reported to sol-max for Luna+GLM parallel gating (no self-merge)

## Notes

Carried nits from S1 (NOT in this story's scope): G3 run_pipeline wiring lands in S3; render_profiles constant import anytime.

Dispatch target: deepseek-fixer (routine measured-first implementation against a fully specified plan; architectural decisions already made in spec). Primary checkout.

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-j9nx]]

## Comments
