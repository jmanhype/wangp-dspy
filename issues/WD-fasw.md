---
id: WD-fasw
title: "Sound effects, revoice, and audio refinement with video held fixed"
status: open
priority: 2
type: feature
labels: [capability, rejected]
parent: WD-t741
created_at: 2026-09-22T20:24:44Z
created_by: speed
updated_at: 2026-09-23T08:35:25Z
content_hash: "sha256:ae1334db7eb4db9084d8d3e34f08544de8d39033da0983827ba3f91501d767b9"
blocks: [WD-gc09]
was_blocked_by: [WD-6tox, WD-soa4, WD-6ml6]
follows: [WD-6tox, WD-soa4, WD-6ml6, WD-pcen]
---

## Description

## USER INTENT
Observable outcome: Wangp can generate sound effects, revoice an existing clip while preserving its visual track, and run an audio-refinement pass that leaves video bytes fixed.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- This is a distinct audio-post lane: it consumes generated or committed media and must make byte-level before/after claims only with hashes and ffprobe evidence.
- Maestro’s H3 Audio Refinement belongs to the video-backend matrix; this story owns generic post-generation revoice/refinement and proves the video-fixed invariant independently.

## OUT OF SCOPE
- Changing visual encoding, cropping, frame rate, or QC decisions under the name of audio refinement.
- Replacing a failed speech generation with an unrecorded manual edit.

## DIFF BUDGET
Roughly 8 files, under 600 authored changed LOC, excluding models and media.

## Boundary Map
PRODUCES:
- predict/audio_post.py -> typed sound-effect, revoice, and refinement requests with source hashes and target stream/layout
- services/audio/post_compiler.py -> deterministic post jobs and video-fixed output naming
- host/audio_post_backends.py -> fail-closed SFX/revoice/refinement adapters
- predict/assembler.py additions or a narrowly scoped peer -> real stream replacement/mixing path with hash accounting
- wangp/audio_cli.py -> `wgp audio sfx|revoice|refine` command implementation and authorized execution boundary
- docs/audio-post.md -> source/output contract, video-fixed proof, and sound-effect evidence matrix
- tests/test_audio_post.py -> real-process audio-post plan/queue coverage; no mocks
- datasets/runs/maestro-parity/WD-fasw/ -> authorized SFX/revoice/refinement bundles

CONSUMES:
- predict/audio_dataplane.py -> existing audio routing contract
  spec: existing audio routing contract
- predict/audio_manifest.py -> existing audio metadata contract
  spec: existing audio metadata contract
- predict/audio_prep.py -> existing audio preparation behavior
  spec: existing audio preparation behavior
- predict/speech_capabilities.py -> authorized voice/revoice engine selection
  spec: authorized voice/revoice engine selection
- services/jobs/queue.py -> durable queue record and attempt transitions
  spec: durable queue record and attempt transitions
- services/jobs/preflight.py -> typed missing source/model failures
  spec: typed missing source/model failures
- qc/audio_critic/profiles.py -> existing audio evidence profile
  spec: existing audio evidence profile
- wangp/cli.py -> stable verb registration and exit-code contract
  spec: stable verb registration and exit-code contract


## Required Outcomes
### no-GPU verifiable now
- Real CLI tests compile SFX, revoice, and refinement requests from committed media hashes and reject absent/ambiguous streams, mismatched duration, missing voice, or invalid target layout before any host call.
- The plan explicitly marks the source video hash as immutable and names the intended output path; a real queue record preserves that invariant.
- Dry-run reconstruction reproduces command graph and source hashes; no generated audio or improved quality is claimed.

