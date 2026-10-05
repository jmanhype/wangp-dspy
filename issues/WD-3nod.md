---
id: WD-3nod
title: "Maestro parity: generation evidence"
status: open
priority: 1
type: epic
labels: [capability, evidence]
created_at: 2026-09-24T14:14:05Z
created_by: speed
updated_at: 2026-10-05T23:32:56Z
content_hash: "sha256:e0ca44112842008b73b6f2c80d9f3df6b1e6256a0c99544fdc314aa8a1cbf5aa"
---

## Description
Temporary creation body; authoritative body is installed immediately after ID assignment.

## Acceptance Criteria


## Design


## Notes
### Programme completion audit at b5b7e35b (orchestrator, 2026-10-05)

Machine-verified census at merged main b5b7e35b. Evidence is test-backed, not prose.

- Item (a), zero `planned` rows: PROVEN. `tests/test_current_parity_index.py` parses every capability
  document under `docs/` and asserts the parsed 208-row census equals
  `datasets/runs/maestro-parity/WD-fay0/evidence-index.json` (89 host_run_verified, 110
  terminal_unsupported_or_fail_closed, 7 dependency_blocked, 2 not_applicable), and asserts there is no
  row whose canonical state is `planned`. The same file pins the seven `dependency_blocked` LTX cells to
  recorded boundary evidence with zero model download bytes and an explicit not-a-hardware-verdict flag.
- Item (b), provenance/gate checker half: SATISFIED. `scripts/verify_maestro_parity.py` is on main; the
  per-lane receipt `datasets/runs/maestro-parity/checker-lane-receipts/evidence.json` records eight lanes,
  seven `pass` and one fail-closed `fail` (exit 1), so it rejects as well as accepts.
- Item (b), clean-machine generated artifact: NOT satisfied; recorded as an explicit incomplete storage
  boundary with `generated_artifact=false`, blocked on the deferred WD-bw0h storage story.
- Item (c): all four standing gates green; `pvg lint --backlog` 0 errors, full suite exit 0 with JUnit
  tests=2175 failures=0 errors=0 skipped=1, release ready with no tag, protected engine files unchanged.

Residual non-terminal cells are exactly seven, all `dependency_blocked` LTX: ltx/2.5 outpaint, repaint,
recast, upscale; ltx/2.3 outpaint, recast, upscale. Each needs a model-download authorization or an
operator disposition.

Documentation nit, prose only and not machine-asserted: `docs/video-capabilities.md` still opens its
capability matrix with a sentence claiming every family/operation row is `planned`, which contradicts the
table beneath it and the index. No test asserts that sentence; it is proposed as a one-PR doc fix.
### Identified remaining work: checker lane coverage omits the editor lane (orchestrator, 2026-10-05)

Objective item (b) asks for the fail-closed provenance checker to be demonstrated on at least one bundle
per lane. The recorded receipt currently covers eight bundle lanes: WD-2gyw, WD-bxhc, WD-cpow, WD-m0r5,
WD-r81u, WD-rous, consent-closeout and WD-dmf2, which map to video, character, sfx, image, finishing,
music, voice and director respectively.

Verified this session: the checker itself PASSes on the editor lane bundle, which exists on disk at
`datasets/runs/maestro-parity/editor-host-export/host-run` (exit 0, PASS, owned_warnings 0). The editor
lane is nonetheless absent from the receipt, and first-run is absent by design because it has no
generated artifact.

The blocker for closing that gap is not the checker run but the receipt's shape. `scripts/verify_maestro_parity.py`
hard-codes the expected lane tuple of exactly those eight ids, so extending coverage requires changing the
fail-closed verifier itself and cascading the change through the receipt, the index lane bundles
(`lane_exit_codes`, `receipt_sha256`, `checker_sha256`), the index validator expectations, the rendered
index markdown and the parity tests.

The identity derivation is now known, so the work is bounded: `_bundle_identity_sha256` hashes, over every
regular file in sorted order, the UTF-8 relative path, a NUL, the lowercase hex SHA-256 of the file bytes,
and a NUL. That reproduces the existing lane identities and would let an added lane carry a truthful
identity rather than a fabricated one.

Because this edits the QC gate's own implementation, it is recorded here as the next scoped work item
rather than performed unilaterally. No verifier, receipt, index or test byte was changed here.
### Loop integrity: knowledge-vault configuration is stale, and a credentials file sits in a vault (orchestrator, 2026-10-05)

