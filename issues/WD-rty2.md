---
id: WD-rty2
title: "VLM QC failure triage: gate/rule/example classification + ledger"
status: closed
priority: 2
type: task
parent: WD-j9nx
created_at: 2026-08-28T00:53:49Z
created_by: speed
updated_at: 2026-08-28T01:36:12Z
content_hash: "sha256:119d35b3f1243337e8233fceae93e2e52134ca05f9954f59a140a7bd8a32ab12"
closed_at: 2026-08-28T01:36:12Z
---

## Description
# #7 — VLM QC failure triage: gate / rule / example classification

## Description

ADOPT of the shuohao-skills three-tier escalation ladder (docs/extraction/shuohao-skills/changelog-design-rationale.md section B; CHANGELOG:384-398): when a QC failure recurs, decide EXPLICITLY which tier absorbs it — (1) deterministically judgeable → hard gate/rule; (2) semantic/ungateable → craft rule + reasoning, NO keyword gate ("keyword scans leak both ways"); (3) example-as-norm — fix the bundled exemplar so every instance demonstrates the rule. Central axiom to carry into our vocabulary: "误拦的门比没有门更糟——门的信用比数量重要" (a false-blocking gate is worse than no gate; a gate's credibility matters more than its count).

Apply to OUR QC failure vocabulary: classify each recurring failure as **gate-false-positive** (the gate fired on good material — fix or remove the gate), **rule-violation** (material genuinely violates a stated rule — fix the material/brief), or **example-gap** (no deterministic signal exists; the exemplar set doesn't demonstrate the norm — add/fix an exemplar, do NOT build a keyword gate). Deliverables: (a) a DETERMINISTIC classifier module in gates/ (zero-model, same pattern as provenance_gate.py: typed violations, loud skip, CLI with exit codes 0/1/2); (b) a TRIAGE LEDGER schema (JSONL append-only record per classified failure, plus a stats view answering: which class dominates, which gate fires most = rewrite that gate's wording, which never fires = dead gate or internalized — the .gates.jsonl/stats discipline from extraction section G); (c) docs/qc-triage.md stating the taxonomy, the 误拦 warning, and the decision procedure.

## Acceptance Criteria

1. **Deterministic classifier (pure, zero-model):** `gates/qc_triage.py` classifies a recorded QC failure event (structured: gate id / verdict / scores / anchor field / notes text) into exactly one of {GATE_FALSE_POSITIVE, RULE_VIOLATION, EXAMPLE_GAP} using explicit, documented heuristics — e.g. human-overridden reject → gate-false-positive candidate; gate fired but material later passed human review → gate-false-positive; gate did not fire but human flagged a violation of a NAMED rule → rule-violation; human flagged something with no named rule and no deterministic signal → example-gap. Ambiguous/unclassifiable events are a TYPED rejection (never silently defaulted). Loud skip on empty input (kind=empty_text pattern).
2. **Triage ledger schema:** `datasets/qc-triage-ledger.schema.json` (or equivalent JSON-schema file) defining the append-only JSONL record: event id, timestamp, genre, gate_id, verdict, scores, classification, confidence, evidence (verbatim notes/critique excerpt), action taken (gate-fixed / brief-fixed / exemplar-added / escalated-human), follow-up story id. A `stats()` helper aggregates the ledger: counts per class, per-gate fire counts, never-fired gate list.
3. **CLI smoke:** `scripts/check_qc_triage.py` with exit codes 0 (classified clean) / 1 (typed rejection or unclassifiable) / 2 (usage error), matching the check_provenance.py CLI convention.
4. **Docs:** `docs/qc-triage.md` — the three-class taxonomy mapped onto our RenderQC vocabulary (Verdict.PASS/REVISE/REJECT, CONCEPT_ENCODING_FAILURE, QCEscalationError, genre thresholds), the 误拦 mis-blocking warning quoted with provenance, and the decision procedure ("first ask: is this deterministically judgeable?").
5. **TDD RED→GREEN:** tests cloned from tests/test_provenance_gate.py conventions (typed violations, loud-skip caplog where applicable, seed data load, CLI exit-code smoke 0/1/2). Full suite green in .venv (Python 3.12), zero-model.

## Design

- Classification inputs are STRUCTURED failure records (from QC verdicts + human-review overrides), not free-text mining — the classifier is deterministic string/field logic, same ZERO-MODEL contract as the other gates.
- The ledger is APPEND-ONLY (retention=none, append anytime — same ruling as the insight-ledger story); stats() is a pure read over the file.
- No auto-rewriting of rules/docs from the ledger (extraction section G: "没有评测集的自动改文档就是瞎改" — we log and a human decides; GEPA-style auto-accept is the ADAPT item for a later story).
- Existing gates (language/no-names/common-actions/provenance) are NOT modified by this story; the classifier consumes their verdicts as input records.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-28T01:36:12Z status: open -> closed

## Links
- Parent: [[WD-j9nx]]

## Comments

### 2026-08-28T01:36:12Z speed
ADOPT #7 DELIVERED: PR #34 merged (GLM PASS/ADOPT — 406/406 green +16 over baseline, RED genuine, ambiguity typed not guessed, ledger append-only, 误拦 operational). Nits: stats class-conflation doc note, known_gates hardcoded in CLI.