### requires an authorized host render
- Separately authorized runs generate a requested sound effect, revoice a real existing clip, and refine its audio while producing a before/after video hash showing the visual stream is byte-for-byte unchanged where the operation promises that invariant.
- Each bundle records model provenance, command, queue attempt, output hashes, ffprobe stream/layout/duration, and relevant transcript/audio gate evidence.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_audio_post.py -q`, real CLI/filesystem/queue only, no mocks.
- Use committed media and real ffprobe/hash inspection; corrupt one hash to prove fail-closed behavior.
- Authorized post bundles must be checked with ffprobe and source/output hashes before any matrix status becomes verified.

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
status: rejected

### evidence
- PM rejection applied via pvg story reject on 2026-09-23.

### proof
- [ ] Story requires another developer delivery before it can be accepted.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence
Summary: Delivered the no-GPU audio-post planning slice only: retained the prior typed model/backend work, added real source/voice hash validation, three deterministic mode plans (sound effect, revoice, refinement), an explicit immutable held-fixed-video contract, seed-bearing command graphs, immutable non-executable durable records, typed exit-2 failures, reconstruction, `wgp sfx`, planned-only docs, and README verb-map/index updates required by the new drift test. No render, host access, SSH, GPU work, model download, generated-audio claim, measured-output claim, or renderer/queue/QC/gate/retry semantic change occurred.
Commands run:
- `uv run --frozen --extra dev pytest tests/test_sfx_capabilities.py -q --junitxml=<tmp>/t.xml` -> exit 0; parsed JUnit tests=29 failures=0 errors=0 skipped=0.
- `uv run --frozen --extra dev pytest tests/test_readme_quickstart.py -q --junitxml=<tmp>/t.xml` -> exit 0; parsed JUnit tests=5 failures=0 errors=0 skipped=0.
- `uv run --frozen --extra dev pytest -q --junitxml=<tmp>/f.xml` -> exit 0; parsed JUnit tests=1848 failures=0 errors=0 skipped=1.
- Real CLI evidence: human plus JSON output for sound effect, revoice, and refinement and all 22 typed failure classes, including `AUDIO_POST_VIDEO_MUTATION_REFUSED`; `/tmp/wd-fasw-cli-evidence.json`, SHA256 `e7255e4176d4272b57fabbd3c8f981389bdf60c72d4fcf8b9080eb9d146d81e1`.
- Queue/reconstruction evidence: update and delete rejected by immutable triggers; planning `next_admissible=null`; genuine render job admitted afterward; all reconstruction hashes match with `hidden_mutation=false`; `/tmp/wd-fasw-cli-evidence.json`.
- `git diff --exit-code -- datasets` and `git diff --exit-code origin/main -- datasets` -> both exit 0; datasets tree SHA256 before/after matched and zero shadowed ssh/curl/wget/nvidia-smi calls.
- Targeted JUnit SHA256 `31407f2d204e4b72f70b969ed0b5cd893462db8e6fc13756671b116e17ed9f8d`; full JUnit SHA256 `c348575c77a6b20b615060d85af15748936d5045ae891f827315ee2bd36ecdda`.
- `uv build --out-dir /tmp/wd-fasw-dist.sMv57o` -> exit 0; one wheel `d3aaa241d14e104ce5461c8692dbc1568ce4fd923cd449e78e058bf11a047273` and one sdist `1206701cf43a7f9b3ce9fd9319edcf27e44bf7fdfc68930ea87fb7e0aaf96d8c`.
- `git fetch origin main && git rebase origin/main` -> incorporated main `a9ed130`; all CLI registrations retained; README verb map/index updated for `sfx`.
- `git push -u origin story/WD-fasw` -> exact head published; `gh pr create` -> https://github.com/jmanhype/wangp-dspy/pull/170.
- `gh api repos/jmanhype/wangp-dspy/commits/dcb5718b61dad30ccabdf75e7d7f830ab833c134/check-runs` -> check `test` completed/success.
SHA: dcb5718b61dad30ccabdf75e7d7f830ab833c134

### CI/Test Results
- Targeted SFX suite: tests=29, passed=29, failures=0, errors=0, skipped=0, command exit=0.
- README drift suite: tests=5, passed=5, failures=0, errors=0, skipped=0, command exit=0.
- Full suite: tests=1848, passed=1847, failures=0, errors=0, skipped=1 (pre-existing), command exit=0.
- Build: command exit=0; exactly one wheel and one sdist with SHA256 values recorded above.
- GitHub check `test` on exact head `dcb5718`: completed/success.

### AC Verification
| AC | Result | Evidence |
|---|---|---|
| Typed SFX, revoice, and refinement requests compile from committed media hashes and declared ffprobe streams | pass | three real CLI mode cases plus ffprobe/hash test; targeted 29/29 |
| Absent/ambiguous streams, mismatched duration, missing voice, invalid layout, and all other incomplete/unsupported classes fail with typed exit 2 and remediation/next command | pass | 22 real subprocess failure cases in `/tmp/wd-fasw-cli-evidence.json` |
| Request that would alter a video declared held-fixed is refused | pass | `AUDIO_POST_VIDEO_MUTATION_REFUSED` case; no crop/scale/retime/reencode plan is emitted |
| Plan marks source video hash immutable and names intended output while queue record preserves invariant | pass | durable record has `video_fixed.immutable=true`, source hash, no transformations, and explicit output path |
| Durable records are immutable, non-executable, and un-drainable by real admission while a genuine render remains admitted | pass | update/delete triggers reject mutation; `next_admissible=null`, then genuine job ID after real `JobQueue.submit` |
| Seed-based dry-run reconstruction reproduces settings/command provenance with hash equality and no hidden mutation | pass | `all_match=true`, `hidden_mutation=false`; recorded/reconstructed settings SHA256 equal |
| `wgp` registration, README verb map, and planned-only docs stay coherent | pass | minimal two-line `sfx` registration; README drift 5/5; docs matrix all planned |
| Committed datasets remain read-only and no hidden host/network/GPU command runs | pass | worktree and origin/main dataset diffs exit 0; shadowed call count 0 |
| Honest no-GPU delivery/build evidence | pass | targeted/full JUnit counters above; one wheel and one sdist; CI success |
| Authorized SFX generation | not verified - requires authorized host run | no model execution or generated audio exists |
| Authorized revoice output | not verified - requires authorized host run | no model execution or generated audio exists |
| Authorized refinement output | not verified - requires authorized host run | no model execution or measured quality improvement exists |
| Authorized before/after proof that output video bytes remain unchanged | not verified - requires authorized host run | no host bundle/output hashes/ffprobe evidence exists |

## nd_contract
status: delivered

### evidence
- Branch `story/WD-fasw`, commit `dcb5718b61dad30ccabdf75e7d7f830ab833c134`, PR #170.
- Targeted suite 29/29 passed; README suite 5/5 passed; full suite 1847 passed plus 1 pre-existing skipped; CI `test` success.
- One wheel and one sdist built with hashes recorded above.

### proof
-[x] NOGPU-1: typed sound-effect, revoice, and refinement planning with committed-media hash/stream validation
-[x] NOGPU-2: immutable held-fixed-video refusal contract and planned output naming
-[x] NOGPU-3: durable immutable non-executable records that real admission cannot drain
-[x] NOGPU-4: typed exit-2 remediation and next command for every implemented incomplete/unsupported class
-[x] NOGPU-5: seed-based reconstruction hash equality without hidden mutation
-[x] NOGPU-6: registered and documented planning-only `wgp sfx` surface including README drift coverage
-[x] NOGPU-7: committed datasets read-only and zero host/GPU/model-download work
-[x] NOGPU-8: targeted, drift, full-test, build, and exact-head CI evidence
-[x] NOGPU-9: no generated-audio, measured-output, quality-improvement, or video-byte-preservation claim

## History
- 2026-09-22T20:24:45Z dep_added: blocked_by WD-6ml6
- 2026-09-22T20:24:45Z dep_added: blocked_by WD-soa4
- 2026-09-22T20:24:45Z dep_added: blocked_by WD-6tox
- 2026-09-22T20:26:48Z dep_added: blocks WD-gc09
- 2026-09-22T22:50:10Z dep_removed: was_blocked_by WD-6tox
- 2026-09-23T01:38:43Z dep_removed: was_blocked_by WD-soa4
- 2026-09-23T06:49:08Z dep_removed: was_blocked_by WD-6ml6
- 2026-09-23T06:51:50Z status: open -> in_progress
- 2026-09-23T06:51:50Z auto-follows: linked to predecessor WD-6tox
- 2026-09-23T06:51:50Z auto-follows: linked to predecessor WD-soa4
- 2026-09-23T06:51:50Z auto-follows: linked to predecessor WD-6ml6
- 2026-09-23T06:51:50Z claimed by dev-WD-fasw
- 2026-09-23T08:09:53Z status: in_progress -> in_progress
- 2026-09-23T08:09:53Z auto-follows: linked to predecessor WD-pcen
- 2026-09-23T08:35:24Z status: in_progress -> open
- 2026-09-23T08:35:24Z released by speed

## Links
- Parent: [[WD-t741]]
- Blocks: [[WD-gc09]]
- Was blocked by: [[WD-6tox]], [[WD-soa4]], [[WD-6ml6]]
- Follows: [[WD-6tox]], [[WD-soa4]], [[WD-6ml6]], [[WD-pcen]]

## Comments

### 2026-09-23T08:35:25Z speed
EXPECTED: typed exit-2 failures must provide a usable next command consistent with the registered wgp CLI. DELIVERED: observed diagnostics return next_command=wgp audio sfx --request <request> --models <models> --json, but exact invocation exits 2: argument verb: invalid choice: 'audio' (choose from video, image, music, first-run, sfx, voice, doctor, content, brief, plan, status, review, recipe, release). GAP: retained typed-model default references the obsolete/nonexistent audio verb and is inconsistent with wangp/sfx_cli.py. FIX: emit mode-specific wgp sfx effect|revoice|refine next commands and lock the exact command validity in tests.
