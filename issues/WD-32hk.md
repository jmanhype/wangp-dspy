---
id: WD-32hk
title: "Cloning consent matrix closeout"
status: in_progress
priority: 1
type: task
labels: [voice, character, evidence, operator-decision]
parent: WD-3nod
created_at: 2026-09-28T13:32:23Z
created_by: speed
updated_at: 2026-09-28T14:56:16Z
content_hash: "sha256:34fa117a6f9c6372238961e46f93bec8e3bc8f1694fb0f95b3ab8c23f181b439"
blocks: [WD-fay0]
follows: [WD-bxhc, WD-dc3w]
assignee: dev-WD-32hk
---

## Description
## Context

## USER INTENT
The six voice/character cells whose media and objective gates already passed should become verified only after the operator explicitly consents to cross-story cloning-reference reuse. That consent has now been given.

## Operator consent
Verbatim operator input:

> Approve

Recorded at `2026-09-28T13:20:11Z` in response to the three-way authorization question. This story uses the approval only for WD-bxhc cloning-reference reuse.

Consent scope:

- The operator approves reuse of the two WD-cpow anchors as WD-bxhc VibeVoice cloning references.
- Primary anchor: WD-cpow `inputs/target-voice.wav`, SHA-256 `b013bad88be5b44609304764aaa6b10afb9f0299d768c8abc48c2d1afd4bed18`.
- Secondary anchor: WD-cpow `outputs/wd_cpow_vibevoice_raw.prepared.wav`, SHA-256 `e371ebe7ee1ce9964657b4f34f61d32fbff2a5345bdb90add6c3e7dba1ee2175`.
- Use is limited to operator-owned research/evaluation in the WD-bxhc evidence chain.
- No redistribution, publication, training, provider spend, new inference, or use outside this consent is authorized.

## Embedded current state
At merged main `6ac1023b522726705d3ea560216f211003a1d4bd`, exactly six cells are `evidence_complete_pending_review`:

- `docs/voice-capabilities.md`: VibeVoice one-reference clone and two-reference clone.
- `docs/character-capabilities.md`: Saved voice binding image and video.
- `docs/character-capabilities.md`: Cross-mode identity preservation image and video.

WD-bxhc already records real hashed output bytes, objective gates, corrected provenance, and the only missing right: explicit cloning-reuse consent. The historical consent-rework record must remain intact as the pre-consent evidence boundary.

## OUT OF SCOPE
- No new voice generation, character generation, model download, host mutation, provider spend, training, or redistribution.
- No modification or overwrite of historical WD-bxhc or WD-cpow artifacts.
- No director structural disposition or clean-machine generated-artifact work.

## DIFF BUDGET
- About 4 files and under 300 changed LOC: voice/character matrices plus a compact consent/evidence bundle.

## Boundary Map
PRODUCES:
- datasets/runs/maestro-parity/consent-closeout/operator-consent.md -> stores verbatim, timestamped, scoped cloning-reuse consent
  spec: names both anchor hashes, the approving operator, WD-bxhc-only scope, research/evaluation constraint, and no-redistribution boundary.
- datasets/runs/maestro-parity/consent-closeout/consent-record.json -> emits machine-verifiable consent chain
  schema: links each of the six target cells to its existing output/gate evidence and both approved reference hashes.
- datasets/runs/maestro-parity/consent-closeout/evidence.json -> returns a canonical post-consent projection
  event: passes `scripts/verify_maestro_parity.py` and records all six target dispositions as `host_run_verified`.
- docs/voice-capabilities.md and docs/character-capabilities.md -> exactly the six approved cells transition from `evidence_complete_pending_review` to `host_run_verified`
  spec: links the new consent bundle while preserving the historical correction record.

CONSUMES:
- WD-bxhc: datasets/runs/maestro-parity/WD-bxhc/evidence.json -> canonical output hashes, media metadata, model/reference provenance, queue attempt, objective gates, and reviewer verdict
  source: copy or hash-reference exact accepted output/gate records; do not regenerate or mutate them.
- WD-bxhc: datasets/runs/maestro-parity/WD-bxhc/reference-consent-rework.md -> pre-consent provenance boundary
  source: the new consent record must quote or link both true-source anchors and explain that consent was absent when this record was authored.
- WD-cpow: datasets/runs/maestro-parity/WD-cpow/operator-authorization.md -> ownership and evaluation-rights provenance
  source: ownership establishes the operator's right to consent; the new `Approve` message supplies the previously missing cross-story cloning consent.

## Story Acceptance Criteria
1. [State] The new consent record verbatimly preserves `Approve`, records `2026-09-28T13:20:11Z`, identifies the operator, and names both exact reference hashes and destinations.
2. [State] The record proves byte identity between each WD-bxhc reference and its WD-cpow anchor before citing consent.
3. [State] Exactly the six named cells transition to `host_run_verified`; no other voice or character cell changes.
4. [State] A canonical evidence projection for the six target outputs passes `scripts/verify_maestro_parity.py` with zero diagnostics.
5. [Unwanted] No historical WD-bxhc/WD-cpow file is modified, no media bytes are regenerated, and no reference is used outside the recorded consent scope.
6. [State] Focused voice/character/capability tests, matrix-transition evidence, the undeselected full suite, `pvg lint --backlog`, `wgp release verify` with `release=ready` and `tag_created=false`, protected-file parity from `6ac1023b`, and `git diff --check` pass.

