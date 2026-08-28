---
id: WD-r8n9
title: "scanner: DANGEROUS verdict on own repo's test fixtures blocks plugin install — quarantine scanner-bait tests"
status: open
priority: 2
type: bug
labels: [security, tooling, upstream]
created_at: 2026-08-24T14:04:28Z
created_by: speed
updated_at: 2026-08-28T01:57:28Z
content_hash: "sha256:c090cf5cc94b5caaa0ff1516d4d86848b9af30f3e56edc09ab554c9a0802c57b"
---

## Description
Hermes plugin_guard scan_plugin rates paivot-hermes DANGEROUS (110 findings) — verdict class 'always blocked', --force cannot override. Root cause: the repo's own unit tests legitimately exercise destructive-string handling (rm -rf / shell quoting / unicode edge cases, e.g. tests/test_driver_ops.py:236, test_vault_s5_evolve.py:226 subprocess fixtures). These are TEST FIXTURES, not runtime code, but the scanner scores them as destructive. Options to evaluate: (a) exclude tests/ from the destructive-pattern scan tier (test code never ships in the runtime path), (b) a per-plugin scanner allowlist/trust marker for self-authored sources, (c) quarantine scanner-bait fixtures into a dedicated file with a recognized header. Current workaround: plugins.scan_on_install=false for the install window (done, re-enabled after). NOTE: scanner logic lives in the Hermes install (~/.hermes/hermes-agent/tools/plugin_guard.py + hermes_cli/plugins_cmd.py) — may belong upstream in hermes-agent, not this repo. Filed here to track decision + workaround doc.

## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments

### 2026-08-24T14:12:27Z speed
Filed upstream: NousResearch/hermes-agent#93927 (includes minimal repro — 4-line test fixture alone yields dangerous — plus root-cause code path: plugin_guard.EXCLUDED_DIRS lacks tests/, skills_guard._determine_verdict:1161 single-critical→dangerous, no override). Fun meta-detail: filing the issue through the agent also tripped the terminal hardline block because the issue TEXT contains the pattern strings — same false-positive class at a different layer, noted in the issue.

### 2026-08-28T01:57:28Z speed
2026-08-27 sol-max: TRIAGE (per operator ruling — triage first, then recommend).

MEASURED VERDICTS (ran installed scanner plugin_guard.scan_plugin on paivot-hermes, 2026-08-27):
- Full working tree: DANGEROUS, 126 findings, 4 critical + 9 high.
- Minus tests/: CAUTION, 34 findings, 0 critical, 7 high.
- Git-shape (minus tests/ AND .toolchain/, which is gitignored local tooling): CAUTION, 20 findings, 0 critical, 3 high.

THE 4 CRITICALS (all in tests/, all deliberate scanner-bait fixtures):
1. tests/test_driver_ops.py:256 [destructive_root_rm] — 'rm -rf /' embedded in a metacharacter-quoting fixture string; the test asserts build_pvg_argv preserves it verbatim into argv (shell-quoting regression guard). Never executed.
2. tests/test_prereq.py:328 [hardcoded_secret] — "sup3r-secret-decoy-token", an explicitly-labeled decoy planted via monkeypatch.setenv to verify secret-scrubbing of error messages; cleaned up by monkeypatch.
3. tests/test_vault_ops.py:84 [system_passwd_access] — "/etc/passwd" in a list of BAD titles asserted to be REFUSED by validate_file_title (traversal-rejection test).
4. tests/test_vault_ops.py:140 [system_passwd_access] — "read ../../etc/passwd" asserted refused with vault_command_refused before any spawn.

CLASSIFICATION: GENUINE SCANNER FALSE-POSITIVE CLASS — test-only content flagged as production threat. Zero runtime exposure: all four are string literals inside assertions that the driver REJECTS or QUOTES them; no fixture is ever executed, and the fixtures exist precisely to prove the driver's own defenses work. No real issue hidden in fixtures. Remaining HIGHs also benign: 4x curl|sh/sudo lines in vendored .toolchain READMEs (gitignored, never shipped) and 3x NEGATIVE doc statements ("No `curl | bash` bootstrap") in README/docs that trip the pattern on their own denial of the practice.

RECOMMENDATION (evidence-backed):
(a) UPSTREAM FIX (preferred; ticket decision left to operator per standing order): hermes-agent#93927 already filed with root cause + 4-line repro. Fix shape supported by this triage: EXCLUDED_DIRS lacks tests/ (test code never ships in the runtime path), and _determine_verdict maps single-critical→dangerous with no override. A tests/-tier exclusion (or test-fixture severity demotion) moves this repo from dangerous→caution — force-installable and human-confirmable, the correct trust posture for self-authored source.
(b) LOCAL INTERIM: none applied, and I recommend against a local ignore/allowlist. scan_on_install=true is already restored (block only matters at install time, not dev). A blanket local ignore would mask future REAL regressions in this repo's own driver code — violating the gate-credibility axiom (误拦的门比没有门更糟——门的信用比数量重要). The one-time confirmation flow after upstream lands is the right interim.
(c) REJECTED alternative: quarantining bait fixtures into a dedicated file with a recognized header — the scanner still scores the file, and it degrades locality of the quoting/traversal tests without fixing the gap.

STATUS: awaiting operator call on upstream ticket disposition. No repo changes made by this triage.