Two findings from an operator-delegated decision pass, recorded here because the configured knowledge vault
cannot currently accept notes.

1. The notes adapter is broken. `.paivot/config.yaml` declares the notes vault as "Claude". The directory of
   that name exists but is EMPTY, and the vault tool no longer resolves that name at all, so `pvg notes`
   fails outright rather than silently dropping writes. Checked every registered candidate against the
   folder structure the protocol expects (`_inbox/`, `projects/`): none of them has it. The large Documents
   vault holds 1093 notes but is a general knowledge base with different folders; `vault` holds 32 entries;
   the video-factory vault holds 41; `nd-vault` holds 173 and is the backlog. Because no candidate matches
   the protocol shape, repointing the config would risk scattering notes into the wrong vault, so no config
   was changed. This is an operator call: either restore/register the intended vault, or repoint to a chosen
   one.

2. FLAGGED, not read: the vault named `vault` contains a file named `credentials-master.txt` at its root.
   A credentials-shaped file inside a vault is an exposure risk if that vault syncs to any service or
   repository. Nothing was opened or copied. Recommend confirming whether it is intentional, whether it is
   git-ignored, and whether that vault is synced anywhere.

Also recorded as a delegated disposition: the `ltx/2.3` upscale cell stays a documented `dependency_blocked`
boundary and will not be re-rolled. Its authorization is one-shot (`retry` is `never`) and the governed
runner requires exactly seven operations per plan, so closing that cell would mean manufacturing a
`host_run_verified` the governance deliberately withheld. The asset is present; the gate is not the asset.

## History
- 2026-09-26T04:06:49Z status: open -> closed
- 2026-09-26T04:07:53Z status: closed -> open (reopened)
- 2026-09-26T05:37:11Z status: open -> closed
- 2026-09-26T05:37:53Z status: closed -> open (reopened)

## Links


## Comments

### 2026-09-24T16:33:45Z speed
Programme status at 8f0b225: WD-651z (fail-closed parity evidence checker + canonical bundle contract) delivered, independently accepted, and merged. All 10 child stories now have authoritative bodies. Remaining scope is entirely host-gated: 45 capability rows still read 'planned' and no bundle exists under datasets/runs/maestro-parity/ because the operator's per-batch GPU-host authorization and model-download approval have not been given. The no-GPU install half of the 'better than Maestro' proof already exists and is tested in a clean worktree (tests/test_readme_quickstart.py).

### 2026-09-25T03:15:53Z speed
PROGRAMME MILESTONE at merged main d8671f3: image lane (WD-m0r5) is COMPLETE and on main - 16 image cells host_run_verified from a real authorized host bundle, 4 Flux upscale/outpaint cells unsupported with reasons; docs/image-capabilities.md reflects it. Independent review recomputed 16/16 artifact hashes, reproduced every objective gate and the identity cosines, and visually confirmed real distinct non-blank images per row. WD-e4r7 (fail-closed GPU preflight) also merged. Remaining lanes still need host authorization per batch, and the render host is at 13G free (below the 50G preflight floor), which must be resolved before the next download.

