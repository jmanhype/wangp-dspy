---
id: WD-izly
title: "adapter: multishot join must use newline-delimited --- separators"
status: open
priority: 1
type: task
labels: [bug]
created_at: 2026-08-23T05:26:06Z
created_by: speed
updated_at: 2026-08-23T05:26:06Z
content_hash: "sha256:af29d6621728b917c5c2a2cfa120242e86a300425f0ea9ea3b1562ac38206b45"
---

## Description
Root cause of both dropped-shot incidents: wgp parse_script splits on regex (?m)^---\s*$ — separator must sit on its own line. Adapter joins briefs with inline '---' so all shots collapse into one prompt; wgp renders 1 shot with exit 0. Fix: join with '\n---\n' in build_settings. RED test: settings['script'] contains newline-delimited separators; live re-render then yields 3 shots x frames.

## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments
