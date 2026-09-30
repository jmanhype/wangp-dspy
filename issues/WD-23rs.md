---
id: WD-23rs
title: "Checker lane receipt coverage"
status: closed
priority: 1
type: task
labels: [evidence, qc, gate, accepted]
parent: WD-3nod
created_at: 2026-09-29T04:33:00Z
created_by: speed
updated_at: 2026-09-29T06:06:28Z
content_hash: "sha256:4a2f1ad3fc62bab25462a53cdb1f0b939e4b09b1796b576be55ebe3edb5d9469"
assignee: dev-WD-23rs
follows: [WD-p587, WD-32hk, WD-dc3w]
closed_at: 2026-09-29T06:04:43Z
close_reason: "Accepted: exact-head evidence, immutable lane hashes, fail-closed fallback ownership, receipt drift coverage, representative outcomes, and all standing gates verified."
led_to: [WD-28ac, WD-qthq, WD-bw0h, WD-he8i, WD-1s5s]
---

## Description
## Context

Current merged main `a382f747f31735c9eaa5eecb4bb6e1581b3403de` has a stricter fail-closed Maestro-parity checker than the historical capstone index. Re-running the canonical verifier now shows four previously accepted verified-lane bundles failing only because known optional Python import fallbacks in their immutable native logs are not classified:

- `WD-cpow` (SFX/audio post): `flash_attn`
- `WD-m0r5` (image): `piexif`
- `WD-r81u` (finishing): `postprocessing`
- `WD-rous` (music): `flash_attn`

The generated outputs and objective gates in those historical bundles remain accepted. The issue is warning ownership/classification, not missing media. The checker must not use a blanket import ignore.

## USER INTENT
The operator must be able to run one fail-closed checker against any generated Maestro-parity bundle and get a trustworthy pass/fail result. Verified historical lanes must pass without hiding optional fallback conditions; genuinely failed gates and unknown import failures must still fail.

## OUT OF SCOPE
- Any GPU/SSH/host contact, model download, media regeneration, or provider spend; this is repository evidence/checker work only.
- Any change to protected engine files or thresholds.
- Reopening or rewriting accepted host media bytes or native logs.
- GUI, publication, training, or unrelated capability work.

## DIFF BUDGET
About 8 files and under 600 authored/evidence changed LOC. JSON evidence edits may be larger mechanically but must remain scoped to warning ownership metadata.

## Boundary Map
PRODUCES:
- scripts/verify_maestro_parity.py -> exact fail-closed classifier for only explicitly proven optional import fallbacks, with stable warning code, line, native-log SHA-256, and successful-output marker
- docs/maestro-parity-evidence-contract.md -> normative warning-ownership contract matching the verifier
- tests/test_maestro_parity_evidence.py -> positive/negative tests proving accepted optional fallbacks pass and unknown/tampered/failed fallbacks fail
- datasets/runs/maestro-parity/WD-cpow/evidence.json -> owned optional import warnings without changing media/log hashes
- datasets/runs/maestro-parity/WD-m0r5/evidence.json -> owned optional import warnings without changing media/log hashes
- datasets/runs/maestro-parity/WD-r81u/evidence.json -> owned optional import warnings without changing media/log hashes
- datasets/runs/maestro-parity/WD-rous/evidence.json -> owned optional import warnings without changing media/log hashes
- datasets/runs/maestro-parity/checker-lane-receipts/evidence.json -> current-machine canonical checker receipt for representative lanes

CONSUMES:
- (existing): scripts/verify_maestro_parity.py -> verify(bundle: Path) -> VerificationReport
- (existing): docs/maestro-parity-evidence-contract.md -> queue-native-log-warning-ownership contract row
- (existing): datasets/runs/maestro-parity/{WD-2gyw,WD-bxhc,WD-cpow,WD-m0r5,WD-r81u,WD-rous}/evidence.json -> immutable accepted lane bundles