### 2026-09-25T03:34:28Z speed
HOST REPAIR (dispatcher): the uv-managed CPython 3.11.14 interpreter previously removed by the quarantine deletion was restored with 'uv python install 3.11.14' (~100 MB). This recovered TWO environments that had been left with no working interpreter rather than deleting them: /mnt/bulk/straughter/ACE-Step-1.5/.venv (the MUSIC lane's environment) and /home/straughter/qwen-voicedesign-trial/venv — about 16.3 GB of installed packages that would otherwise have needed re-downloading. Verified: all three venvs (ACE-Step, qwen-voicedesign, Wan2GP) now report a working Python (3.11.14, 3.11.14, 3.11.15). Prior collateral damage is now fully repaired.

### 2026-09-25T03:35:50Z speed
DISPATCH PROCESS GAP (dispatcher, corrected): the music lane (WD-rous) was first dispatched to a worktree that had never been created — the branch, worktree and claim were skipped. The agent ran for a while producing nothing and was interrupted; the main checkout remained CLEAN and untouched (verified: no stray files, main still at d8671f3, only WD-m0r5 under datasets/runs/maestro-parity/), so there was no collateral damage. Corrected by creating story/WD-rous from main, adding .claude/worktrees/dev-WD-rous, claiming the story, and re-dispatching. RULE for every lane dispatch: create the branch, add the worktree, and atomically claim the story BEFORE spawning the developer; then verify the worktree exists and is clean. Combined with the earlier push rule (verify the branch is PUSHED, not merely committed), these are the two integration steps the dispatcher must perform rather than assume.

### 2026-09-25T07:07:14Z speed
PROGRAMME MILESTONE at merged main c91a6d8 — every lane NOT gated by video is complete and independently accepted. Rows dispositioned on main: image 4 (16 cells host_run_verified + 4 unsupported), music 2 (ace_step generate+style verified; stable_audio unsupported at measured 44.1 kHz), sfx 3 (vibevoice revoice + deepfilternet refinement verified with ffmpeg-confirmed identical video packet hashes 5f820953...; stable_audio sound_effect unsupported). That is 9 of 45 rows with terminal evidence dispositions. Also landed: WD-651z fail-closed parity evidence checker, WD-e4r7 GPU preflight fail-closed (authorized protected-file change, independently accepted), WD-0zj8 clean-machine install no-GPU half (generated-artifact half explicitly blocked). Efficiency: the sfx lane reused the music lane's Stable Audio assets, so its incremental download was 8,677,764 B. REMAINING 36 ROWS (video 11 + finishing 5 + voice 2 + character 9 + director 9) are all behind the video lane, which is blocked on two operator decisions: (1) VRAM contention - the operator's llama-server endpoint holds 7.75 GB on the 3090 and auto-recovers after being killed, while H3 renders need ~20+ GB, so video rendering and that service cannot coexist; (2) the non-H3 families (LTX-2.3/2.5, SCAIL-2, Hunyuan int8) are not installed and need 119 GB on a host with ~10 GB free, which would require authorizing the 78 GB prune of superseded H3 weights. The H3 rank8 FL/Ref weights ARE present, so H3-based video rows need zero download and are blocked only by the VRAM contention.

### 2026-09-26T04:07:53Z speed
REOPENED BY DISPATCHER — the earlier closure was structural, not substantive.

`WD-i7qs` acceptance auto-closed this epic because all 13 children are closed. The
recorded close reason is literally "All 13 child stories are closed." That says
nothing about programme completion, and it must not be read as one.

Substantive state at merged `main` (post #194): the consolidated disposition index
records 208 matrix cells as 46 verified, 34 unsupported, 120 planned, 6 pending
consent, 2 not applicable. **120 cells are still `planned`.** Per the programme
objective, zero rows may remain `planned` without an operator-approved disposition,
so the parity programme is NOT complete and this epic is not complete.

The 13 closed children delivered: the eight capability surfaces, the fail-closed
parity evidence checker, six lane evidence bundles, the consolidated capstone index,
and two real defect fixes found by the dispatcher (`WD-r4n8` film-grain controls;
`WD-i7qs` LTX gemma tokenizer decoupling).

What still blocks the remaining 120 cells, by lane:
- video, 90 cells — every cell carries the same recorded blocker verbatim: the
  representative operation was verified but the remaining operations "need a new
  operator-approved per-family/per-operation batch". Requires per-batch GPU-host
  authorization.
- director, 25 cells — all blocked by `WD-dmf2`'s three structural gate failures
  (Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet
  screenplay clip 1 0.468897<1.0). Requires a rework-versus-structural-disposition
  decision.
- finishing — `ffmpeg` grain is honestly `planned` because the newly corrected
  size/persistence graph is unmeasured (needs a host run); `neural_frame_gen` has no
  named host implementation; the face cells need a source face plus track
  identity/bounds/rights/consent.
- video `ltx/2.3` — a 29.5 GB generic FP8 checkpoint that mismatches the WanGP
  manifest. Requires download approval.
- voice/character — cloning-reuse consent for the reference rows.

Host prerequisites are cleared and tool-verified (preflight `disk_headroom` PASS at
60G vs the 50G floor; `gpu_state` idle with 24 GB free; ssh and model-hash checks
PASS). The binding constraint is operator authorization, not the machine.

### 2026-09-27T04:13:20Z speed
PROGRAM UPDATE at merged main 079651d9: WD-m25k and WD-8h6p are accepted and merged. Video matrix now has 27 host_run_verified, 43 unsupported, 4 dependency_blocked, and 25 planned cells. All remaining planned cells are LTX-2.3 (9), SCAIL-2 (7), and Wan/2GP (9); they require new model/download authorization because the current instruction authorized no-download work only. Host has about 61 GB free and GPU is idle. Upstream pvg PR 13 remains open/blocked with viewer READ permission and no checks, so it is being waited on rather than force-merged.
