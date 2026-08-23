---
id: WD-1eix
title: "dogfood cycle 2: ledger injection + SshHost repeatability"
status: in_progress
priority: 2
type: task
labels: [dogfood, delivered]
created_at: 2026-08-23T04:00:35Z
created_by: speed
updated_at: 2026-08-23T04:10:21Z
content_hash: "sha256:6191eeb7b4af8eae1dfba641d5cd892db694fbb9655454c2fd425337babd1fb9"
assignee: dev-WD-1eix
---

## Description
Second full dogfood cycle through paivot-hermes: verify (a) the insight ledger actually injects the last-10 digest into a fresh session (couldn't during T0), (b) SshHost remote render repeats clean with no glue, (c) full claim->render->QC->insight->deliver->accept loop through plugin ops only.

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-08-22.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## History
- 2026-08-23T04:00:51Z status: open -> in_progress
- 2026-08-23T04:00:51Z claimed by dev-WD-1eix
- 2026-08-23T04:10:20Z status: in_progress -> in_progress

## Links


## Comments
