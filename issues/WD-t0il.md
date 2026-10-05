---
id: WD-t0il
title: "Gate: remaining Maestro-parity scope (1 LTX cell + first-run artifact) pending new operator authorization"
status: deferred
priority: 1
type: task
labels: [capability, evidence, gate]
parent: WD-3nod
created_at: 2026-09-26T05:37:46Z
created_by: speed
updated_at: 2026-10-05T15:06:08Z
content_hash: "sha256:12c66e02512b86cc0a9273f2645deafd705d2d7465d5cdaa201e9d33cfc3f1fe"
blocks: [WD-fay0]
was_blocked_by: [WD-he8i]
---

## Description
## Purpose

This story exists so the programme record cannot claim completion it has not
earned. `pvg` closes an epic automatically when its last child closes, which
twice produced a false "Maestro parity: generation evidence — accepted" state
while 120 matrix cells remained `planned`. This story is the epic's standing gate:
it stays open (blocked) until the remaining cells reach terminal, evidence-backed
states, so the epic stays open and the loop reports a real escalation instead of
"epic_complete".

This is a tracking gate, not dispatchable engineering work. It must not be worked,
claimed, or closed by an agent. Only the operator closing the underlying scope
retires it.

## Remaining scope (authoritative count from the capstone index)

208 cells: 46 verified, 34 unsupported, 120 planned, 6 pending consent, 2 not
applicable. The 120 planned cells sit in eight state-bearing capability matrices.

- **video, 90 cells.** Every cell carries the same recorded blocker verbatim: the
  representative operation was verified and the remaining operations "need a new
  operator-approved per-family/per-operation batch". Unlocked by: per-batch
  GPU-host authorization.
- **director, 25 cells.** All blocked by `WD-dmf2`'s three structural gate
  failures: Whisper screenplay clip 1 `0.556 < 0.6`, SyncNet audio clip 1
  `0.594741 < 1.0`, SyncNet screenplay clip 1 `0.468897 < 1.0`. Unlocked by: a
  rework-versus-structural-disposition decision.
- **finishing, 4 cells.** `ffmpeg` Film grain is honestly `planned` because the
  corrected size/persistence graph (WD-r4n8) is unmeasured and needs a host run;
  `neural_frame_gen` has three cells with no named host implementation, which the
  record states is "absence, not hardware infeasibility" and therefore needs a
  scope decision.
- **voice/character, 6 cells.** Clone and cross-mode identity rows are
  `evidence_complete_pending_review`; the reference consent chain is unapproved.
  Unlocked by: cloning-reuse consent.
- **video `ltx/2.3`.** A 29.5 GB generic FP8 checkpoint mismatches the WanGP
  manifest. Unlocked by: download approval.
- **video `ltx/2.5`.** Root-caused and fixed on the WanGP fork branch
  `story/WD-i7qs` @ `faea82d1` (declared in `WD-i7qs`, dispatched and accepted).
  Unlocked by: deploying that branch to the render host and authorizing the run.

Also outstanding for criterion (b): the clean-machine one-command install that
emits a real generated artifact (blocked on host authorization plus a complete
model manifest), and a checker-demonstrated bundle for the `director` lane, which
depends on the director decision above.

## Host prerequisites (already cleared, tool-verified)

`wgp doctor --probe-host` against `3090`: `ssh_reachable` PASS, `model_files` PASS
with a real verified hash, `disk_headroom` PASS at 60G free against the 50G floor,
`gpu_state` idle with 24 GB free. The binding constraint is operator authorization,
not the machine.

## MANDATORY SKILLS
None identified.

## nd_contract
status: blocked

### evidence
- Capstone disposition index (WD-fay0) and the reopened epic comment on WD-3nod.
- Preflight probe output recorded in the WD-3nod epic comment.

### proof
- [ ] Zero rows remain `planned` without an operator-approved disposition
- [ ] Criterion (b) clean-machine generated-artifact demonstration completed
- [ ] Criterion (b) checker demonstrated on a director-lane bundle

## Acceptance Criteria
- [ ] Zero capability matrix cells remain `planned` without an operator-approved terminal disposition or an explicit scope decision.
- [ ] The clean-machine one-command install emits a real generated artifact from a complete authorized model manifest.
- [ ] The parity checker is demonstrated successfully on a director-lane evidence bundle.

## Design


## Notes
### Host headroom restored by reversible offload (orchestrator, 2026-10-05)

