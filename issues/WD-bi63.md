---
id: WD-bi63
title: "docs: document subdir install spec (#adapters/plugin) + scanner trust note for paivot-driver"
status: closed
priority: 3
type: chore
labels: [docs, plugin]
created_at: 2026-08-24T14:04:14Z
created_by: speed
updated_at: 2026-08-24T14:18:51Z
content_hash: "sha256:04df9e390e1fc969cc1ecab849b92bcdf77d411d76c0ea6e0ddef4fbf4776cd1"
closed_at: 2026-08-24T14:18:51Z
close_reason: "PR #61 merged to paivot-hermes main: subdir install spec + scanner bypass + consent gate documented."
---

## Description
Live install findings (2026-08-24, jmanhype-glm session): (1) A bare 'hermes plugins install jmanhype/paivot-hermes' installs the WRONG layout — the loader needs plugin.yaml at the install root but paivot-hermes keeps it at adapters/plugin/plugin.yaml. The working form is the subdir spec: hermes plugins install https://github.com/jmanhype/paivot-hermes.git#adapters/plugin (installs as 'paivot-driver'). README/install docs must state this. (2) The Hermes plugin security scanner rates this repo DANGEROUS (110 findings) because the repo's own TEST FIXTURES contain rm -rf / shell-quoting strings (e.g. tests/test_driver_ops.py:236 tricky-string case). Self-authored installs need plugins.scan_on_install temporarily disabled — document the override and consider quarantining scanner-bait fixtures (e.g. move destructive-string tests to a fixtures file the scanner skips, or a marker) so a future 'hermes plugins install jmanhype/paivot-hermes' works clean.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-24T14:18:51Z status: open -> closed

## Links


## Comments
