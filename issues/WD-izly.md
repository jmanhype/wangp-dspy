---
id: WD-izly
title: "adapter: multishot join must use newline-delimited --- separators"
status: in_progress
priority: 1
type: task
labels: [bug, delivered]
created_at: 2026-08-23T05:26:06Z
created_by: speed
updated_at: 2026-08-23T05:30:12Z
content_hash: "sha256:e9411ba0225b48189aa47b467de72ad1a8cc8e187b9da89c472dbb07f6b0a770"
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

## Links


## Comments