## Story Acceptance Criteria
1. [State] At merged main, the canonical checker exits 0 for these representative verified bundles: `WD-2gyw` video, `WD-bxhc` voice/character, `WD-cpow` SFX/audio post, `WD-m0r5` image, `WD-r81u` finishing, `WD-rous` music, and `consent-closeout` voice/character consent projection.
2. [State] The checker still exits nonzero for `WD-dmf2` director/editor evidence because its recorded objective gates and reviewer verdict genuinely fail; no classification may upgrade that bundle.
3. [State] Optional import fallback classification is exact and evidence-backed: module name, native log line, exact log SHA-256, and a successful output/save marker are recorded; unknown imports, changed hashes, missing success markers, and generic `ImportError` values remain fail-closed.
4. [State] No accepted output, native log, media metadata, model/reference provenance, queue result, or objective gate value is rewritten to manufacture a pass; only explicit warning ownership/contract/test/receipt data may change.
5. [State] A current checker receipt records command, commit, pass/fail result, warnings, and SHA-256 for each representative bundle, and fails closed if the receipt drifts.
6. [State] Focused checker tests, undeselected full suite, `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity, `git diff --check`, and exact-head CI pass.

## Testing Requirements
- Extend `tests/test_maestro_parity_evidence.py` with real temporary bundle fixtures; no mocks of verifier behavior.
- Include each accepted optional fallback and negative coverage for an unknown module, changed log bytes, and a fallback without a successful-output marker.
- Run the canonical checker on every representative bundle listed in AC 1 and on `WD-dmf2`.
- Run focused tests, the undeselected full suite, lint, release verification, protected parity, diff check, and exact-head CI.

## Delivery Requirements
- Record exact commands, parsed JUnit counters, checker results, commit SHA, PR, CI, unchanged media/log hashes, and AC table.
- Include `LEARNINGS:`.
- Do not contact the GPU host or regenerate evidence.

## MANDATORY SKILLS
- pvg
- tool-systematic-debugging

## nd_contract
status: new

### evidence
- Current verifier observations at main `a382f747`: WD-2gyw/WD-bxhc/consent-closeout pass; WD-cpow, WD-m0r5, WD-r81u, and WD-rous fail only on unclassified optional import fallbacks; WD-dmf2 genuinely fails objective/reviewer gates.

### proof
- [ ] Pending exact optional-warning ownership, current lane receipts, tests, and standing gates.

## Acceptance Criteria


## Design


## Notes
Observable outcome: the operator can run the canonical checker on each representative bundle and it returns an explicit pass/fail result with owned warning provenance.
## PM Decision
ACCEPTED [2026-09-29]: Independently verified PR 216 exact head, exact-head CI, scoped immutable evidence, fail-closed fallback ownership, representative lane outcomes, receipt drift behavior, and standing gates.

## nd_contract
status: accepted

### evidence
- Reviewed PR 216 head baf16edd14d4bb92e1737c1b438beee072da05a1 and CI run 36525559743 success at that exact SHA.
- Re-ran representative checker lanes, focused checker suite, receipt drift test, backlog lint, release verify, pvg verify, compile/JSON checks, protected-file parity, and whitespace checks.
- Confirmed the exact eight-path diff scope and current checker/native-log SHA-256 bindings.

### proof
- [x] AC #1 through AC #6 independently verified.

## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-29.

### proof
- [x] Story closed after accepted label was applied.


## Implementation Evidence

This standalone heading continues the preceding DELIVERED proof without replacing it. Commands run, CI/test counters, commit SHA, coverage, immutable hashes, PR, exact-head CI, AC table, and LEARNINGS remain authoritative in the preceding detailed block.

## nd_contract
status: delivered

### evidence
- Commit SHA `baf16edd14d4bb92e1737c1b438beee072da05a1`; PR 216 exact-head CI success.

### proof
- [x] All six ACs are verified in the detailed Implementation Evidence above.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-29.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

### CI/Test Results

Commands run:
- `python3 scripts/verify_maestro_parity.py datasets/runs/maestro-parity/<each representative lane and WD-dmf2>`
- `uv run --frozen --extra dev pytest -q tests/test_maestro_parity_evidence.py --junitxml=/tmp/WD-23rs-focused.xml`
- `timeout 1800 uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-23rs-full.xml`
- `pvg lint --backlog`
- `uv run --frozen --extra dev wgp release verify`
- `git diff --exit-code a382f747f31735c9eaa5eecb4bb6e1581b3403de -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
- `git diff --check`
- `pvg verify <eight changed paths> --include-tests --format=text`
- `git push origin story/WD-23rs`

Summary: checker lanes PASS/expected-fail as specified; focused 94/0/0/0; full 2127/0/0/1; lint 0/0; release ready/tag false; protected parity and whitespace PASS; PR exact-head CI PASS.
Commit SHA: baf16edd14d4bb92e1737c1b438beee072da05a1
PR: https://github.com/jmanhype/wangp-dspy/pull/216
Coverage: 82% checker-module coverage from the coverage-only run; canonical warning count 0.

## nd_contract
status: delivered

### evidence
- Story head and PR CI SHA `baf16edd14d4bb92e1737c1b438beee072da05a1`.
- Full details, hashes, warnings, AC table, and LEARNINGS are in the preceding authoritative Implementation Evidence block.

### proof
- [x] All six story ACs verified as detailed above.

## Implementation Evidence (DELIVERED)

PROOF:

### Exact commands and results

- Checker commands (one per bundle): `python3 scripts/verify_maestro_parity.py datasets/runs/maestro-parity/<lane>`
  - WD-2gyw exit 0, PASS, 5 owned mutagen warnings.
  - WD-bxhc exit 0, PASS, 0 warnings.
  - WD-cpow exit 0, PASS, 2 `OPTIONAL_IMPORT_FALLBACK` warnings.
  - WD-m0r5 exit 0, PASS, 17 `OPTIONAL_IMPORT_FALLBACK` warnings.
  - WD-r81u exit 0, PASS, 1 `OPTIONAL_IMPORT_FALLBACK` warning.
  - WD-rous exit 0, PASS, 2 `OPTIONAL_IMPORT_FALLBACK` warnings.
  - consent-closeout exit 0, PASS, 0 warnings.
  - WD-dmf2 exit 1, expected failure: objective_gate_results[21],[23],[24],[26],[27] and reviewer_verdict.decision remain failing.
- Focused checker tests: `uv run --frozen --extra dev pytest -q tests/test_maestro_parity_evidence.py --junitxml=/tmp/WD-23rs-focused.xml`
  - Parsed JUnit: tests=94, errors=0, failures=0, skipped=0, time=1.401s.
  - Includes real temporary copies of native-log bytes, all three accepted module forms, unknown-module, changed-hash, missing-success-marker, representative real bundles, WD-dmf2 negative, and receipt-drift coverage.
- Coverage-only run: global `coverage run --source=scripts.verify_maestro_parity -m pytest -q tests/test_maestro_parity_evidence.py`, then `coverage report --show-missing`
  - Coverage: 82% (493 statements, 90 missed) for the checker module.
  - Coverage environment warning observation: the global coverage executable selected Python 3.10 and emitted pytest-asyncio and LiteLLM/Pydantic deprecation warnings. The canonical frozen `uv` focused/full runs emitted no warnings; `coverage` is not installed in the frozen project environment.
- Undeselected full suite: `timeout 1800 uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-23rs-full.xml`
  - exit 0; parsed JUnit: tests=2127, errors=0, failures=0, skipped=1, time=1246.220s.
  - The sole skip is `tests/test_jobs_integration_3090.py::test_live_preflight_against_3090`, explicitly gated by `WANGP_3090=1`. It was not enabled because WD-23rs forbids GPU/SSH contact. Canonical test warnings: none.
- Backlog gate: `pvg lint --backlog`
  - PASS; scanned 151 issues; errors=0; review findings=0.
- Release gate: `uv run --frozen --extra dev wgp release verify`
  - PASS; version checks pass; tag-ready v0.1.0; tag_created=false; release=ready.