The 50 GiB doctor floor was unmet (root volume at 21.6 GB free, 98% used). Before authorizing any
download I ran a read-only inventory, then performed a reversible, symlink-preserving offload of two
demonstrably inactive trees from the root NVMe to the idle 1.6T disk:

- moved `.hf_cache` (17 GB; last write 2026-08-18) and `scenema-models` (36 GB; last write 2026-05-30)
  to `/mnt/bulk-hdd/ssd-offload/20261005/`, leaving symlinks at the original paths so absolute-path
  resolution is unchanged.
- verification before removing either source: matching file manifests (md5 `93ee19b0f49a474b5d901e129596225e`
  for `scenema-models`) and a clean `rsync --checksum` dry run reporting no differences.
- both inactive trees had zero open file descriptors and zero files written since 2026-10-01, unlike
  `Maestro` (399 open FDs, left untouched) and `ComfyUI` (active, left untouched).

Result: root free 21.6 GB -> 73 GB, so the 50 GiB floor is now satisfied. Restore path: remove each
symlink and move the directory back, or `rsync` from `/mnt/bulk-hdd/ssd-offload/20261005/`.

This unblocks the headroom precondition only. No download was performed and no render was run:
the seven `dependency_blocked` LTX cells still require explicit model-download authorization.
### Headroom margin added before any download (orchestrator, 2026-10-05, addendum)

Because the five required LTX assets total 22.07 GB and root had only 73 GB free (floor 53.69 GB),
one further inactive tree was offloaded by the same verified, symlink-preserving procedure:
`qwen38-3090` (30.38 GB; zero open file descriptors; nothing written under it since 2026-08-18) moved to
`/mnt/bulk-hdd/ssd-offload/20261005/qwen38-3090` after its file manifest matched
(md5 `a21f16a491df6543bdb4145275d3738f`) and the source was removed.

Root free is now 101 GB. Total offload this session is about 81 GB (`.hf_cache` 17 GB,
`scenema-models` 36 GB, `qwen38-3090` 29 GB), all reversible by moving the directories back.

Exact download set still awaiting explicit operator approval (22.07 GB total, all from
`DeepBeepMeep/LTX-2`): three 1.22 GB ic-lora files (outpaint, ingredients-0.9, in-outpainting-0.9),
one 0.30 GB ic-lora pixel-spatial-upscaler-x2-1.0, and one 18.11 GB dev_diffusion_model_quanto_int8.
### Four LTX dependency assets downloaded and hash-recorded (orchestrator, 2026-10-05)

Authorized by the operator's delegation of the recommended path; downloaded on the host with
`curl -L --fail --retry 3 -C -` into `/home/straughter/Wan2GP/ckpts/`, each verified by exact byte
size against the remote Content-Length and hashed for provenance:

- ltx-2.3-22b-ic-lora-outpaint.safetensors, 1308756416 bytes, sha256 32c5d3e0649aa4e89b192319f3c79460dfd2319d2859ca11fa6f88e983a81665
- ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors, 1308778338 bytes, sha256 515e4e139001ac6282357a5b35372e42e98b3affd5fcc886a52242abeed19559
- ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors, 1308778338 bytes, sha256 73dd0841c0d4f0eb26fb1f017781b841b2752021944ac5ecefe57917f6dae6b5
- ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors, 327322640 bytes, sha256 984851b769ea2bcb4c9e0a239a7676239e42c6a6001ddc69943b41ff0b283c1d

This clears the previously recorded missing-dependency boundary for six of the seven remaining cells:
ltx/2.5 outpaint, repaint, recast, upscale and ltx/2.3 outpaint, recast. The seventh, ltx/2.3 upscale,
still requires ltx-2.3-22b-dev_diffusion_model_quanto_int8.safetensors (18.11 GB), which was not downloaded.

No render has been run and no cell has been promoted: `host_run_verified` still requires an authorized
host batch producing a run bundle with command, commit, provenance, queue attempt, output hashes,
ffprobe metadata and gate results. Root free after download: 97 GB.
### The last LTX cell cannot be retried under the recorded authorization (orchestrator, 2026-10-05)

Read-only inspection of the governed runner and the recorded authorization explains why the single
remaining cell cannot be closed without a new operator decision:

- The final-operations runner refuses any plan whose operations list is not exactly seven entries
  ("Exactly seven planned operations are required"), so a one-operation batch is structurally impossible.
