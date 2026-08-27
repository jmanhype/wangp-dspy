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
updated_at: 2026-08-27T15:55:12Z
content_hash: "sha256:739555f3839bf176e96cd81dceefd26b1916e07336c3296d1ef678efd7f490ff"
assignee: sol-max
follows: [WD-txt9, WD-mhr2]
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

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-txt9]], [[WD-mhr2]]

## Comments

### 2026-08-27T15:18:17Z speed
Dispatch (sol-max, 2026-08-27): Qwen implements — full methodology extraction per AC (a)-(e) into docs/extraction/shuohao-skills/. GLM reviews — verdicts on adopt/adapt/pass recommendations are reviewer-decided. Both agents already briefed and running. Orchestrator will not implement.
