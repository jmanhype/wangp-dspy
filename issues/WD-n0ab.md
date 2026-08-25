---
id: WD-n0ab
title: "plugin: knowledge_capture is half-wired — no _OP_SPEC/dispatch/enum, CaptureBuffer producer missing"
status: open
priority: 1
type: bug
parent: WD-j9nx
created_at: 2026-08-25T01:30:30Z
created_by: speed
updated_at: 2026-08-25T01:30:30Z
content_hash: "sha256:b7ba96e9c4842609d40c3eb9583c4dd2e2af2f1e11652d436930e1f6d50cf1aa"
---

## Description
The paivot-hermes plugin's knowledge_capture op is declared in driver/ops.py (_OPERATIONS line 63, role matrix developer+pm_acceptor) but has NO _OP_SPEC entry, NO executor dispatch branch, and is ABSENT from the paivot_story tool enum. Calling it dies on KeyError at kind, prefix, text_flag = _OP_SPEC[op]. The real capture path (run_knowledge_capture in driver/vault_capture.py, sha256 + evidence chain) is reachable only via session-end flush hooks, and nothing calls CaptureBuffer.add() — the producer is missing. Docs (README table, ARCHITECTURE.md) advertise the op as live. Fix: mirror insight_append — _OP_SPEC entry + executor dispatch branch (synthetic argv, no subprocess) + paivot_story enum + a CaptureBuffer.add() producer on the plugin surface.

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-j9nx]]

## Comments