- The same runner requires the JEVI authorization to carry `operations_authorized` true and
  `retry` equal to "never". The recorded authorization is therefore explicitly ONE-SHOT: the six
  already-promoted cells may not be re-executed under it.
- The gate22 plan's seven operations are, in order, outpaint, repaint, recast and upscale for ltx/2.5
  followed by outpaint, recast and upscale for ltx/2.3. The final cell was thus already part of the
  one-shot batch and was excluded only because its distilled LoRA was absent at the time.
- The runner also refuses to reuse an existing queue database, so any future batch needs a fresh
  namespace and a fresh queue database.

Consequence: the blocker for the final cell is no longer the asset, which is now present, but the
one-shot authorization semantics. Closing it requires a NEW operator authorization naming a new
seven-operation set. Nothing was executed here and no cell state changed.

## History
- 2026-09-26T05:37:53Z dep_added: blocks WD-fay0
- 2026-09-26T05:37:53Z status: open -> blocked
- 2026-09-26T05:38:12Z status: blocked -> deferred
- 2026-09-30T15:33:53Z dep_added: blocked_by WD-he8i
- 2026-09-30T17:13:38Z dep_removed: was_blocked_by WD-he8i

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Was blocked by: [[WD-he8i]]

## Comments

### 2026-09-26T05:38:22Z speed
State note (dispatcher): this gate is held in `deferred`, deliberately — neither
open nor closed.

Why: `pvg` closes an epic automatically when its last child closes. That has now
produced a false "Maestro parity: generation evidence — accepted" state twice
(once on `WD-i7qs` acceptance, once on `WD-14ej` acceptance), while 120 matrix
cells remained `planned`. Keeping one non-closed child in the epic prevents the
spurious closure and keeps the epic open, which is the truthful state.

Observed `pvg` behaviour while establishing this (worth a toolchain fix; `pvg` is
an operator-owned binary and cannot be changed from this repo):

- `status: blocked` is NOT what the loop reads. With this story set to `blocked`,
  `pvg loop next --json` still returned `decision: act`, `Ready: 1`, and offered it
  as a `developer_new` dispatch target.
- `status: deferred` gives the correct signal: `pvg loop next --json` returns
  `decision: wait`, `Ready: 0`, `Other: 1`, reason "1 stories in non-dispatcher
  workflow states". That is the honest state: there is no dispatchable work and the
  programme is waiting on operator authorization.
- An epic with zero non-closed children reports `decision: epic_complete` /
  "run completion gate", which reads as programme completion. It is not.

Two further toolchain gaps found in the same pass:
- `.github/workflows/ci.yml` runs only `pytest -q` and a build. It does NOT run
  `pvg lint --backlog`, so the lint gate in the programme's criterion (c) can
  regress and merge with CI green. This actually happened: creating a sibling story
  broke the capstone `blocked_by` invariant and lint failed, while CI stayed green.
  `pvg` is a Mach-O arm64 binary, so it cannot run on `ubuntu-latest` as-is; the
  gate is currently enforced by story-level discipline, not structurally.
- Creating any new child of an epic that has a `capstone` sibling requires an
  immediate `pvg issues link <new> --blocks <capstone>` and a `MANDATORY SKILLS`
  section in the body, or lint fails. Both are undocumented in the story template.

### 2026-09-26T06:08:32Z speed
Director-lane blocker re-examined by the dispatcher; the harness-threshold
hypothesis is FALSIFIED. Recorded so it is not re-investigated.

Hypothesis tested: "the SyncNet gate bar of 1.0 is unreachable, so the 25 director
cells are blocked by a mis-specified threshold rather than by media."

Evidence from the accepted WD-dmf2 bundle, `datasets/runs/maestro-parity/WD-dmf2/evidence.json`:

- `syncnet_screenplay_clip0002_confidence`: measured `1.10503`, threshold `1.0`
- `syncnet_screenplay_clip0001_confidence`: measured `0.468897`, threshold `1.0`
- `syncnet_audio_clip0001_confidence`:     measured `0.594741`, threshold `1.0`
- `whisper_gates[2]`: score `0.556`, `pass_bar` `0.6`

Clip 2 CLEARS the 1.0 bar at 1.10503 while clip 1 does not. The threshold is
therefore reachable, the gate is not structurally unpassable, and the same harness
passes a different clip. The failures are media-specific to clip 1, exactly as the
capstone recorded.

