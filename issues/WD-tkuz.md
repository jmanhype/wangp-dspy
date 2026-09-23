---
id: WD-tkuz
title: "Portable characters and continuity across image and video generation"
status: closed
priority: 2
type: feature
labels: [capability, accepted]
parent: WD-t741
created_at: 2026-09-22T20:24:44Z
created_by: speed
updated_at: 2026-09-23T09:16:30Z
content_hash: "sha256:f579e1267b9cab99a647df2d6ad475bf771c420494a93fa3b4045629a3e9e861"
was_blocked_by: [WD-6tox, WD-pcen, WD-6ml6]
assignee: dev-WD-tkuz
follows: [WD-6tox, WD-pcen, WD-6ml6, WD-soa4]
closed_at: 2026-09-23T09:16:29Z
close_reason: "Accepted at 308b587c: independent round-trip/hash/continuity/durable-record checks passed; 33+5+1852 tests green; CI, build, read-only, command-drift, and delivery proof 9/9 passed."
---

## Description

## USER INTENT
Observable outcome: reusable character definitions carry appearance and voice, share as portable files, recover native-resolution views, bind to saved voices, and are reused consistently by both image and video modes.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- Typed briefs and speaker manifests already identify characters, and the entity registry records deterministic identity constraints; this story creates the reusable portable product object and generation bindings.
- Native-resolution recovery must preserve original bytes/provenance and must not upscale or silently substitute a rendered thumbnail as native.
- Continuity is evidence-based: identity gates and cross-mode hashes/state links, not a claim embedded in a prompt.

## OUT OF SCOPE
- Creating a real-person deepfake or a named public character without recorded authorization and licence review.
- Hiding character voice consent or appearance licence metadata inside a host-only model directory.

## DIFF BUDGET
Roughly 9 files, under 700 authored changed LOC, excluding character assets and generated media.

## Boundary Map
PRODUCES:
- predict/character_packages.py -> portable typed schema for identity, appearance assets, native-source links, voice binding, constraints, and version
- services/characters/package_service.py -> import/export, hash verification, native-view recovery, and compatibility checks
- predict/image_capabilities.py and predict/video_capabilities.py integration points -> explicit character-reference binding for both modes
- wangp/character_cli.py -> `wgp character create|show|export|import|recover|bind-voice` command implementation
- docs/character-packages.md -> portable format, consent/licence fields, native-resolution semantics, and cross-mode usage
- tests/test_character_packages.py -> real-process package round-trip coverage; no mocks
- datasets/runs/maestro-parity/WD-tkuz/ -> authorized cross-mode character continuity bundles

CONSUMES:
- predict/content_brief.py -> typed character and plate contract
  spec: typed character and plate contract
- predict/speaker_manifest.py -> speaker identity contract
  spec: speaker identity contract
- predict/voice_registry.py -> saved portable voice package
  spec: saved portable voice package
- docs/entity-registry.md -> existing deterministic identity-governance rules
  spec: existing deterministic identity-governance rules
- qc/audio_critic/vision_judge.py -> identity-vision evidence boundary
  spec: identity-vision evidence boundary
- predict/image_capabilities.py -> image request compilation and reference binding
  spec: image request compilation and reference binding
- predict/video_capabilities.py -> video request compilation and continuity binding
  spec: video request compilation and continuity binding
- services/jobs/queue.py -> durable queue record and attempt transitions
  spec: durable queue record and attempt transitions
- services/jobs/preflight.py -> typed missing package/reference failures
  spec: typed missing package/reference failures
- wangp/cli.py -> stable verb registration and exit-code contract
  spec: stable verb registration and exit-code contract


## Required Outcomes
### no-GPU verifiable now
- Real CLI round-trip creates a character package, exports it to a portable archive/file, imports it in a clean temporary directory, verifies all asset hashes, and fails typed on tampering or missing native source.
- Native-resolution recovery resolves and hashes the recorded source view without transcoding; if the source is unavailable it emits an actionable missing-asset diagnostic rather than substituting a derivative.
- Character binding to a saved voice is represented in image/video dry-run plans with explicit package and voice hashes; duplicate IDs, incompatible modes, and absent bindings fail typed.
- No identity-preservation capability is marked verified before authorized image and video runs.

### requires an authorized host render
- Separately authorized runs reuse the same portable character in image generation/edit and video create/extend operations, with bound saved voice where speech is involved.
- Bundles include character package/voice hashes, native sources, model provenance, commands, output hashes, identity-gate evidence, and reviewer decisions.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_character_packages.py -q`, real archive/file/CLI/queue processes with no mocks.
- Deliberately alter one real package byte and prove import fails with the exact hash mismatch.
- Authorized cross-mode artifacts are reviewed through their recorded identity gates; no identity claim may be prompt-only.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must use `pvg story deliver`, paste real command output, and provide an AC table plus hashes for every produced artifact and read-only input.
- A GPU-dependent claim may be made only from a recorded run bundle with command, repository commit, model/asset provenance, queue record, exit status, output hashes, QC/gate evidence, and operator authorization for that run. A plan, prompt, unit test, or intention is not generation evidence.
- No story may silently download a model, contact a host, use a paid provider, or claim a capability the matrix marks unverified.

## nd_contract
status: new

### evidence
- Created 2026-09-22 under epic WD-t741 from the Maestro v2.3.0 capability inventory.

### proof
- [ ] Pending implementation and independent PM acceptance.


## Acceptance Criteria


## Design


## Notes


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Summary: Continued and preserved commit ff4e5d7/b634e25, then added hash-verified portable .wgpcharacter export/import, saved-voice binding, native-source recovery, duplicate-free registry resolution, image/video continuity validation, immutable non-executable character plan records, seed-based reconstruction, the wgp character verb, capability documentation, and the README verb-map entry required by the new drift test. Planning only; no media generation or host work.

Commands run:
- git log --oneline -2
- uv run --frozen --extra dev pytest tests/test_character_capabilities.py -q
- git push -u origin story/WD-tkuz
- git fetch origin main && git rebase origin/main
- uv run --frozen --extra dev pytest tests/test_readme_quickstart.py -q -- exit 0, parsed 5 passed / 0 failed / 0 errors / 0 skipped
- uv run --frozen --extra dev pytest tests/test_character_capabilities.py -q --junitxml=/tmp/wd-tkuz-evidence/targeted.xml -- exit 0, parsed 33 passed / 0 failed / 0 errors / 0 skipped
- uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-tkuz-evidence/full-final-308b587.xml -- exit 0, parsed 1852 passed / 1 skipped / 0 failed / 0 errors
- /tmp/wd_tkuz_generate_evidence.py -- captured human and JSON round-trip plus 29 typed failure scenarios; exact one-byte package-member mismatch metadata; zero shadowed ssh/curl/wget/nvidia-smi calls; datasets digest 7fc0a50d44f61afc9cd4af55efd34864cd370740d4d562a39612a77fe6a33183 unchanged
- uv build --out-dir /tmp/wd-tkuz-evidence/build-308b587 -- exit 0, exactly one wheel and one sdist
- gh pr create ... -- https://github.com/jmanhype/wangp-dspy/pull/171
- gh api repos/jmanhype/wangp-dspy/commits/308b587ce6f4e575e5db21bac337579f7dff98eb/check-runs -- test completed/success
- git diff --check origin/main...HEAD -- exit 0
SHA: 308b587ce6f4e575e5db21bac337579f7dff98eb

### CI/Test Results

- Targeted pytest at exact head: exit 0; tests=33, failures=0, errors=0, skipped=0.
- Full pytest at exact head: exit 0; tests=1852, failures=0, errors=0, skipped=1.
- README drift test: exit 0; 5 passed.
- Build: exit 0; wheel=1, sdist=1; wheel SHA-256 ebeeaac00c1172831c34196bac1eb2e105f2381e74daf08cea974a3113b9b5b4; sdist SHA-256 2300244d4446179d71db5880496318e69270c6cf4323c2c1b60b2310de29a95d.
- GitHub check test at exact head 308b587ce6f4e575e5db21bac337579f7dff98eb: completed, conclusion success.
- Queue evidence: character_plan_records=1, jobs table absent in plan DB, update/delete rejected, real admission path selected zero plan rows, and a genuine render job remained next-admissible.
- Reconstruction evidence: recorded and reconstructed binding/seed hashes matched; hidden_mutation=false; package and database bytes unchanged.

### AC Verification

| AC | Result | Evidence |
| --- | --- | --- |
| Portable package appearance plus saved voice round-trip with stable hashes and registry identity resolution | Pass | tests/test_character_capabilities.py real CLI export/import/show/resolve; repeated package digest equal; evidence summary |
| Tampering and missing assets fail typed with exact hashes | Pass | one changed appearance-member byte rejected with expected/actual SHA-256; missing native source typed; 29 failure captures |
| Native-resolution recovery is exact-byte and fail-closed | Pass | source and recovered hashes equal, transcoded=false/substituted_derivative=false; unavailable source rejected |
| Image/video requests carry explicit appearance/voice/package hashes and reject identity, mode, duplicate, ambiguous, and binding mismatches | Pass | image and video real CLI dry-runs plus parametrized typed exit-2 diagnostics |
| Durable plans are immutable, non-executable, non-drainable, and reconstructible | Pass | separate character_plan_records table, update/delete triggers, JobQueue/JobExecutor proof, genuine job admissible, hash match |
| Seed-based dry-run reconstruction is read-only with no hidden mutation | Pass | binding/seed reconstruction hashes equal; database/package and datasets digests unchanged |
| CLI registration, README verb map, and planning-only capability docs are complete | Pass | two-line wangp/cli.py registration; README drift suite passed; every docs matrix row planned |
| No identity-preservation or generated-media capability is claimed | Pass | docs and CLI summary set planned / false; no generation bundle exists |
| Authorized image and video reuse with generated media and identity gates | not verified - requires authorized host run | No GPU/host render was requested or executed in this lane |

## nd_contract
status: delivered

### evidence
- Branch story/WD-tkuz pushed at 308b587ce6f4e575e5db21bac337579f7dff98eb.
- PR 171 exact-head GitHub check completed with success.
- Targeted/full local parsed counters and build artifacts recorded above.

### proof
- [x] Portable appearance plus saved-voice .wgpcharacter format writes, reads, round-trips, and hashes stably.
- [x] Registry resolves unique character/speaker identity and rejects duplicate or ambiguous identities.
- [x] Image/video continuity requests expose package/appearance/voice hashes and fail typed on every mismatch class with remediation and next command.
- [x] Native-source recovery copies exact bytes only and never substitutes a derivative.
- [x] One changed real package member byte fails import with exact expected/actual hashes.
- [x] Planning records are immutable and outside the executable jobs table while genuine render admission remains possible.
- [x] Seed-based reconstruction matches binding/seed hashes without package, database, datasets, or hidden mutation.
- [x] wgp character registration, README verb map, and all-planned capability boundary are covered by real-process tests.
- [x] No GPU, SSH, download, renderer, queue gate change, or generated-media claim was made.


## History
- 2026-09-22T20:24:45Z dep_added: blocked_by WD-pcen
- 2026-09-22T20:24:45Z dep_added: blocked_by WD-6ml6
- 2026-09-22T20:24:45Z dep_added: blocked_by WD-6tox
- 2026-09-22T20:24:46Z dep_added: blocks WD-8ioj
- 2026-09-22T20:24:47Z dep_added: blocks WD-eq1i
- 2026-09-22T20:27:37Z dep_added: blocks WD-gc09
- 2026-09-22T22:50:10Z dep_removed: was_blocked_by WD-6tox
- 2026-09-23T04:22:27Z dep_removed: was_blocked_by WD-pcen
- 2026-09-23T06:49:08Z dep_removed: was_blocked_by WD-6ml6
- 2026-09-23T06:51:49Z status: open -> in_progress
- 2026-09-23T06:51:49Z auto-follows: linked to predecessor WD-6tox
- 2026-09-23T06:51:49Z auto-follows: linked to predecessor WD-pcen
- 2026-09-23T06:51:49Z auto-follows: linked to predecessor WD-6ml6
- 2026-09-23T06:51:49Z claimed by dev-WD-tkuz
- 2026-09-23T08:41:35Z status: in_progress -> in_progress
- 2026-09-23T08:41:35Z auto-follows: linked to predecessor WD-soa4
- 2026-09-23T09:16:29Z status: in_progress -> closed
- 2026-09-23T09:16:29Z dep_removed: no_longer_blocks WD-8ioj
- 2026-09-23T09:16:29Z dep_removed: no_longer_blocks WD-eq1i
- 2026-09-23T09:16:29Z dep_removed: no_longer_blocks WD-gc09

## Links
- Parent: [[WD-t741]]
- Was blocked by: [[WD-6tox]], [[WD-pcen]], [[WD-6ml6]]
- Follows: [[WD-6tox]], [[WD-pcen]], [[WD-6ml6]], [[WD-soa4]]

## Comments
