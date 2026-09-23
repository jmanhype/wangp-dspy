---
id: WD-soa4
title: "Music generation, ABC planning, style adaptation, and a second independent model"
status: closed
priority: 2
type: feature
labels: [capability, accepted]
parent: WD-t741
created_at: 2026-09-22T20:24:44Z
created_by: speed
updated_at: 2026-09-23T01:38:44Z
content_hash: "sha256:4637501c66908d551c11ab75b1f9ae28bd7bed7e0112e303801dd07723d78284"
assignee: dev-WD-soa4
follows: [WD-6tox]
closed_at: 2026-09-23T01:38:43Z
close_reason: "Accepted: exact-head probes, immutable non-executable records, real selector admission, typed failures, reconstruction, read-only proof, scoped/full tests, CI, and honest planned-only matrix all passed."
led_to: [WD-pcen]
---

## Description

## USER INTENT
Observable outcome: one governed request can plan and generate a song with melody/chord structure and ABC score, produce 48 kHz stereo output, choose an instrumental preset, adapt/train style, compare before/after audibly, and select a second independent music model.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- Current audio code is primarily speech/AV QC and pipeline preparation; it is not a first-class Maestro song-generation surface.
- ABC melody/chord planning can be checked deterministically without inference, but audio generation and style adaptation are host/model claims.
- Style adaptation must preserve clear provenance for training/reference inputs and must not relicense or hide upstream material.

## OUT OF SCOPE
- Redistributing source songs, stems, model weights, or generated audio without recorded upstream rights.
- Claiming 48 kHz stereo from filename or request metadata rather than measured ffprobe output.

## DIFF BUDGET
Roughly 10 files, under 800 authored changed LOC, excluding model assets and audio.

## Boundary Map
PRODUCES:
- predict/music_capabilities.py -> typed song request with lyrics/style, melody/chord plan, ABC score, instrumental preset, sample rate/channel target, model choice, and style-adaptation inputs
- services/music/song_compiler.py -> deterministic score/job records and segment/arrangement plans
- host/music_backends.py -> two independent model adapters with fail-closed manifest/provenance checks
- wangp/music_cli.py -> `wgp music plan|compile|style|compare` command implementation and submit boundary
- docs/music-capabilities.md -> score schema, models, 48 kHz stereo acceptance, adaptation policy, and comparison contract
- tests/test_music_capabilities.py -> real-process score/queue/reconstruction coverage; no mocks
- datasets/runs/maestro-parity/WD-soa4/ -> authorized audio bundles including before/after style adaptation

CONSUMES:
- predict/audio_manifest.py -> typed audio metadata contract
  spec: typed audio metadata contract
- predict/audio_prep.py -> existing audio preparation behavior
  spec: existing audio preparation behavior
- services/jobs/queue.py -> durable queue record and attempt transitions
  spec: durable queue record and attempt transitions
- services/jobs/preflight.py -> typed missing model/reference failures
  spec: typed missing model/reference failures
- host/render_host.py -> authorized host execution and artifact retrieval
  spec: authorized host execution and artifact retrieval
- qc/audio_critic/profiles.py -> existing music profile provenance
  spec: existing music profile provenance
- wangp/cli.py -> stable verb registration and exit-code contract
  spec: stable verb registration and exit-code contract


## Required Outcomes
### no-GPU verifiable now
- Real tests build representative ABC melody/chord plans, validate syntax and structural invariants, normalize instrumental and model selection, and emit deterministic JSON and score artifacts without inference.
- A real queue record includes score hash, arrangement, model, target `48000 Hz / 2 channels`, reference hashes, and style-adaptation mode; missing or malformed inputs fail typed.
- Dry-run reconstruction exactly reproduces score and model settings; the test explicitly asserts no audio file is created and no quality is claimed.
- Docs mark generation, second-model output, and style adaptation as planned until recorded runs exist.

### requires an authorized host render
- Separately authorized host runs generate instrumental and non-instrumental songs on each independent model, measure 48 kHz stereo with ffprobe, and retain source score/hash provenance.
- An authorized style-adaptation run records before and after audio, training/reference provenance, command/settings, and an audible A/B comparison artifact; no automatic aesthetic claim is made.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_music_capabilities.py -q`, real process only, no mocked ABC parser, queue, subprocess, or filesystem.
- Authorized bundles are checked with ffprobe, hashes, and real playback-candidate metadata; tests must not fabricate audio.

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
- PM closeout applied via pvg story accept on 2026-09-22.

### proof
- [x] Story closed after accepted label was applied.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-22.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence
Summary: Delivered the no-GPU music planning slice only: typed melody/chord/ABC requests, two independent planned model slots, instrumental/song normalization, 48 kHz stereo declarations, structural style-adaptation provenance and audible-A/B contract, deterministic score artifacts, immutable non-executable plan records, typed failures, and reconstruction. No render, host access, GPU work, model download, training, generated-audio claim, or gate semantic change occurred.

Commands run:
- `git log --oneline -3`; `git status --short --branch`; `pvg nd show WD-soa4`
- `uv run --frozen --extra dev pytest tests/test_music_capabilities.py -q` -> exit 0, 28/28 passed, 0 failed
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-soa4-full-final-junit.xml` -> exit 0; JUnit: tests=1743, errors=0, failures=0, skipped=1, time=375.461s
- `uv run --frozen --extra dev pytest tests/test_music_capabilities.py -q --junitxml=/tmp/wd-soa4-scoped-final-junit.xml` -> exit 0; JUnit: tests=28, errors=0, failures=0, skipped=0, time=30.779s
- Real CLI captures under `/tmp/wd-soa4-cli-evidence`: human+JSON for plan/compile/style/compare; compare=`records=1 all_match=true hidden_mutation=false`; style=`training_executed=false audio_created=false ... after_status=planned aesthetic_verdict=none`
- Durable queue evidence: `music_plan_records` had one immutable record per requested section/track with backend, full score/hash, arrangement, section, and 48000 Hz/2-channel format; `JobQueue.list_state('pending')==[]` and `next_admissible()==None`; after inserting a genuine render job, `next_admissible()` selected only that job
- Typed failure evidence: real subprocess tests cover all 23 emitted failure classes with exit 2 and machine-readable diagnostics; scoped JUnit is 28/28 passed
- Read-only proof: shadowed ssh/nvidia-smi/call log bytes=0, ssh calls=0, nvidia-smi calls=0; `git diff --exit-code -- datasets` and `git diff --exit-code origin/main -- datasets` -> exit 0; worktree clean
- `uv build --out-dir /tmp/wd-soa4-dist-5089849` -> exit 0; clean artifact set: one wheel and one sdist
- `git fetch origin main`; `git rebase origin/main` -> no-op/up to date; no `wangp/cli.py` conflict arose
- `git push -u origin story/WD-soa4`; `gh pr create ...` -> https://github.com/jmanhype/wangp-dspy/pull/166
- `gh api repos/jmanhype/wangp-dspy/commits/508984904459f806e679dd8b1dbf9197677c7ce8/check-runs` -> `test completed success`

SHA: 508984904459f806e679dd8b1dbf9197677c7ce8

### CI/Test Results
- Scoped music suite: 28 passed, 0 failed, 0 errors, 0 skipped.
- Full repository suite: 1743 tests total; 1742 passed, 1 pre-existing skipped, 0 failed, 0 errors.
- GitHub check `test` for commit `5089849`: completed/success.
- Build: `wangp_dspy-0.1.0-py3-none-any.whl` sha256 `1caed19b235c255aa7931e5c2598a581ef27a329d9e2bdfaf18403f0a34a5937`; `wangp_dspy-0.1.0.tar.gz` sha256 `26791f0c47ca4f1d572313619b82ac297c7c1a6554f09d1711747e816cc67a23`.