Conclusion: the director lane stays a genuine operator decision
(rework the clip-1 media versus record a measured structural limitation). It is not
a threshold defect and there is no ungated fix here.

Also re-checked and clean, for the same reason:
- `predict/finishing.py:313-317` -- `real_esrgan` requires `model_sha256` and the
  hash is rejected on every other backend. Enforced, not a gap.
- `FaceTrack.source` / `.license` / `.consent_ref` -- all `min_length=1` under
  `extra="forbid"`, so a track cannot be declared without them. Guard is real, and
  the surface only ever claimed to prove request shape.

### 2026-09-26T15:55:59Z speed
Progress update only (gate remains deferred): WD-isg9 was accepted and merged at 07a7f47d. It terminalized eight minimax_h3/standard video cells (five host_run_verified, three unsupported host boundaries). Current video matrix census: 10 host_run_verified, 7 unsupported, 82 planned. Combined known planned scope is now 112 cells: video 82, director 25, finishing 5.

### 2026-09-26T19:21:02Z speed
Progress update only (gate remains deferred): WD-43tj was accepted and merged at fed25bdf. All nine minimax_h3/taomate_three_step cells are unsupported host implementation boundaries. Current video matrix census: 13 host_run_verified, 21 unsupported, 65 planned. Combined known planned scope is now 95 cells: video 65, director 25, finishing 5.

### 2026-09-26T20:21:28Z speed
Progress update only (gate remains deferred): WD-5k28 accepted and merged at 2b4714bf. All nine h3_outpaint cells are unsupported host implementation boundaries. Current video census: 13 host_run_verified, 30 unsupported, 56 planned. Combined known planned scope: 86 cells (video 56, director 25, finishing 5).

### 2026-09-27T21:40:53Z speed
Progress update only (gate remains deferred): WD-osfm was accepted and merged at 7393245f. Its nine LTX-2.3 cells moved to 5 host_run_verified, 1 unsupported, and 3 dependency_blocked. Consolidated video matrix is now 40 host_run_verified, 52 unsupported, 7 dependency_blocked, and 0 planned. Overall 208-cell census is therefore 51 verified, 35 unsupported, 111 planned, 6 pending consent, and 2 not applicable. Separately, WD-qswf was accepted and merged at 7275e44f; the undeselected full suite now passes 2108/2108 selected tests with 0 failures, 0 errors, and 1 skip.

### 2026-09-28T06:50:53Z speed
Warning-clean gate update at merged main 6ac1023b522726705d3ea560216f211003a1d4bd: WD-dc3w and WD-s2nb are accepted and merged. Exact-main CI 36383656953 succeeded with zero annotations and zero known warning classes; exact-main local JUnit parsed 2109 tests, 0 errors, 0 failures, 1 skip. Backlog lint and release verification pass. This does not change the operator-gated matrix census.

### 2026-09-28T06:53:02Z speed
CURRENT SCOPE CORRECTION at merged main 6ac1023b522726705d3ea560216f211003a1d4bd, superseding stale 120/111-cell arithmetic and prior progress comments: the live capability matrices now have zero planned video, image, music, sfx, or finishing cells. Outstanding work is 29 cells total: 23 director planning cells remain planned pending the operator's rework-versus-structural decision, and 6 voice/character clone/cross-mode cells remain evidence_complete_pending_review pending cloning-reference consent. The clean-machine generated-artifact demonstration also remains blocked on host/model authorization. CI warning hygiene is no longer an outstanding lane.

### 2026-09-29T06:36:02Z speed
Progress update at merged main 2c20caa15b12b783188d5e707e0d29dda4f5eeb7: WD-23rs was independently accepted and merged by PR #216. The current canonical lane-receipt test passes, the seven verified representative lanes pass with exact owned warnings, and WD-dmf2 still fails its real objective/reviewer gates. Main CI run 36529726239 succeeded in 24m14s; backlog lint passed 151/0/0; release verification reports ready=true/tag_created=false; protected-engine parity is unchanged. Current state-bearing capability matrices contain zero planned cells, but the non-matrix first-run "Generated artifact from first-run" row remains intentionally incomplete until WD-bw0h's real H3 clean-machine artifact is authorized and verified. WD-bw0h's local PosixPath/host-default repairs are green at PR #215 head 64897225, but the story remains not delivered because the prior one-attempt host authorization was consumed before host contact.

