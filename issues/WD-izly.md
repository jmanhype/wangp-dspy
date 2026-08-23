---
id: WD-izly
title: "adapter: multishot join must use newline-delimited --- separators"
status: closed
priority: 1
type: task
labels: [bug, accepted]
created_at: 2026-08-23T05:26:06Z
created_by: speed
updated_at: 2026-08-23T05:30:16Z
content_hash: "sha256:be12dfc0d2f1841f05fcc0de6ef939b15780ac0e0eb555adf2df7df14a73dba7"
closed_at: 2026-08-23T05:30:15Z
close_reason: "PR #13 merged (eb56db2): line-anchored separator fix + Qwen early-split guard; Luna verified regex against live 3090 source; 139 tests green"
---

## Description
Root cause of both dropped-shot incidents: wgp parse_script splits on regex (?m)^---\s*$ — separator must sit on its own line. Adapter joins briefs with inline '---' so all shots collapse into one prompt; wgp renders 1 shot with exit 0. Fix: join with '\n---\n' in build_settings. RED test: settings['script'] contains newline-delimited separators; live re-render then yields 3 shots x frames.

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-08-23.

### proof
- [x] Story closed after accepted label was applied.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-08-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-08-23T05:30:11Z status: open -> in_progress
- 2026-08-23T05:30:15Z status: in_progress -> closed

## Links


## Comments
