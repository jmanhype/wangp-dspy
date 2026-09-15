# v3 parity repair — implementation status

## Checkout and scope

Work is in `/Users/Shared/HermesWorkspace/wangp-dspy`, branch
`codex/golden-v3-lf003-repro`, based at
`6565d3e81d6d110d2ae2d7b831e09db189fc74da`. HEAD advanced during the work to
`23dd219ff76b406f8d41d81ea4f66583f936d966` (the separate cut-1 operator-verdict
commit). The repair code remains local and uncommitted. This is a dirty
development checkout, **not** a fresh-clone acceptance run. Pre-existing edits
were preserved. No claim here means the repair was merged or pushed, or that
the operator has given a new whole-pair verdict.

The original audit describes the broken path. This document records repairs
separately; it does not retroactively bless old renders.

The observed root cause was the nonempty `script` field entering WanGP's
`[MULTISHOT]` shortcut, where image-start, image-reference and audio-guide
conditioning were dropped. The repo then replaced the generated soundtrack
with the guide, twice across adapter/runtime seams. Whisper could therefore
approve the correct words without proving that audio drove the video. The
repaired native route preserves conditioning and H3's generated audio together.

## Implemented

1. **Dedicated Ref2VA transport.** `predict/ref2va_settings.py` rejects
   multishot fields and unresolved chain placeholders. The adapter sends
   `wgp-settings.json`, not the operational envelope. Logs must prove native
   prompt/reference encoding and must not contain `[MULTISHOT]`.
2. **Native audio preservation.** Both guide-replacement muxes were removed
   from Ref2VA. Native/final hashes must match. Old discard-audio jobs require
   replanning; non-Ref2VA external-remux lanes remain separate.
3. **Meaningful transcript gating.** Pre-render Whisper reads the guide;
   post-render Whisper reads native generated audio. QC/adoption requires
   native runtime evidence and matching hashes, preventing old remux adoption.
4. **Honest vision and verdicts.** Stills measure mouth activity, not A/V
   synchrony: `mouth_sync=null`, `av_sync_verified=false`. The actual seed
   image is part of the comparison. Ref2VA completion is NEEDS REVIEW, not KEEP.
5. **Versioned golden route.** `predict/v3_recipe.py` contains the recovered
   prompts, profile/seed/request resolution, guide filter and tail seek.
   `golden_v3` selects the recovered two-ref grammar; the acceptance bundle
   entrypoint defaults to it. Golden failures cannot silently reseed.
6. **Recovered media operations.** Chain extraction uses `-sseof -0.05` and
   `-update 1`. Assembly uses AV filter concat, x264 CRF 18 + AAC. New-source
   v3 prep preserves trim/highpass/+9dB behavior without forced exact-grid
   padding or double-processing original fixtures.
7. **Measured evidence.** The host boundary records mapped asset hashes,
   measured guide duration/rate/channels, wire settings, local source hashes
   and remote dispatch/model-code hashes.
8. **Corrected control entrypoint.** `scripts/run_v3_native_control.py` now
   selects true `raw.mp4`, not externally remuxed `raw.mux.mp4`, and traverses
   the repaired repo production path.
9. **Pinned-artifact regression gate.** `predict/v3_canary.py` checks both
   native cuts, the chained seed and assembled pair against original SHA256s,
   then verifies frames, FPS and zero audio/video start timestamps. The golden
   runner invokes this before emitting its final run record. A mismatch writes
   a failed report and returns failure; it does not reseed or change a verdict.

## Offline validation

2026-09-12 latest full suite: **1,313 passed; 1 skipped; zero failures or
collection errors** (1,314 collected, 16.647 s, local test timestamp 19:22).
JUnit: `datasets/runs/pull/v3-native-fixed-20260912/parity-tests.xml`.
`git diff --check` passed.

