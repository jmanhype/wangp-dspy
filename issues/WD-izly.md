---
id: WD-izly
title: "adapter: multishot join must use newline-delimited --- separators"
status: closed
priority: 1
type: task
labels: [bug, delivered]
created_at: 2026-08-23T05:26:06Z
created_by: speed
updated_at: 2026-08-23T05:30:15Z
content_hash: "sha256:6d74571ffd1e17ca0ebec9d9db17660517691807104a535c00bae7b1fd4cea8c"
closed_at: 2026-08-23T05:30:15Z
close_reason: "PR #13 merged (eb56db2): line-anchored separator fix + Qwen early-split guard; Luna verified regex against live 3090 source; 139 tests green"
---

## Description
Root cause of both dropped-shot incidents: wgp parse_script splits on regex (?m)^---\s*$ — separator must sit on its own line. Adapter joins briefs with inline '---' so all shots collapse into one prompt; wgp renders 1 shot with exit 0. Fix: join with '\n---\n' in build_settings. RED test: settings['script'] contains newline-delimited separators; live re-render then yields 3 shots x frames.

## Acceptance Criteria


## Design


## Notes


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