## Testing Requirements
- Integration verification is mandatory and must use real artifact bytes/hashes; no mocked media or consent chain.
- Verify all referenced files with SHA-256.
- Run the canonical checker on the new bundle.
- Run focused voice/character/capability tests and the undeselected full suite.
- Record coverage for any new Python helper; if documentation/evidence-only, explicitly record the coverage boundary.

## Delivery Requirements
- Record the consent hash, all reference/output hashes, matrix before/after counts, checker result, full-suite JUnit counters, commit SHA, branch, PR, and CI result.
- Include `## Implementation Evidence`, `Summary:`, `Commands run:`, `SHA:`, `### CI/Test Results`, `### AC Verification`, and `LEARNINGS:`.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Created from operator consent at `2026-09-28T13:20:11Z`, merged main `6ac1023b522726705d3ea560216f211003a1d4bd`, and accepted WD-bxhc/WD-cpow artifacts.

### proof
- [ ] Pending consent record, hash verification, six-cell matrix transition, canonical checker, and standing gates.

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence (DELIVERED)

Summary: recorded the operator's verbatim scoped `Approve`, verified both WD-cpow anchors byte-for-byte, created a canonical checker-passing consent-closeout projection, and advanced exactly the six named cells from `evidence_complete_pending_review` to `host_run_verified`.

SHA: `ec3b07360d7e142cd5c9bb0bddf177d118f423d4` on `story/WD-32hk`.

Branch: `story/WD-32hk` (pushed to `origin/story/WD-32hk`).

PR: https://github.com/jmanhype/wangp-dspy/pull/214

Exact-head CI: CI run https://github.com/jmanhype/wangp-dspy/actions/runs/36436770508 completed `success` for `ec3b07360d7e142cd5c9bb0bddf177d118f423d4`; job `test` completed successfully in 22m14s.

### CI/Test Results

