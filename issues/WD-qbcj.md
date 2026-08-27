---
id: WD-qbcj
title: "Methodology extraction: shuohao-skills pass docs, doctrines, design rationale"
status: in_progress
priority: 2
type: task
labels: [methodology, extraction, delivered]
parent: WD-j9nx
created_at: 2026-08-27T15:18:07Z
created_by: speed
updated_at: 2026-08-27T15:58:12Z
content_hash: "sha256:1d58149142559eb655055191f1df63c2fc8297604ac1ca8afcba9ea790cc0c19"
assignee: sol-max
follows: [WD-txt9, WD-mhr2, WD-pt60, WD-xzqp]
---

## Description
## Description

Deep extraction beyond WD-4k56 (which took gate-array / H3-contract / export-pack / assembler). Scope:

1. **The five references/*-pass.md craft docs** — outline-pass (adaptation economics: cut-with-reasons, merge-by-function, scene cap 4+ceil(eps/10) clamped 5-15, payoff spacing rules, narrative-prop test, two-round skeleton validation), roster/profile passes, script-pass, scene/prop/sheet passes, storyboard-pass.
2. **no-names-in-image-prompts doctrine.**
3. **Language-split field discipline** — machine fields always English, evidence never translated, deliberate no-promptLocal-for-voice.
4. **inferred-marker provenance convention.**
5. **CHANGELOG.md 827-line design-rationale history.**
6. **docs/superpowers spec-driven evolution.**

## Acceptance Criteria

(a) Each methodology area extracted to `docs/extraction/shuohao-skills/` with file:line refs + attribution.
(b) adopt/adapt/pass RECOMMENDATIONS with rationale vs SGFLIX bible / wangp-dspy / X-content pipelines; final verdicts reviewer-decided.
(c) Novel-specific craft vs generalizable method explicitly separated per artifact.
(d) All artifacts governed-captured (consented role re-registers if implementer is role-blocked).
(e) Apache-2.0 + eternityspring attribution preserved.

Verify board via `nd show`; report story id. Then CLAIM the story and append a dispatch note (Qwen implements, GLM reviews — both already briefed and running). Do not implement yourself.

## Acceptance Criteria


## Design


## Notes
Closure evidence (sol-max, 2026-08-27) — AC pointers:

(a) 12 docs in docs/extraction/shuohao-skills/ (4 technique WD-4k56 + 7 methodology this story + RUBRIC), each with file:line refs vs /tmp/shuohao-skills @ main. Merged in PR #26 (cdccd7d); GLM non-blocking nit patched post-merge at efeca56 (CHANGELOG citation :163 -> :162).
(b) adopt/adapt/pass RECOMMENDATIONS per artifact; final verdicts reviewer-decided: GLM review capture-20260827T153308Z = 9 ADOPT final across both stories (7 recommended ADOPT confirmed + 2 reviewer upgrades: h3-prompt-contract ADAPT->ADOPT, export-pack-spec ADAPT->ADOPT), zero overrides of ADOPTs, zero fabrications (62/62 citations resolve; 1 soft-reflow + 1 off-by-one line number, minor). ADOPT promotions deliberately NOT executed — promotion into skills/lanes is a separate operator decision.
(c) Novel-specific-vs-generalizable labeling present in all 7 artifacts (G4 pipeline matrices).
(d) Governed captures: 7 extraction captures + rubric capture-20260827T152238Z + review capture-20260827T153308Z, all under .git/paivot/nd-vault/knowledge/, sha256-verified on the hash chain.
(e) Apache-2.0 + eternityspring attribution headers verified present in all 7 by GLM.

Probe cleanup note: test-append-probe line was NOT present in issues/WD-qbcj.md at closure time (fresh grep 2026-08-27 found nothing; vlt line-73 delete had returned the dispatch comment intact) — no delete performed; nothing to clean.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-08-27.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-08-27T15:18:17Z status: open -> in_progress
- 2026-08-27T15:18:17Z auto-follows: linked to predecessor WD-txt9
- 2026-08-27T15:18:17Z claimed by sol-max
- 2026-08-27T15:45:45Z status: in_progress -> in_progress
- 2026-08-27T15:45:45Z auto-follows: linked to predecessor WD-mhr2
- 2026-08-27T15:57:06Z status: in_progress -> in_progress
- 2026-08-27T15:57:06Z auto-follows: linked to predecessor WD-pt60
- 2026-08-27T15:57:11Z status: in_progress -> in_progress
- 2026-08-27T15:57:11Z auto-follows: linked to predecessor WD-xzqp

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-txt9]], [[WD-mhr2]], [[WD-pt60]], [[WD-xzqp]]

## Comments

### 2026-08-27T15:18:17Z speed
Dispatch (sol-max, 2026-08-27): Qwen implements — full methodology extraction per AC (a)-(e) into docs/extraction/shuohao-skills/. GLM reviews — verdicts on adopt/adapt/pass recommendations are reviewer-decided. Both agents already briefed and running. Orchestrator will not implement.

### 2026-08-27T15:55:28Z speed
Closure evidence (sol-max, 2026-08-27): AC (a) 12 docs in docs/extraction/shuohao-skills/ with file:line refs + attribution, merged PR #26 cdccd7d (GLM nit patched efeca56). (b) Final verdicts reviewer-decided per GLM review capture-20260827T153308Z: 9 ADOPT final = 7 recommended ADOPT confirmed + 2 reviewer upgrades (h3-prompt-contract ADAPT->ADOPT, export-pack-spec ADAPT->ADOPT); zero overrides of ADOPTs; zero fabrications (62/62 citations resolve; 1 soft-reflow + 1 off-by-one line, minor). ADAPT/PASS sets as documented per artifact. ADOPT promotions deliberately NOT executed — promotion into skills/lanes is a separate operator decision. (c) Novel-specific-vs-generalizable labeling in all 7 (G4 matrices). (d) Governed captures: 7 extraction + rubric 152238Z + review 153308Z under nd-vault knowledge/, sha256 on hash chain. (e) Apache-2.0 + eternityspring attribution verified in all 7. Probe note: test-append-probe absent at closure (fresh grep found nothing; vlt line-73 delete returned dispatch comment intact) — no delete performed.

### 2026-08-27T15:58:12Z speed
DELIVERY (2026-08-27T15:57Z, sol-max): story_deliver executed via developer-role wiring — board labeled 'delivered' (status in_progress pending PM accept). Delivery note: GLM FINAL PASS (review capture-20260827T153308Z; rubric 152238Z) — zero fabrications, 9 ADOPT final across both extraction stories (7 recommended + 2 reviewer upgrades), zero overrides of ADOPTs. Artifacts: 7 methodology docs merged at cdccd7d (PR #26), nit patched efeca56; 9 governed captures under nd-vault knowledge/ sha256-chained. AC (a)-(e) met; completion documented in Notes + Comments per the board's checkbox fallback instruction. ADOPT promotions deliberately not executed — separate operator decision.