- Protected parity: `git diff --exit-code a382f747f31735c9eaa5eecb4bb6e1581b3403de -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
  - PASS; exit 0; no protected engine file changed.
- Whitespace: `git diff --check`
  - PASS; exit 0.
- Static/evidence preflight: `uv run --frozen --extra dev python -m py_compile scripts/verify_maestro_parity.py tests/test_maestro_parity_evidence.py`; JSON parse checks for all five edited/added evidence records
  - PASS.
- pvg verify: `pvg verify <eight changed paths> --include-tests --format=text`
  - `VERIFY: PASSED (2 files scanned, 0 issues)`.

### Commit, branch, PR, and exact-head CI

- Implementation commit: `ffe1e126891e547dbaa63e5ec54708698f50b7a1` (`feat(WD-23rs): own optional import fallbacks`).
- Receipt-binding/story head: `baf16edd14d4bb92e1737c1b438beee072da05a1` (`evidence(WD-23rs): bind checker lane receipt commit`).
- Branch: `story/WD-23rs`; remote head equals local head.
- PR: https://github.com/jmanhype/wangp-dspy/pull/216
- Exact-head CI: https://github.com/jmanhype/wangp-dspy/actions/runs/36525559743
  - headSha=baf16edd14d4bb92e1737c1b438beee072da05a1; conclusion=success; test duration=21m50s.
- Push command: `git push origin story/WD-23rs` (a382f747..baf16edd).

### Immutable evidence and current receipt

- Changed paths from base a382f747 are exactly the authorized eight: verifier, contract, checker tests, four lane evidence records, and new checker-lane receipt. No output, media, native log, model/reference provenance, queue result, or objective gate value was changed.
- Affected native-log SHA-256 bindings:
  - WD-cpow stable-sfx.native.log: `4c173ad03256175b37b54df2affcbccd81c927ff1d44a1ad14485c85b0557100`
  - WD-m0r5 qwen-batch.native.log: `e45615acbbdb98d786712047422b8e78ce7466f47a8c36dcc4d13596d9d93f07`
  - WD-m0r5 flux-batch.native.log: `c8b213173905d95bf7cd157542651ceda705378aabc9c0d4d5a1fc645b31952d`
  - WD-m0r5 qwen-standard-identity-attempt2.native.log: `1cbc96feaba1be561968cec016ab9fefec824909e304e822ea9fcf10ce8efc31`
  - WD-m0r5 flux-standard-identity-attempt3.native.log: `a3c9bcfadd7fe152fb1e181939a6911a50a5c218faef56ba8ec6b9e2494b62e4`
  - WD-m0r5 flux-kontext-identity-attempt2.native.log: `bdf3fb79d11419401289753103bf5f938be18d52aff58e7a2feb80490ca84aeb`
  - WD-r81u wd-r81u-attempt5.native.log: `7639781ce306941a4f35d0ab8c568fd739dd1db293bf3354fadea72add6aa21d`
  - WD-rous stable-generate.native.log: `ebca7e6ec3c24c496a4acabca67704cda7ee52aa7dd8e962247b9d7bacbfec63`
- Current checker SHA-256: `6475a33b5b06f9324f6342204198f22b0d6421bc0709c5861006fa2e801856af`.
- Current full-lane path+byte bundle identities are recorded in `datasets/runs/maestro-parity/checker-lane-receipts/evidence.json`; `verify_checker_receipt()` recomputes checker hash, bundle identities, exact warnings/diagnostics, and outcomes and has a real drift-failure test.

### AC Verification

| AC | Requirement | Evidence | Status |
|---|---|---|---|
| 1 | Seven verified representative bundles pass | Exact checker commands above; receipt records all seven PASS and exact warnings | PASS |
| 2 | WD-dmf2 still genuinely fails objective/reviewer gates | Exact checker output above; no fallback classification for WD-dmf2 | PASS |
| 3 | Exact, evidence-backed fallback ownership; unknown/hash/generic/missing marker fail | verifier `optional_import_fallbacks`, focused positive/negative real-byte tests | PASS |
| 4 | Immutable outputs/logs/provenance/gates untouched | `git diff --name-only a382f747..HEAD` contains only the eight authorized paths | PASS |
| 5 | Current receipt records command/commit/result/warnings/hashes and fails closed on drift | `checker-lane-receipts/evidence.json`, `verify_checker_receipt`, drift test | PASS |
| 6 | Focused/full/lint/release/protected/diff/CI pass | Exact commands and parsed results above; PR CI success at exact head | PASS |

LEARNINGS:

- Python `splitlines()` treats carriage returns as record boundaries but the checker deliberately counts `split("\n")` lines; fallback evidence had to be generated with checker line semantics, not shell `grep -n`.
- `flash_attn` and `piexif` could be owned by adjacent fallback/save lines, while WD-r81u required the already-completed FFmpeg output boundary before the optional `postprocessing` import failure. The three cases needed precise module-specific marker semantics rather than a module allow-list alone.
- Binding each import occurrence independently forced all 17 WD-m0r5 warnings into exact ownership rather than allowing a broad piexif exception.
- The receipt cannot safely trust a bundle filename: a path-plus-byte identity plus checker code hash catches media/log drift and silent checker changes together.
- The repository's frozen environment does not include coverage; an external global coverage interpreter introduced unrelated deprecation warnings. Canonical `uv` test runs remained warning-free, and the external-tool observation is recorded rather than hidden.

### OBSERVATIONS (unrelated)

- [CONCERN] `tests/test_jobs_integration_3090.py::test_live_preflight_against_3090` remains explicitly gated by `WANGP_3090=1`; it was not run under this story because GPU/SSH contact was forbidden.
- [CONCERN] The global coverage-only command selected Python 3.10 and emitted pytest-asyncio and LiteLLM/Pydantic deprecation warnings; no project dependency was changed.

## nd_contract
status: delivered

### evidence
- Checker implementation commit `ffe1e126891e547dbaa63e5ec54708698f50b7a1`; story/PR head `baf16edd14d4bb92e1737c1b438beee072da05a1`.
- PR `https://github.com/jmanhype/wangp-dspy/pull/216`; exact-head CI run `36525559743` success.
- Focused JUnit 94/0/0/0; full JUnit 2127/0/0/1; lint/release/protected/diff/CI all PASS.
- Current receipt and immutable lane identities are committed under `datasets/runs/maestro-parity/checker-lane-receipts/evidence.json`.

