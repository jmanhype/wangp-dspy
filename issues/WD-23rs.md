---
id: WD-23rs
title: "Checker lane receipt coverage"
status: open
priority: 1
type: task
labels: [evidence, qc, gate]
parent: WD-3nod
created_at: 2026-09-29T04:33:00Z
created_by: speed
updated_at: 2026-09-29T04:33:00Z
content_hash: "sha256:41ed52054f62d009767f82c948b393bb794c0706c281d7ea41104056304b0ad1"
---

## Description
## Context

Current merged main `a382f747f31735c9eaa5eecb4bb6e1581b3403de` has a stricter fail-closed Maestro-parity checker than the historical capstone index. Re-running the canonical verifier now shows four previously accepted verified-lane bundles failing only because known optional Python import fallbacks in their immutable native logs are not classified:

- `WD-cpow` (SFX/audio post): `flash_attn`
- `WD-m0r5` (image): `piexif`
- `WD-r81u` (finishing): `postprocessing`
- `WD-rous` (music): `flash_attn`

The generated outputs and objective gates in those historical bundles remain accepted. The issue is warning ownership/classification, not missing media. The checker must not use a blanket import ignore.

## USER INTENT
The operator must be able to run one fail-closed checker against any generated Maestro-parity bundle and get a trustworthy pass/fail result. Verified historical lanes must pass without hiding optional fallback conditions; genuinely failed gates and unknown import failures must still fail.

## OUT OF SCOPE
- Any GPU/SSH/host contact, model download, media regeneration, or provider spend; this is repository evidence/checker work only.
- Any change to protected engine files or thresholds.
- Reopening or rewriting accepted host media bytes or native logs.
- GUI, publication, training, or unrelated capability work.

## DIFF BUDGET
About 8 files and under 600 authored/evidence changed LOC. JSON evidence edits may be larger mechanically but must remain scoped to warning ownership metadata.

## Boundary Map
PRODUCES:
- scripts/verify_maestro_parity.py -> exact fail-closed classifier for only explicitly proven optional import fallbacks, with stable warning code, line, native-log SHA-256, and successful-output marker
- docs/maestro-parity-evidence-contract.md -> normative warning-ownership contract matching the verifier
- tests/test_maestro_parity_evidence.py -> positive/negative tests proving accepted optional fallbacks pass and unknown/tampered/failed fallbacks fail
- datasets/runs/maestro-parity/WD-cpow/evidence.json -> owned optional import warnings without changing media/log hashes
- datasets/runs/maestro-parity/WD-m0r5/evidence.json -> owned optional import warnings without changing media/log hashes
- datasets/runs/maestro-parity/WD-r81u/evidence.json -> owned optional import warnings without changing media/log hashes
- datasets/runs/maestro-parity/WD-rous/evidence.json -> owned optional import warnings without changing media/log hashes
- datasets/runs/maestro-parity/checker-lane-receipts/evidence.json -> current-machine canonical checker receipt for representative lanes

CONSUMES:
- (existing): scripts/verify_maestro_parity.py -> verify(bundle: Path) -> VerificationReport
- (existing): docs/maestro-parity-evidence-contract.md -> queue-native-log-warning-ownership contract row
- (existing): datasets/runs/maestro-parity/{WD-2gyw,WD-bxhc,WD-cpow,WD-m0r5,WD-r81u,WD-rous}/evidence.json -> immutable accepted lane bundles

## Story Acceptance Criteria
1. [State] At merged main, the canonical checker exits 0 for these representative verified bundles: `WD-2gyw` video, `WD-bxhc` voice/character, `WD-cpow` SFX/audio post, `WD-m0r5` image, `WD-r81u` finishing, `WD-rous` music, and `consent-closeout` voice/character consent projection.
2. [State] The checker still exits nonzero for `WD-dmf2` director/editor evidence because its recorded objective gates and reviewer verdict genuinely fail; no classification may upgrade that bundle.
3. [State] Optional import fallback classification is exact and evidence-backed: module name, native log line, exact log SHA-256, and a successful output/save marker are recorded; unknown imports, changed hashes, missing success markers, and generic `ImportError` values remain fail-closed.
4. [State] No accepted output, native log, media metadata, model/reference provenance, queue result, or objective gate value is rewritten to manufacture a pass; only explicit warning ownership/contract/test/receipt data may change.
5. [State] A current checker receipt records command, commit, pass/fail result, warnings, and SHA-256 for each representative bundle, and fails closed if the receipt drifts.
6. [State] Focused checker tests, undeselected full suite, `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity, `git diff --check`, and exact-head CI pass.

## Testing Requirements
- Extend `tests/test_maestro_parity_evidence.py` with real temporary bundle fixtures; no mocks of verifier behavior.
- Include each accepted optional fallback and negative coverage for an unknown module, changed log bytes, and a fallback without a successful-output marker.
- Run the canonical checker on every representative bundle listed in AC 1 and on `WD-dmf2`.
- Run focused tests, the undeselected full suite, lint, release verification, protected parity, diff check, and exact-head CI.

## Delivery Requirements
- Record exact commands, parsed JUnit counters, checker results, commit SHA, PR, CI, unchanged media/log hashes, and AC table.
- Include `LEARNINGS:`.
- Do not contact the GPU host or regenerate evidence.

## MANDATORY SKILLS
- pvg
- tool-systematic-debugging

## nd_contract
status: new

### evidence
- Current verifier observations at main `a382f747`: WD-2gyw/WD-bxhc/consent-closeout pass; WD-cpow, WD-m0r5, WD-r81u, and WD-rous fail only on unclassified optional import fallbacks; WD-dmf2 genuinely fails objective/reviewer gates.

### proof
- [ ] Pending exact optional-warning ownership, current lane receipts, tests, and standing gates.

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-3nod]]

## Comments
