---
id: WD-eq1i
title: "Director and composition: prompt or audio to governed multi-clip film"
status: open
priority: 2
type: feature
labels: [capability]
parent: WD-t741
created_at: 2026-09-22T20:24:44Z
created_by: speed
updated_at: 2026-09-23T11:29:25Z
content_hash: "sha256:b928233853f21a660c00b0ec100f6f30d3e287f91fa875f6925b6e0c361264cd"
blocks: [WD-gc09]
was_blocked_by: [WD-6tox, WD-soa4, WD-6ml6, WD-tkuz]
follows: [WD-6tox, WD-soa4, WD-6ml6, WD-tkuz, WD-fasw]
---

## Description

## USER INTENT
Observable outcome: one prompt or one audio track can become a governed multi-clip film plan and, only after separate authorization, a finished artifact; screenplay and music-video modes carry continuity, pacing, auto/manual review, and queue enhancement.

## Context (Embedded)
- The governed repository path is plan -> durable queue -> host render -> QC gates -> assembly -> provenance/recipe; `wgp` is the stable CLI and GPU execution is never implied by planning.
- Existing director services, content-brief planning, chain planning, assembler, and QC provide the governed substrate; this story exposes Maestro’s product-level composition modes without weakening review.
- Beat-aware music-video planning consumes measured audio beats rather than fabricated beat claims.
- Auto review is a policy over real gates and reviewer evidence; manual review remains available and must not be bypassed by a planner.

## OUT OF SCOPE
- A free-form prompt that silently calls an external LLM or paid provider; provider selection and authorization are explicit.
- Accepting continuity because the screenplay mentions a character; cross-clip state must be represented and checked.

## DIFF BUDGET
Roughly 11 files, under 900 authored changed LOC, excluding models and generated media.

## Boundary Map
PRODUCES:
- services/director/composition.py -> typed prompt/audio/screenplay/music-video composition requests and outputs
- services/director/continuity.py -> explicit character/appearance/voice/location state across scenes and clips
- services/director/pacing.py -> deterministic pacing and beat-to-clip/window mapping
- services/director/review_policy.py -> auto/manual gate policy and review checkpoints
- wangp/director_cli.py -> `wgp director plan|enhance|queue|review` command implementation and submit boundary
- docs/director-composition.md -> prompt/audio/screenplay/music-video workflows, long-form limits, review modes, and evidence contract
- tests/test_director_composition.py -> real-process composition/queue coverage; no mocks
- datasets/runs/maestro-parity/WD-eq1i/ -> authorized director run bundles

CONSUMES:
- services/director/orchestrator.py -> existing director orchestration seam
  spec: existing director orchestration seam
- services/director/schema.py -> existing director schema
  spec: existing director schema
- services/director/run_records.py -> existing run-record semantics
  spec: existing run-record semantics
- services/chain/plan.py -> multi-shot planning seam
  spec: multi-shot planning seam
- services/chain/keyframes.py -> keyframe/continuity seam
  spec: keyframe/continuity seam
- predict/video_capabilities.py -> accepted video request contract
  spec: accepted video request contract
- predict/music_capabilities.py -> accepted music request contract
  spec: accepted music request contract
- predict/character_packages.py -> portable character continuity binding
  spec: portable character continuity binding
- predict/voice_registry.py -> portable saved voice binding
  spec: portable saved voice binding
- services/jobs/queue.py -> durable queue record and attempt transitions
  spec: durable queue record and attempt transitions
- services/jobs/preflight.py -> typed composition/continuity failures
  spec: typed composition/continuity failures
- predict/assembler.py -> governed assembly path
  spec: governed assembly path
- wangp/cli.py -> stable verb registration and exit-code contract
  spec: stable verb registration and exit-code contract


## Required Outcomes
### no-GPU verifiable now
- Real CLI tests turn a fixed prompt, a committed audio track, and a fixed screenplay into deterministic multi-clip plans with explicit continuity state and per-clip prompts/overlaps.
- Beat-aware music-video planning reads real audio/beat evidence and maps every clip window; absent/corrupt beat evidence is a typed failure.
- Pacing and exact-timecode/window-count controls preserve total target duration up to the programme’s 60-minute contract, and auto/manual review checkpoints are explicit in JSON.
- Queue enhancement rewrites only intended fields with provenance and leaves the original request hash recoverable; a real temporary queue can reconstruct the full composition without generation.

### requires an authorized host render
- Separately authorized runs execute at least one prompt-to-film, one audio/music-video, and one screenplay path through video/music/speech as needed, including assembly and all mandatory QC gates.
- The run bundle records the composition source, review decisions, per-clip queue attempts, model provenance, output hashes, final duration, and recipe/reconstruction evidence.

## Testing Requirements
- `uv run --frozen --extra dev pytest tests/test_director_composition.py -q`, real CLI/files/audio/queue processes, no mocks.
- Use real committed audio and screenplay fixtures; assert one missing/corrupt continuity or beat input produces a typed preflight failure.
- Authorized director bundles must be reviewed with queue, QC, ffprobe, hash, and recipe evidence before capability rows become verified.

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
Summary: Delivered the no-GPU director planning slice for prompt, audio, beat-aware music video, screenplay continuity, pacing, auto/manual review, immutable non-executable records, prompt-only enhancement, reconstruction, CLI registration, README integration, and capability documentation. No GPU, host, SSH, download, renderer, queue execution, or generated-media claim is made.

Commands run:
- `git log --oneline -2`; `git status --porcelain`
- `uv run --frozen --extra dev pytest tests/test_director_capabilities.py -q --junitxml=/tmp/wd-eq1i-director.xml`
- `uv run --frozen --extra dev pytest tests/test_readme_quickstart.py::test_readme_capability_status_and_documentation_index tests/test_readme_quickstart.py::test_readme_verb_map_matches_cli -q --junitxml=/tmp/wd-eq1i-readme.xml`
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-eq1i-full.xml`
- `pvg verify services/director/composition.py services/director/continuity.py services/director/pacing.py services/director/review_policy.py services/director/plan_compiler.py wangp/director_cli.py wangp/cli.py README.md docs/director-capabilities.md --include-tests tests/test_director_capabilities.py --format=text`
- `uv build --out-dir /tmp/wd-eq1i-build.pfDjn0`
- `gh pr create --base main --head story/WD-eq1i` -> https://github.com/jmanhype/wangp-dspy/pull/173
- Exact-head check-run poll for `2ed37d968f0c66f0f9346e87bc58868727df8fe7`: `test` completed `success`.

SHA: 2ed37d968f0c66f0f9346e87bc58868727df8fe7

### CI/Test Results
- Director targeted JUnit: `tests=33 errors=0 failures=0 skipped=0`, exit 0.
- README contract JUnit: `tests=2 errors=0 failures=0 skipped=0`, exit 0.
- Full suite JUnit: `tests=1914 errors=0 failures=0 skipped=1`, exit 0. The sole skip is pre-existing optional `tests/test_jobs_integration_3090.py::test_live_preflight_against_3090`, gated by `WANGP_3090=1`; it was not run because this story forbids host/GPU work.
- `pvg verify`: `VERIFY: PASSED (8 files scanned, 0 issues)`.
- Build produced exactly one wheel and one sdist: `wangp_dspy-0.1.0-py3-none-any.whl` SHA-256 `c6b8fc2a4d325cfaa707cd9d6ece87ff8eb4fde2c04b28008c9f2714e0e15766`; `wangp_dspy-0.1.0.tar.gz` SHA-256 `e74c2ab174baeda360d2858e034cf6ec24cba0877bd41e6cfeff54b85171eb17`. Both contain `wangp/director_cli.py` and `services/director/plan_compiler.py`.
- PR #173 exact-head check run: `test completed success`.
- Human and JSON outputs were captured under `/tmp/wd-eq1i-evidence/` for all four success modes and all 26 runtime typed failure classes. Every runtime and static emitted `next_command` resolved against live CLI help.
- Queue proof: SQLite update/delete triggers reject mutation; real `JobQueue.next_admissible()` selects no director record; a genuine render job in a separate database remains admissible; original director database bytes remain unchanged.
- Reconstruction: original and prompt-enhanced records independently recompile with equal request and clip hashes, `all_match=true`, `hidden_mutation=false`.
- Read-only proof: committed datasets digest `c367434034e024f038f3da5a24ac0828a012eb6f950ffa5dd8fd49c62906bc6b`; audio digest `f3d66cac4458d0d33870ff6dc97df75eff95d57b154180dd303be4f955c91857`; all shadowed `ssh`/`curl`/`wget`/`nvidia-smi` logs empty.
- Deviation: branch adds 2,267 lines, above the story's rough 900-line budget, because the existing checkpoint was preserved and exhaustive failure/process coverage was required. No forbidden finishing-lane file was touched; `wangp/cli.py` changes are exactly one import plus one registration call.

### AC Verification
| AC | Result | Evidence |
| --- | --- | --- |
| Prompt/audio/music-video/screenplay deterministic ordered multi-clip planning | PASS | `tests/test_director_capabilities.py` real-process mode matrix; targeted JUnit 33/33. |
| Beat-aware planning uses declared measured beats and rejects absent/unproven evidence | PASS | Music-video mode test plus `DIRECTOR_AUDIO_BEATS_MISSING` and `DIRECTOR_AUDIO_BEATS_INVALID` failure tests. |
| Explicit screenplay continuity states and changes across clips | PASS | Screenplay test asserts Rho's explicit state transition and Tess carried forward. |
| Exact/window pacing preserves complete target duration within 60-minute contract | PASS | Exact and window-count tests assert count, ordered starts, and total duration. |
| Auto/manual review checkpoints are explicit and gates are not bypassed | PASS | Mode tests and `DIRECTOR_REVIEW_MODE_CONFLICT`; policy reports `bypasses_gate=false`. |
| Prompt-only queue enhancement preserves original hash/provenance and source DB | PASS | Enhancement test compares original/enhanced hashes, changed fields, source bytes, and reconstruction. |
| Durable immutable non-executable records cannot drain real admission | PASS | Trigger, real-selector, genuine-job, and byte-identity tests all pass. |
| Seed reconstruction hash equality | PASS | Original and enhanced `review` tests report `all_match=true`, `hidden_mutation=false`. |
| Typed exit-2 failures, remediation, and resolving next commands | PASS | 26 runtime failure classes tested in human and JSON modes; live CLI resolution guard passes. |
| CLI/README/docs integration | PASS | README contract JUnit 2/2; `wgp --help` includes `director`; `docs/director-capabilities.md` rows remain planned. |
| Packaging and CI | PASS | One wheel and one sdist; PR #173 exact-head `test` check completed success. |
| Host render / generated media / final duration / creative quality | not verified - requires authorized host run | No host, GPU, renderer, model download, or generated artifact was contacted or produced. |

## nd_contract
status: delivered

### evidence
- Branch: `story/WD-eq1i`
- SHA: `2ed37d968f0c66f0f9346e87bc58868727df8fe7`
- PR: https://github.com/jmanhype/wangp-dspy/pull/173
- CI: exact-head `test completed success`.
- Local parsed JUnit and build hashes are recorded above.

### proof
- [x] Fixed prompt, committed audio metadata, measured music-video beats, and fixed screenplay produce deterministic ordered no-GPU plans.
- [x] Explicit continuity, pacing, overlaps, auto/manual review checkpoints, and planning-surface references are emitted.
- [x] Immutable non-executable records reject mutation and cannot drain the real admission path while a genuine job remains admissible.
- [x] Queue enhancement changes only authorized prompt fields with provenance and preserves the original request hash.
- [x] Seed reconstruction independently reproduces request and clip hashes.
- [x] Every tested incomplete/unsupported input exits 2 with remediation and a next command resolving against the live CLI.
- [x] README verb map, capability table, documentation index, and planned-only capability matrix are integrated.
- [x] Real-process tests, README drift tests, full suite, pvg verify, and one-wheel/one-sdist build pass as recorded.
- [x] Read-only no-host proof is recorded; generated media remains unclaimed.

## History
- 2026-09-22T20:24:46Z dep_added: blocked_by WD-6tox
- 2026-09-22T20:24:46Z dep_added: blocked_by WD-soa4
- 2026-09-22T20:24:47Z dep_added: blocked_by WD-6ml6
- 2026-09-22T20:24:47Z dep_added: blocked_by WD-tkuz
- 2026-09-22T20:24:47Z dep_added: blocks WD-gc09
- 2026-09-22T22:50:10Z dep_removed: was_blocked_by WD-6tox
- 2026-09-23T01:38:43Z dep_removed: was_blocked_by WD-soa4
- 2026-09-23T06:49:08Z dep_removed: was_blocked_by WD-6ml6
- 2026-09-23T09:16:29Z dep_removed: was_blocked_by WD-tkuz
- 2026-09-23T09:36:23Z status: open -> in_progress
- 2026-09-23T09:36:23Z auto-follows: linked to predecessor WD-6tox
- 2026-09-23T09:36:23Z auto-follows: linked to predecessor WD-soa4
- 2026-09-23T09:36:23Z auto-follows: linked to predecessor WD-6ml6
- 2026-09-23T09:36:23Z auto-follows: linked to predecessor WD-tkuz
- 2026-09-23T09:36:23Z claimed by dev-WD-eq1i
- 2026-09-23T11:06:51Z status: in_progress -> in_progress
- 2026-09-23T11:06:51Z auto-follows: linked to predecessor WD-fasw
- 2026-09-23T11:29:25Z status: in_progress -> open
- 2026-09-23T11:29:25Z released by speed

## Links
- Parent: [[WD-t741]]
- Blocks: [[WD-gc09]]
- Was blocked by: [[WD-6tox]], [[WD-soa4]], [[WD-6ml6]], [[WD-tkuz]]
- Follows: [[WD-6tox]], [[WD-soa4]], [[WD-6ml6]], [[WD-tkuz]], [[WD-fasw]]

## Comments