### proof
- [x] AC #1: WD-2gyw, WD-bxhc, WD-cpow, WD-m0r5, WD-r81u, WD-rous, and consent-closeout exit 0.
- [x] AC #2: WD-dmf2 exits 1 on five real objective failures plus reviewer rejection.
- [x] AC #3: exact module/path/line/hash/fallback/success ownership; unknown/hash/generic/missing-marker tests fail closed.
- [x] AC #4: only authorized warning ownership/contract/test/receipt files changed; immutable bytes and hashes unchanged.
- [x] AC #5: current machine receipt records exact command, commit, result, warnings, diagnostics, and bundle identities; drift test fails.
- [x] AC #6: focused, full, lint, release, protected parity, whitespace, and exact-head CI gates pass.

## History
- 2026-09-29T04:33:00Z dep_added: blocks WD-fay0
- 2026-09-29T04:34:03Z status: open -> in_progress
- 2026-09-29T04:34:03Z auto-follows: linked to predecessor WD-p587
- 2026-09-29T04:34:03Z claimed by dev-WD-23rs
- 2026-09-29T05:45:15Z status: in_progress -> in_progress
- 2026-09-29T05:45:15Z auto-follows: linked to predecessor WD-32hk
- 2026-09-29T05:47:40Z status: in_progress -> in_progress
- 2026-09-29T05:47:40Z auto-follows: linked to predecessor WD-dc3w
- 2026-09-29T06:04:43Z status: in_progress -> closed
- 2026-09-29T06:04:43Z dep_removed: no_longer_blocks WD-fay0

## Links
- Parent: [[WD-3nod]]
- Follows: [[WD-p587]], [[WD-32hk]], [[WD-dc3w]]
- Led to: [[WD-28ac]], [[WD-qthq]], [[WD-bw0h]], [[WD-he8i]], [[WD-1s5s]]

## Comments
