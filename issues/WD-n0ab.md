---
id: WD-n0ab
title: "plugin: knowledge_capture is half-wired — no _OP_SPEC/dispatch/enum, CaptureBuffer producer missing"
status: in_progress
priority: 1
type: bug
parent: WD-j9nx
created_at: 2026-08-25T01:30:30Z
created_by: speed
updated_at: 2026-08-28T02:13:03Z
content_hash: "sha256:33e8d35a9ee140eb9d38f8069f213ec8e12c3edd4e67c5ba0105046c9566b751"
assignee: dev-WD-n0ab
follows: [WD-txt9, WD-mhr2]
labels: [fix-merged-pending-delivery]
---

## Description
The paivot-hermes plugin's knowledge_capture op is declared in driver/ops.py (_OPERATIONS line 63, role matrix developer+pm_acceptor) but has NO _OP_SPEC entry, NO executor dispatch branch, and is ABSENT from the paivot_story tool enum. Calling it dies on KeyError at kind, prefix, text_flag = _OP_SPEC[op]. The real capture path (run_knowledge_capture in driver/vault_capture.py, sha256 + evidence chain) is reachable only via session-end flush hooks, and nothing calls CaptureBuffer.add() — the producer is missing. Docs (README table, ARCHITECTURE.md) advertise the op as live. Fix: mirror insight_append — _OP_SPEC entry + executor dispatch branch (synthetic argv, no subprocess) + paivot_story enum + a CaptureBuffer.add() producer on the plugin surface.

## Acceptance Criteria


## Design


## Notes
2026-08-26 REOPEN: prior delivered status was false (gaps verified on main c16fec7). Fix at paivot-hermes fix/wd-n0ab-knowledge-capture @ b704a69 — 708 tests green, py311 OK — pending independent review + operator merge.
2026-08-26: fix MERGED to paivot-hermes main as ab9f27c (PR #86, 708 tests green, GLM review PASS). Plugin resynced across all profiles + global (hash-verified identical). Remaining: verify live knowledge_capture through the plugin surface in a fresh session, then deliver.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-08-24.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-08-25T01:32:17Z status: open -> in_progress
- 2026-08-25T01:32:17Z auto-follows: linked to predecessor WD-txt9
- 2026-08-25T01:32:17Z claimed by dev-WD-n0ab
- 2026-08-25T01:44:46Z status: in_progress -> in_progress
- 2026-08-25T01:44:46Z auto-follows: linked to predecessor WD-mhr2

## Links
- Parent: [[WD-j9nx]]
- Follows: [[WD-txt9]], [[WD-mhr2]]

## Comments

### 2026-08-26T17:38:32Z speed
Reopened 2026-08-26: prior 'delivered' status was FALSE — knowledge_capture gaps verified present on main c16fec7 (no _OP_SPEC entry, no executor dispatch, absent from paivot_story enum, no CaptureBuffer producer). Fix implemented on paivot-hermes branch fix/wd-n0ab-knowledge-capture @ b704a69 (708 tests green, py311 OK), pending independent review + operator merge.

### 2026-08-28T02:13:03Z speed
CLOSE-OUT (2026-08-27, operator relay per Sol probe evidence): knowledge_capture fix verified LIVE on paivot-hermes main f5e1ff6 — op registered in _OPERATIONS, executor dispatch (executor.py:1033), plugin surface wired, installed-plugin hash == source (a6fd8ee1), every typed guard proven in-process (mode enum, run_is_live lineage, related-wikilink rules), happy-path probe passed with note-on-disk + sha256 evidence match. Digest-definition ruling: digest of record = note WITHOUT envelope marker (frontmatter+body, per spec docstring) — on-disk-bytes variant declined; if the distinction ever matters operationally, file a one-liner ticket. Story delivered and closed.
