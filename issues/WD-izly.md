---
id: WD-izly
title: "adapter: multishot join must use newline-delimited --- separators"
status: in_progress
priority: 1
type: task
labels: [bug]
created_at: 2026-08-23T05:26:06Z
created_by: speed
updated_at: 2026-08-23T05:30:11Z
content_hash: "sha256:d5672ff04a09caa211c8544b1453753e76b9cd5a48d20ee88351c2e2a8863ed2"
---

## Description
Root cause of both dropped-shot incidents: wgp parse_script splits on regex (?m)^---\s*$ — separator must sit on its own line. Adapter joins briefs with inline '---' so all shots collapse into one prompt; wgp renders 1 shot with exit 0. Fix: join with '\n---\n' in build_settings. RED test: settings['script'] contains newline-delimited separators; live re-render then yields 3 shots x frames.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-23T05:30:11Z status: open -> in_progress

## Links


## Comments