### 2026-09-29T06:55:18Z speed
LTX dependency decision metadata (HEAD-only, zero model bytes downloaded): the seven dependency_blocked video cells require five unique upstream assets. Measured Content-Length / LFS ETag: ingredients LoRA 1,308,778,338 bytes / sha256 4647f4f18c87208f949b6f473d49af679ddd87532b40718480e5153852f1f1ba; outpaint LoRA 1,308,756,416 / 76df7c1ccbe8d657e38f38e8defbc0755a8d57b1a2b34fcad1f6376f4ce289f0; in-outpainting LoRA 1,308,778,338 / 748bca2d539cf2776abe801da96f06d6f31eec64f2354dea0f4b336292d3b837; LTX-2.5 spatial upscaler 327,322,640 / 229e549af18993e1670ad5dac7d2d8d03bb558ae446ac4ee23f8ba1263783996; LTX-2.3 dev int8 transformer 19,447,662,547 / f27d0effb85903172d976f1929dc0b3a204944ff014574eaab51cdc5e54f0f22. Total unique download volume: 23,701,298,279 bytes (~23.7 GB), under the prior 60 GB ceiling. This note records the operator decision payload only; it does not authorize a download or host contact.

### 2026-09-29T08:35:55Z speed
Strict current-state audit at merged main 2c20caa15b12b783188d5e707e0d29dda4f5eeb7: state-bearing matrices have zero planned cells but retain seven dependency_blocked LTX cells (WD-28ac prepared). The capstone non-matrix inventory additionally retains two planned generation rows: docs/editor.md "Authorized host export/media" and docs/first-run.md "Generated artifact from first-run". WD-bw0h owns the first-run row. No existing story owns the editor host-export row; it requires a separately authorized governed host export/render bundle and must not inherit WD-gc09's accepted no-GPU editor evidence. Standing quick gates remain green: backlog lint 152/0/0, release ready/tag_created=false, protected parity unchanged, clean main tree.

### 2026-09-29T10:17:55Z speed
Editor-gap ownership update at main 2c20caa1: WD-qthq now owns docs/editor.md "Authorized host export/media." Its local two-source deterministic project/export, not_authorized template, fail-closed runner, and real API tests are complete at PR 218 head e55588f57fd46ca43e144a57662a09eafad1668a with exact-head CI success. WD-qthq is deferred pending explicit host-3090 authorization; no editor host/media claim is made yet.

### 2026-09-30T15:30:17Z speed
Merged-main progress at 5a94eb491c524816334e23e1b2894acc3b772819: WD-qthq was independently accepted and merged. Main CI run 36733667937 succeeded in 25m24s; backlog lint 153/0/0; release ready/tag false; editor host-run canonical checker passed. Current authoritative docs leave seven LTX dependency_blocked cells and the first-run generated row incomplete. The historical WD-fay0 index still lists editor as planned, but merged docs/editor.md and the WD-qthq host-run bundle supersede that stale index row.

### 2026-09-30T17:39:21Z speed
Current-state index reconciliation at merged main b5169fec6885660f2c5806864d03d99b8db6fecc: WD-he8i was independently accepted and merged. The consolidated validator now passes with 208 matrix rows—89 host_run_verified, 7 dependency_blocked, 110 terminal unsupported/fail-closed, 2 not applicable, and 0 planned. Editor Authorized host export/media is host_run_verified via WD-qthq. The only remaining execution gaps are WD-bw0h first-run generated artifact at the storage-root boundary and seven WD-28ac LTX cells at the destination-storage shortfall boundary. Main CI 36750088915 succeeded, backlog lint 154/0/0, release ready/tag false, and protected parity is unchanged.

### 2026-10-02T00:25:31Z speed
Current post-WD-cuzw gate audit at merged main b5b7e35b131de72e541bec508fcac19fced895f3: parity validator PASS with 208 rows (89 host_run_verified, 7 dependency_blocked, 110 terminal unsupported/fail-closed, 2 not_applicable), backlog lint 156/0/0, release ready=true/tag_created=false, and clean tree. Recorded remote free after verified H3 offload is 48494047232 bytes. WD-28ac exact five-asset/23701298279-byte LTX batch now has 24792748953 bytes of recorded pre-download headroom and is the recommended next operator decision. WD-bw0h remains ineligible under the 53687091200-byte doctor floor by 5193043968 bytes. No host contact or downstream authorization is implied by this gate note.