Coverage includes literal prompts versus recovered script, exact wire keys,
dispatch guards, native preservation, wrong-native-words rejection despite a
correct guide, chain/concat argv, real ffmpeg audio prep, honest still scores
and golden no-reseed behavior. Tests that demanded the broken remux/timing
contracts were updated. Unrelated stale DSPy `reasoning` and host-health/log
test fixtures also needed correction. Passing tests is **not** a quality verdict.

## Live validation — exact two-cut reproduction complete

Run ID: `v3-native-fixed-20260912`.

```text
./.venv/bin/python scripts/run_v3_native_control.py \
  --run-id v3-native-fixed-20260912 \
  --db datasets/runs/pull/v3-native-fixed-20260912/jobs.db \
  --ledger datasets/runs/pull/v3-native-fixed-20260912/runs.jsonl \
  --output datasets/runs/pull/v3-native-fixed-20260912/assembled.mp4
```

Cut 1 is `render-0059`. Its log contains **Encoding H3 prompt and references**
followed by denoising. The actual wire has the original prompt, seed 904,
request 480x832, 56 frames, two ordered refs and original prepared guide; no
`script`. The first denoising step took approximately 50 seconds and WanGP
estimated approximately 18 minutes for the cut. The old approximately 4-minute
shortcut renders are not an equivalent benchmark.

### Cut 1 independently verified and operator accepted

The original render finished in 18m34s. Its filename contained spaces and
punctuation, exposing output-discovery and SSH argument-boundary defects.
After those fixes, explicit recovery reused that completed render in a new
attempt namespace, `render-0062`, without new GPU rendering. `render-0059`
and all failed attempt records remain intact.

- MP4 MD5: **be96a3027d1fa8f4b14454118ab4d97a**, identical to original cut 1.
- SHA256: **c790452320e6893227caa0827c941a3e610403e776d7b833ae94d5ef135439a6**.
- Both decoded video and decoded audio are identical; pixel MAE is 0.
- 56 frames, 704x576, 24 fps; both streams begin at zero.
- Native pre/post Whisper: **0.857 / 0.714**, threshold 0.6.
- Operator verdict supplied via Hermes: “fucking perfect”; the matching
  entry is independently visible in commit `23dd219`. This is a **cut-1**
  verdict, not a new whole-pair verdict.
- Re-QC visual activity/action/identity: **0.85 / 0.90 / 0.95**, threshold 0.7.
  Phonetic A/V synchrony remains explicitly unmeasured by the still judge.

The first still-judge response was the literal all-zero schema example, with
no observations. This rejection remains recorded. The prompt was corrected
to specify score semantics without a copyable numeric answer, and to request
brief visible observations. One explicit re-QC of the **same bytes** passed
with observations about grandma's speaking pose and the silent soul. No
threshold was lowered and no generated score was fabricated or waived.

### Cut 2 independently verified

`render-0063` completed the normal native Ref2VA path in 18m15s. Its input was
the accepted predecessor's extracted frame and grandma's silent-face ref,
original soul guide, verbatim cut-2 prompt, seed 904, profile 2 and 56 frames.
The extracted chain PNG is **byte-identical** to original `v3_c2seed.png`:
SHA256 `f40f44155a8d61862bf96b136108fd262a9a7f612bcaa04b8fa9becc32861656`.

- MP4 MD5: **6b485e84f875ccc30a87476b34bf38d3**, identical to original cut 2.
- SHA256: **617aa35d7ed542ef75be6b89594f249220559dbeeff809a9cadc2d38556bda65**.
- Both decoded video and decoded audio are identical; pixel MAE is 0.
- 56 frames, 704x576, 24 fps; both streams begin at zero.
- Native pre/post Whisper: **0.800 / 0.600**, threshold 0.6.
- Visual activity/action/identity: **0.90 / 0.85 / 0.95**, threshold 0.7.
- Both jobs are `done`; their machine verdict remains NEEDS REVIEW.

### Assembled pair and permanent canary — passed

New output: `datasets/runs/pull/v3-native-fixed-20260912/assembled.mp4`.
This is the two newly rendered native cuts, concatenated through the repo's
host assembly seam, not the original video copied into a new output path.