Commands run:
- `python3 scripts/verify_maestro_parity.py datasets/runs/maestro-parity/consent-closeout`
- `python3 /tmp/wd32hk_verify_consent.py`
- `python3 /tmp/wd32hk_matrix_check.py`
- `uv run --frozen --extra dev pytest -q tests/test_speech_capabilities.py tests/test_vibevoice.py tests/test_character_capabilities.py tests/test_maestro_parity_evidence.py tests/test_content_and_capabilities.py --junitxml=/tmp/wd32hk-focused.xml`
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd32hk-fullsuite.xml`
- `pvg lint --backlog`
- `uv run --frozen --extra dev wgp release verify --json`
- `git diff --exit-code 6ac1023b522726705d3ea560216f211003a1d4bd -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`
- `git diff --exit-code 6ac1023b522726705d3ea560216f211003a1d4bd -- datasets/runs/maestro-parity/WD-bxhc datasets/runs/maestro-parity/WD-cpow`
- `git diff --check`
- `pvg verify datasets/runs/maestro-parity/consent-closeout/operator-consent.md datasets/runs/maestro-parity/consent-closeout/consent-record.json datasets/runs/maestro-parity/consent-closeout/evidence.json docs/voice-capabilities.md docs/character-capabilities.md --format=text`

Summary:
- Canonical checker: PASS with zero diagnostics and zero owned warnings.
- Consent/hash verifier: PASS; all five historical source records and both source/destination/projection anchor chains matched.
- Matrix transition: PASS; exactly six status-cell changes, no other status-cell changes.
- Focused suite: 225 tests, 0 errors, 0 failures, 0 skipped.
- Undeselected full suite: 2,109 tests, 0 errors, 0 failures, 1 skipped. No tests were deselected. The sole skip is the pre-existing explicit `tests.test_jobs_integration_3090.test_live_preflight_against_3090` optional live-host gate; enabling it would violate this story's no-host-contact/no-host-mutation boundary.
- `pvg lint --backlog`: PASS, 150 issues scanned, 0 errors, 0 review findings.
- Release verify at the clean exact commit: `release=ready`, `tag_created=false`.
- Protected-file parity from `6ac1023b`: PASS with empty diff.
- Historical WD-bxhc/WD-cpow parity from `6ac1023b`: PASS with empty diff.
- `git diff --check`: PASS.
- `pvg verify`: `VERIFY: PASSED (0 files scanned, 0 issues)` for the explicit documentation/evidence paths.

Coverage boundary: documentation/evidence-only change; no new Python helper was committed, so no new Python coverage percentage applies. Real artifact-byte integration verification is supplied by the canonical checker and hash/cmp evidence rather than mocks.

### Hash Evidence

- `operator-consent.md`: `0b9be707e7399c8593df2d3a70fea93713d13dffebc70a67a02b5e43af012705`
- `consent-record.json`: `86e8640270f11255faa9eedea5ba5a21eb4d977398f4757aeb4d26bb412f7341`
- `evidence.json`: `1c52dc2eb2221aea135ad0890a8bdf23fca5937730b7986298f733ef6f7aa4d6`
- Primary anchor/source/destination/projection SHA-256: `b013bad88be5b44609304764aaa6b10afb9f0299d768c8abc48c2d1afd4bed18`
- Secondary anchor/source/destination/projection SHA-256: `e371ebe7ee1ce9964657b4f34f61d32fbff2a5345bdb90add6c3e7dba1ee2175`
- Clone-one output SHA-256: `23bdc389f731615ad1e5f566320a0b36240d98730d69dc8633069bccc4191d2b`
- Clone-two output SHA-256: `b9bec33bc91958f1fa39461cdd0f842f683e501cabd0ee87e15dc3a900c45024`
- Character image SHA-256: `da4cbd9752c85a3eb7baaf9feba95533269d5e74d676a59e9d6660f1ba9fcfb6`
- Character video SHA-256: `1cba8c8a7e0b2d43142cc053766ca729850ebb5b3beaa0ba02e99df8252eca81`
- Saved-voice package SHA-256: `232866634eee225f4a7bb05216d53861b49feb81697bcbe6e994f4e8435ef3ef`

Matrix before/after:
- Voice: verified `2 -> 4`; pending `2 -> 0`; unsupported remained `2`.
- Character: verified `14 -> 18`; pending `4 -> 0`; unsupported remained `2`.
- Changed cells: exactly 6.

### AC Verification

| AC # | Requirement | Evidence | Status |
|---|---|---|---|
| 1 | Verbatim `Approve`, timestamp, operator, exact hashes, destinations, and limits | `operator-consent.md` and `consent-record.json` | PASS |
| 2 | Byte identity for both WD-bxhc references and WD-cpow anchors before consent application | `cmp --silent` plus matching source/destination/projection SHA-256 values | PASS |
| 3 | Exactly six named cells transition; no other voice/character status cell changes | `/tmp/wd32hk_matrix_check.py` output and docs diff | PASS |
| 4 | Canonical six-cell projection passes checker with zero diagnostics | `PASS ... owned_warnings=0` | PASS |
| 5 | No historical artifact mutation, media regeneration, or out-of-scope use | Historical parity diff empty; copied exact bytes only; no host/network generation operation | PASS |
| 6 | Required tests and standing gates pass | Focused/full JUnit counters, lint, release, parity, and diff-check evidence above | PASS |

LEARNINGS:
- The strict bundle resolver cannot reference sibling historical bundles, so a checker-passing consent projection must carry exact read-only byte copies rather than relative traversal or symlink shortcuts.
- The non-media `.wgpvoice` saved-binding artifact belongs under hashed reference provenance; limiting `output` to four real image/audio/video artifacts avoids falsely labeling a package as media.
- macOS `cmp` rejects the invented `--bytes-bytes-only` spelling; `cmp --silent` is the portable exact-byte command used in the final evidence.
- Release verification intentionally failed on the dirty authoring tree and passed only after the exact implementation commit, which is the correct clean-tree boundary.

### OBSERVATIONS (unrelated)
- `pvg notes search "WD-32hk consent closeout"` failed before implementation because the configured `Claude` vault was unavailable (`vlt: vault "Claude" not found`). No story data was changed and the canonical `pvg issues show` path remained healthy.

### DISCOVERED_BUG
- title: pvg notes search selects unavailable Claude vault
- context: Running the developer-skill vault-context search in the WD-32hk worktree returned `pvg notes: vlt vault=Claude ... vault "Claude" not found. Available: vault, .vault, nd-vault, Obsidian Vault, Brand OS (AI Video Factory)`. The canonical live issue and delivery operations worked through `pvg issues` and `pvg nd`; only the optional notes search failed.
- affected_files: none
- discovered_during: WD-32hk

## nd_contract
status: delivered

### evidence
- Commit: `ec3b07360d7e142cd5c9bb0bddf177d118f423d4`
- PR: https://github.com/jmanhype/wangp-dspy/pull/214
- CI: success at the exact head, run `36436770508`
- Checker: PASS, zero diagnostics/warnings
- Focused: 225/0/0/0; full undeselected: 2109 tests, 0 errors, 0 failures, 1 explicit optional live-host skip
- Lint/release/parity/diff gates: PASS

### proof
- [x] AC #1: scoped consent record is verbatim and exact.
- [x] AC #2: both anchors and projections are byte-identical.
- [x] AC #3: exactly the six named cells transition.
- [x] AC #4: canonical projection passes with zero diagnostics.
- [x] AC #5: historical artifacts remain unchanged and no out-of-scope use occurred.
- [x] AC #6: all required tests and standing gates pass.

## History
- 2026-09-28T13:32:26Z dep_added: blocks WD-fay0
- 2026-09-28T13:33:03Z status: open -> in_progress
- 2026-09-28T13:33:04Z auto-follows: linked to predecessor WD-dc3w
- 2026-09-28T13:33:04Z claimed by dev-WD-32hk

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-bxhc]], [[WD-dc3w]]

## Comments