### AC Verification
| AC | Result | Evidence |
|---|---|---|
| Representative ABC melody/chord plans validate syntax and structural invariants and emit deterministic JSON/score artifacts without inference | pass | `tests/test_music_capabilities.py`; scoped 28/28; deterministic repeated CLI JSON and `/tmp/wd-soa4-cli-evidence/*.abc` |
| Queue records include score hash, arrangement, model, 48000 Hz/2-channel target, reference hashes, and style-adaptation mode | pass | durable queue test asserts every immutable per-track field; typed failure tests reject malformed inputs |
| Plan records are immutable and cannot be drained as executable work | pass | SQLite update trigger test plus real `JobQueue.list_state`/`next_admissible`; genuine-job admission remains selected |
| Dry-run reconstruction reproduces score and model settings without hidden mutation or audio creation | pass | `wgp music compare` reconstruction: all_match=true, hidden_mutation=false; tests assert no `.wav` is created |
| Two independent named model slots and instrumental/song settings normalize fail-closed | pass | `ace_step` and `stable_audio` adapters/manifest provenance tests; both slots remain planned |
| Style adaptation is structurally validated with reference rights/hashes and audible before/after declaration | pass | style CLI/test records before hash, planned after path, reference source/rights/hash; training=false, audio_claimed=false |
| Every implemented incomplete/unsupported class exits typed | pass | all 23 diagnostic classes are exercised through real subprocesses with exit 2 |
| No host/GPU/model-download/dataset mutation | pass | shadow PATH log empty; datasets diffs exit 0; docs/tests contain no render invocation |
| Documentation keeps capability rows planned and requires ffprobe-measured host evidence | pass | `docs/music-capabilities.md` matrix remains planned and says generated audio/style A/B are unclaimed |
| Instrumental and non-instrumental songs on each independent model | not verified - requires authorized host run | no authorized render bundle or measured ffprobe evidence exists |
| Second independent model output | not verified - requires authorized host run | `stable_audio` generation is planned only |
| Authorized style training/adaptation and audible A/B output | not verified - requires authorized host run | structural plan only; no training, inference, after-audio, playback, or aesthetic verdict claimed |

## nd_contract
status: delivered

### evidence
- Branch `story/WD-soa4`, commit `508984904459f806e679dd8b1dbf9197677c7ce8`, PR #166.
- Scoped suite 28/28 passed; full suite 1742 passed plus 1 skipped, 0 failures/errors; CI `test` success.
- One wheel and one sdist built with hashes recorded above.

### proof
- [x] AC #1: typed requests, ABC structural validation, deterministic normalization and artifacts
- [x] AC #2: complete immutable per-track plan records
- [x] AC #3: real admission path cannot drain planning-only records
- [x] AC #4: reconstruction hash match with no hidden mutation or audio
- [x] AC #5: two independent model slots normalize fail-closed
- [x] AC #6: style adaptation validated structurally with provenance and audible-A/B declaration
- [x] AC #7: every implemented typed failure class is machine-readable and exits 2
- [x] AC #8: no GPU/host/model-download/dataset mutation
- [x] AC #9: docs and matrix remain honest and planned

## History
- 2026-09-22T20:24:45Z dep_added: blocks WD-fasw
- 2026-09-22T20:24:47Z dep_added: blocks WD-eq1i
- 2026-09-22T20:27:37Z dep_added: blocks WD-gc09
- 2026-09-23T00:09:23Z status: open -> in_progress
- 2026-09-23T00:09:23Z auto-follows: linked to predecessor WD-6tox
- 2026-09-23T00:09:23Z claimed by dev-WD-soa4
- 2026-09-23T01:18:56Z status: in_progress -> in_progress
- 2026-09-23T01:38:43Z status: in_progress -> closed
- 2026-09-23T01:38:43Z dep_removed: no_longer_blocks WD-fasw
- 2026-09-23T01:38:43Z dep_removed: no_longer_blocks WD-eq1i
- 2026-09-23T01:38:43Z dep_removed: no_longer_blocks WD-gc09

## Links
- Parent: [[WD-t741]]
- Follows: [[WD-6tox]]
- Led to: [[WD-pcen]]

## Comments