- MP4 MD5: **c523919b6ac93a29edd43de75e424033**.
- SHA256: **0146285a9ea6441b4688e1651a467c9af189e9b63e1403ffbf92938825294a51**.
- **Byte-for-byte identical** to original `v3_pair.mp4`, 757,629 bytes.
- Decoded video and decoded audio also match; pixel MAE is 0.
- 112 frames, 704x576, 24 fps, 4.666667 seconds; both streams begin at zero.
- `golden-canary.json` in that run directory passed against the four pinned
  original hashes. `pair-golden-verification.json` additionally records the
  decoded comparisons. The append-only `runs.jsonl` carries the verification.
  Verification record SHA256:
  `ca504d75066123185f97abdb883a92a9bb19a80b2897e944d7e9e9b64eb2f834`.
- The exact regression guard also rejects shifted A/V timestamps, incorrect
  frame counts or FPS, missing audio, missing files and hash mismatches.

Implementation/test corrections occurred after the initial process launched;
source hashes are recorded, but this remains a development canary, not an
immutable fresh-clone release/environment proof. Exact recovery of this
two-cut reference does not prove quality for arbitrary new premises.

### Further boundaries exposed and repaired during recovery

1. **Native filenames:** the old basename regex excluded spaces/punctuation.
   Discovery now accepts legitimate names while still checking real files,
   timestamps and rejecting path components/control characters. Regression
   tests use the native filename shape, not just `multishot_TIMESTAMP.mp4`.
2. **SSH argument boundaries:** OpenSSH joins command arguments into shell
   text. Passing a Python argv through unchanged split native filenames into
   multiple operands. Structured `SshHost.run_probe` commands now use quoted
   argv serialization; tests emulate actual remote-shell parsing, including
   spaces, apostrophes and shell metacharacters. The legacy one-string
   detached-launch surface remains explicitly separate in behavior.
3. **Completed-render recovery:** recovery requires the exact prior wire,
   unchanged input/code hashes, a completed native log, its authoritative
   saved-output line, a caller-specified native SHA256, valid containment and
   frame count. It copies into a new attempt directory, mirrors the verified
   log to both hosts, and executes ordinary runtime/QC. `--resume` refuses
   unrelated databases and preserves dependency/attempt history.
4. **Assembly environment:** the original concat ran with the 3090's FFmpeg
   6.1.1, while the Mac has 8.0.1. The golden control now requests host-side
   assembly through the repo seam, with input/output SHA256 verification and
   recorded FFmpeg version, rather than claiming byte parity across codecs.

The old `v3-native-control-20260912b` completed/native claim was retracted by
append-only corrections in its existing `runs.jsonl`. Original records and
artifacts were not deleted or rewritten.

## Remaining boundaries — not claimed fixed

- A calibrated full-video/audio phonetic synchrony judge is not implemented.
  Whisper and stills are explicitly insufficient; operator A/V review is needed.
- Checkpoint hashes and complete Python/Torch/CUDA/driver/ffmpeg versions are
  not yet an approved renderer lock. Defaults inherited from WanGP matter.
- The golden route consumes the versioned recipe, not every historical
  director/experimental entrypoint. Explicit alternatives must not be described
  as recovered v3. Consolidation of those older APIs remains separate work.
- Assembly timestamps/frames are now verified by the golden canary; there is
  not yet a generic fail-closed assembly probe for every lane.
- Neither new-premise generalization nor six-cut/deep-chain acceptance is
  proven by a two-cut control. Latent protection remains a separate cycle.
- Earlier failures on the conditioning-dropping multishot route do **not**
  establish an H3 chain-depth ceiling. They cannot justify blaming latent
  drift before measuring a correctly conditioned chain. Historical operator
  artifact verdicts stay intact; their prior model-ceiling explanation is not
  carried forward as a demonstrated property of native Ref2VA.
