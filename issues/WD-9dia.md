---
id: WD-9dia
title: "meta-hint guard over-triggers on lighting vocabulary ('flash', 'cut' in lighting sense)"
status: open
priority: 3
type: bug
labels: [prompt-director, validation]
created_at: 2026-08-24T21:54:47Z
created_by: speed
updated_at: 2026-08-24T21:54:47Z
content_hash: "sha256:558ae18f473212d07c5e6b5e2e14ba6bcf9f1ea35ae3a3218eb8365f3fef3202"
---

## Description
Live finding (Lost-Futures batch): an aesthetic-pack intent containing lighting language ('flash' — as in muzzle flash / camera flash lighting, also potential 'cut' as in light cut) was rejected by _META_HINT_RE as an editor meta-hint, killing a render cycle. The regex guards the four core brief sections but aesthetic director language legitimately uses these words in non-editing senses. Fix: context-aware check (e.g. reject 'flash cut'/'cut to' patterns, allow bare 'flash'/'lighting flash'), or move the check to n-gram patterns that imply editing ops. Regression: the pack-03 PS2 intent.

## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments
