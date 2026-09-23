---
id: WD-6ml6
title: "Speech, reference voice cloning, portable character voices, and a second TTS engine"
status: closed
priority: 2
type: feature
labels: [capability, accepted]
parent: WD-t741
created_at: 2026-09-22T20:24:44Z
created_by: speed
updated_at: 2026-09-23T06:49:08Z
content_hash: "sha256:5f4ab89f704aa795f5559e7241fe9f6c0111598770cc646197d914e47e5ffda9"
assignee: dev-WD-6ml6
follows: [WD-pcen, WD-soa4]
closed_at: 2026-09-23T06:49:07Z
close_reason: "Accepted: exact head b33e8b8; 34/34 targeted and 1817 full tests (1 pre-existing skip), planned-only matrix, immutable non-executable plans, no host calls, clean worktree."
---

## Description

## USER INTENT
Observable outcome: Wangp can generate speech, clone a voice from one or two references, split longer scripts by real segment limits and assemble them, use a second independent TTS engine, and save portable character voices.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- Existing VibeVoice work under `predict/` and accepted speech/AV gates is the primary lane; this story turns it into a broad, portable `wgp` voice capability and adds a genuinely independent fallback engine.
- A saved character voice is a portable manifest plus consent/provenance constraints, not an opaque host path.
- Segment assembly must preserve speaker identity, ordering, silence boundaries, hashes, and downstream AV synchronization.

## OUT OF SCOPE
- Cloning a real person without recorded authorization/consent or using unrelated reference files smuggled into a worker.
- Treating a TTS vendor alias as the required second engine; the fallback must be independently implemented and separately run.

## DIFF BUDGET
Roughly 10 files, under 800 authored changed LOC, excluding voices, weights, and audio.

## Boundary Map
PRODUCES:
- predict/speech_capabilities.py -> typed speech request with text/language/style, zero/one/two references, segment policy, TTS engine, and target voice package
- services/voice/segment_compiler.py -> deterministic segment splitting at real engine limits plus ordered assembly plan
- host/speech_backends.py -> primary and independent secondary TTS adapters with fail-closed model/reference checks
- predict/voice_registry.py -> portable character-voice packages containing manifest, hashes, reference roles, consent/licence constraints, and compatibility profile
- wangp/voice_cli.py -> `wgp voice plan|generate|clone|export|import` command implementation and submit boundary
- docs/voice-capabilities.md -> engine matrix, segment limits, cloning consent, portability format, and evidence policy
- tests/test_voice_capabilities.py -> real-process voice/queue/package coverage; no mocks
- datasets/runs/maestro-parity/WD-6ml6/ -> authorized speech/clone run bundles

CONSUMES:
- predict/vibevoice.py -> existing primary speech generation seam
  spec: existing primary speech generation seam
- predict/audio_prep.py -> existing audio preparation behavior
  spec: existing audio preparation behavior
- predict/speaker_manifest.py -> speaker identity contract
  spec: speaker identity contract
- predict/content_brief.py -> typed character/dialogue contract
  spec: typed character/dialogue contract
- services/jobs/queue.py -> durable queue record and attempt transitions
  spec: durable queue record and attempt transitions
- services/jobs/preflight.py -> typed missing voice/model failures
  spec: typed missing voice/model failures
- qc/audio_critic/whisper_gate.py -> real transcript evidence boundary
  spec: real transcript evidence boundary
- qc/audio_critic/av_sync_gate.py -> real AV synchronization evidence boundary
  spec: real AV synchronization evidence boundary
- wangp/cli.py -> stable verb registration and exit-code contract
  spec: stable verb registration and exit-code contract


## Required Outcomes
### no-GPU verifiable now
- Real CLI tests normalize plain speech and one/two-reference cloning, reject missing consent or wrong reference count/format, split scripts using each engine’s declared limit, and emit an exact assembly order without synthesis.
- Portable voice export/import round-trips through a real temporary directory and verifies manifest/hashes; imported paths are namespace-safe and do not expose operator secrets.
- A real temporary queue stores text hash, segment map, engine, voice package hash, and output target; malformed text, over-limit single segments, and missing voices produce typed exit-2 failures before host contact.
- Dry-run reconstruction reproduces all segments and engine settings; docs mark synthesis and secondary-engine output unverified until runs exist.

### requires an authorized host render
- Separately authorized host runs synthesize plain speech on both engines, one-reference and two-reference clones, and one over-limit script whose real segments are assembled in order.
- Bundles retain authorization/consent provenance, references, commands, queue attempts, output hashes, ffprobe metadata, transcript evidence, and portable package linkage.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_voice_capabilities.py -q` with real files/CLI/queue and no mocks.
- Use real reference audio fixtures and deliberately exceed one declared segment limit to test actual typed splitting.
- Authorized speech bundles are verified by ffprobe, hashes, and existing transcript tooling; no synthetic audio is committed to pass tests.

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
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-23.

### proof
- [x] Story closed after accepted label was applied.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence
Summary: Delivered the no-GPU speech planning slice only: typed plain-speech, one-reference cloning, two-reference cloning, independent Chatterbox fallback, real engine segment ceilings with ordered assembly accounting, immutable model/reference provenance, per-engine normalization, portable character packages with appearance/voice bindings, immutable non-executable segment records, typed exit-2 failures, and seed-based reconstruction. No render, host access, SSH, GPU work, model download, generated-audio claim, measured output claim, or gate semantic change occurred.
Commands run:
- `uv run --frozen --extra dev pytest tests/test_speech_capabilities.py -q --junitxml=/tmp/wd6ml6-targeted-final.xml` -> exit 0; parsed JUnit tests=34 failures=0 errors=0 skipped=0.
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd6ml6-full-final.xml` -> exit 0; parsed JUnit tests=1817 failures=0 errors=0 skipped=1.
- Real CLI evidence: human plus JSON for VibeVoice speech, one-reference clone, two-reference clone, Chatterbox secondary speech, portable export/import, durable planning/reconstruction, and all 27 typed failure classes; `/tmp/wd6ml6-cli-evidence.json`, SHA256 `a08c4b3bfc9f8d12df65ae60d6c1759db9c3ba11cc3a7bcc4a5d3df1de5d9529`.
- Queue/admission/reconstruction evidence: two immutable records for two requested segments, update/delete rejected, planning `next_admissible=null`, genuine render job admitted, reconstruction `all_match=true` / `hidden_mutation=false`, datasets unchanged, and zero shadowed host invocations; `/tmp/wd6ml6-queue-evidence.json`, SHA256 `3a4ad242376107458a3d23a85408f4eafe1e4305b2decbc4c8b32e9cef96f185`.
- JUnit SHA256: targeted `847caa37e1d18bbfd218877d362e507c2826048431dc86379fb85c3d17fa5b47`; full `b068fefd8dee257b9ce5c0c7f1f7e8d5caa45decb8aa2a4f06a7d7f2fac6fcad`.
- `git diff --exit-code -- datasets` and `git diff --exit-code origin/main -- datasets` -> exit 0; zero changed dataset files.
- `uv build --out-dir /tmp/wd6ml6-dist.k5gHds` -> exit 0; exactly one wheel `590aea555a25901f8be85ed6feba059c9c88a2046c428757f3436be88f4e02f0` and one sdist `5b72828ca38cccf94762c6123672d2b2ab57a9746f8e3287ef7c6823ccf2a44e`.
- `git fetch origin main && git rebase origin/main` -> branch already up to date; no `wangp/cli.py` conflict.
- `git push -u origin story/WD-6ml6` -> success; `gh pr create` -> https://github.com/jmanhype/wangp-dspy/pull/168.
- `gh api repos/jmanhype/wangp-dspy/commits/b33e8b8b04314cb2eee0158fcc6aa48545751010/check-runs` -> check `test` completed/success.
SHA: b33e8b8b04314cb2eee0158fcc6aa48545751010

### CI/Test Results
- Targeted speech suite: tests=34, passed=34, failures=0, errors=0, skipped=0, command exit=0.
- Full suite: tests=1817, passed=1816, failures=0, errors=0, skipped=1 (pre-existing), command exit=0.
- Build: command exit=0; one wheel and one sdist with SHA256 values recorded above.
- GitHub check `test` on exact head `b33e8b8`: completed/success.

### AC Verification
| AC | Result | Evidence |
|---|---|---|
| Typed plain speech and one/two-reference cloning normalize through real CLI without synthesis | pass | `tests/test_speech_capabilities.py` representative mode cases; targeted tests=34/34; no assembled audio created |
| Independent second TTS engine and per-engine settings normalize fail-closed | pass | `chatterbox/chatterbox_multilingual` adapter plus manifest/settings tests; VibeVoice and Chatterbox rows remain planned |
| Real engine segment limits produce ordered per-segment records and assembled-output accounting | pass | two requested segments with order `[1,2]`, text hashes, source/segment character counts, silence count/duration, and planned output target |
| Durable records are immutable, non-executable, and un-drainable by real admission while genuine render remains admitted | pass | SQLite update/delete triggers reject mutation; `JobQueue.next_admissible=null` before and genuine job ID after genuine submission |
| Every implemented incomplete/unsupported class has typed exit 2, remediation, and next command | pass | real subprocess coverage and captured output for all 27 diagnostic classes |
| Portable saved-character definitions round-trip with appearance/voice binding and namespace-safe import | pass | real `.wgpvoice` ZIP export/import test verifies manifest, package/reference hashes, appearance binding, and canonical destination names |
| Seed-based dry-run reconstruction has hash equality without hidden mutation | pass | all reconstructed segment settings hashes match; `all_match=true`, `hidden_mutation=false` |
| Documentation and matrix remain honest planned-only boundaries | pass | `docs/voice-capabilities.md`; all rows planned; no generation evidence claimed |
| Committed datasets remain byte-identical and no shadowed host command is invoked | pass | dataset diffs exit 0; shadowed ssh/curl/wget/nvidia-smi call log empty |
| Authorized synthesis on VibeVoice and Chatterbox | not verified - requires authorized host run | no model execution or measured audio exists |
| Authorized one-reference and two-reference clone output | not verified - requires authorized host run | no model execution or measured audio exists |
| Authorized over-limit script synthesis and ordered assembly | not verified - requires authorized host run | assembly is planned only; no ffprobe/transcript/AV evidence exists |
| Portable package linked to an authorized generated voice | not verified - requires authorized host run | package provenance is validated but no generated target audio exists |

## nd_contract
status: delivered

### evidence
- Branch `story/WD-6ml6`, commit `b33e8b8b04314cb2eee0158fcc6aa48545751010`, PR #168.
- Targeted suite 34/34 passed; full suite 1816 passed plus 1 pre-existing skipped; CI `test` success.
- One wheel and one sdist built with hashes recorded above.

### proof
-[x] NOGPU-1: typed speech, one-reference cloning, two-reference cloning, and independent second-engine planning
-[x] NOGPU-2: real engine segment limits, ordered assembly accounting, and per-segment durable records
-[x] NOGPU-3: per-backend normalization and fail-closed engine/mode pairing
-[x] NOGPU-4: immutable non-executable records that the real admission path cannot drain
-[x] NOGPU-5: typed exit-2 remediation and next command for every implemented failure class
-[x] NOGPU-6: portable character export/import with appearance/voice binding and hash verification
-[x] NOGPU-7: seed-based reconstruction hash equality without hidden mutation
-[x] NOGPU-8: planned-only docs/matrix, unchanged datasets, and no host/GPU/model-download work
-[x] NOGPU-9: no generated-audio, measured-output, transcript, or AV-sync claim

## History
- 2026-09-22T20:24:45Z dep_added: blocks WD-fasw
- 2026-09-22T20:24:45Z dep_added: blocks WD-tkuz
- 2026-09-22T20:24:47Z dep_added: blocks WD-eq1i
- 2026-09-22T20:27:37Z dep_added: blocks WD-gc09
- 2026-09-23T05:41:42Z status: open -> in_progress
- 2026-09-23T05:41:42Z auto-follows: linked to predecessor WD-pcen
- 2026-09-23T05:41:42Z claimed by dev-WD-6ml6
- 2026-09-23T06:30:48Z status: in_progress -> in_progress
- 2026-09-23T06:30:48Z auto-follows: linked to predecessor WD-soa4
- 2026-09-23T06:49:07Z status: in_progress -> closed
- 2026-09-23T06:49:08Z dep_removed: no_longer_blocks WD-fasw
- 2026-09-23T06:49:08Z dep_removed: no_longer_blocks WD-tkuz
- 2026-09-23T06:49:08Z dep_removed: no_longer_blocks WD-eq1i
- 2026-09-23T06:49:08Z dep_removed: no_longer_blocks WD-gc09

## Links
- Parent: [[WD-t741]]
- Follows: [[WD-pcen]], [[WD-soa4]]

## Comments
