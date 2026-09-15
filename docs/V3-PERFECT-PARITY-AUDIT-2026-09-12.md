# v3 “Perfect” Parity Audit — 2026-09-12

## Verdict

The recovered `v3_pair_generator.py` still reproduces the operator-approved
film byte-for-byte on the current 3090. The repository pipeline does not run
the same semantic renderer path. It emits a non-empty `script` field, which
makes WanGP dispatch the job to its multishot shortcut. That shortcut does not
forward `image_start`, `image_refs`, or `audio_guide` to generation. The repo
then discards the model's generated audio and lays the original guide WAV over
the unrelated video. This exactly matches the operator's observation: speech
audio is being laid on top of mouth motion generated for something else.

This is not a bad seed and is not evidence that the validated v3 recipe stopped
working. It is a control-plane/renderer-payload architecture error.

## Controlled A/B evidence

Both runs used the same 3090, current WanGP checkout, model checkpoint paths,
input fixtures, prompt text, seed 904, profile 2, and `sdpa` attention.

| Property | Recovered temporary generator | Repo control |
|---|---|---|
| Settings carrier | `prompt`, no `script` | `prompt` plus non-empty `script` |
| WanGP log path | Normal Ref2VA | Multishot shortcut |
| Log marker | `Encoding H3 prompt and references` | `[MULTISHOT] Detected script with 1 shots` |
| `image_start` used by generator | Yes | No; omitted from multishot config |
| `image_refs` used by generator | Yes, two refs | No; omitted from multishot config |
| `audio_guide` used by generator | Yes | No; omitted from multishot config |
| Canonical audio | Native H3 A/V output | Guide WAV remuxed over generated video |
| Chain extraction | `-sseof -0.05` | `-sseof -0.1` |
| Assembly | filter concat, H.264 CRF 18 + AAC | concat demuxer, stream copy |
| Final stream start | video 0, audio 0 | video +0.041992 s, audio 0 |

The recovered generator rerun produced the known hashes again:

| Artifact | MD5 |
|---|---|
| `v3_c1.mp4` | `be96a3027d1fa8f4b14454118ab4d97a` |
| `v3_c2.mp4` | `6b485e84f875ccc30a87476b34bf38d3` |
| `v3_pair.mp4` | `c523919b6ac93a29edd43de75e424033` |

The direct rerun happened immediately before the repo control and was
byte-identical, so the model, seed, host, checkpoint, and current WanGP legacy
Ref2VA path are demonstrably still capable of the perfect result. The repo
wrapper is the isolated variable.

### Exact renderer-settings shape difference

The recovered final cut-2 settings contain these keys which the repo payload
omits: `audio_guide2`, `keep_frames_video_source`, `premise`, `resolution`,
`video_guide`, and `video_source`.

The repo payload adds these keys which the recovered payload did not contain:
`audio_policy`, `audio_provenance`, `audio_qc`, `embedded_guidance_scale`,
`force_fps`, `frames_per_shot`, `guidance_scale`, `height`,
`multi_prompts_gen_type`, `num_inference_steps`, `profile`, `requested_frames`,
`script`, `speaker_manifest`, and `width`.

Most critically, `script` is not inert metadata: its presence changes the
WanGP implementation that executes the job. The other repo-only operational
fields should also live outside the renderer payload so future WanGP changes
cannot reinterpret them as generation controls.

Visual evidence agrees with the dispatch diagnosis. The perfect cut retains
the demon, grandmother, and soul-on-rack composition from the pinned image.
The repo control removes the demon and re-stages the grandmother and soul,
which is what a text-only regeneration would do after the image conditioning
inputs were omitted.

## Finding 1 — renderer metadata and renderer settings are mixed

`predict/job_config.py::WanGPJobConfig` requires a non-empty `script`.
`predict/render_profiles.py::Ref2VAProfile.build_settings()` reuses that generic
multishot config for Ref2VA and therefore always serializes `script`.

In the current WanGP CLI, `wgp.py::process_tasks_cli()` treats the mere presence
of `task.params.script` as a dispatch flag. It bypasses the normal Ref2VA path
and calls `models/minimax_h3/multishot.py::generate_multishot()`.

The repo's job envelope, provenance, policy, QC fields, and the renderer's
actual settings must be separate typed objects. Operational metadata must not
be dumped into WanGP's behaviorally overloaded settings document.

### Required change

Introduce a dedicated `Ref2VASingleShotSettings` serializer. It must not inherit
from or pass through `WanGPJobConfig`, and it must emit no non-empty `script`.
The v3 renderer payload is a strict allowlist matching the recovered settings:

- `model_type=minimax_h3_ref2va_pruned`
- `image_prompt_type=S`
- `image_start`
- `video_prompt_type=I`
- exactly two `image_refs`: `[image_start, silent_character_face]`
- `audio_prompt_type=A`
- `audio_guide`
- `video_source=null`, `video_guide=null`, `keep_frames_video_source=""`
- `video_length=56`
- `resolution=480x832`
- `seed=904`
- exact prompt text

Profile 2 and `sdpa` remain CLI arguments, not invented renderer fields.
Provenance, policies, manifests, and QC stay in the repo job envelope/sidecars.

Add a pre-render dispatch guard for Ref2VA jobs:

- reject any non-empty `script`;
- after render, require `Encoding H3 prompt and references` in the log;
- reject `[MULTISHOT]` in a Ref2VA log.

## Finding 2 — WanGP multishot drops all three conditioning inputs

The current WanGP multishot dispatch copies width, height, frames, steps,
guidance, seed, FPS, and memory settings into `_ms_config`. It does not copy:

- `image_start`;
- `image_refs`;
- `audio_guide`;
- `image_prompt_type` / `video_prompt_type` / `audio_prompt_type`.

Therefore the repo-produced “Ref2VA” clips were text-only generations. The
files were loaded during settings parsing but were never supplied to the model.
Last-frame chaining and Picture-N binding existed only in metadata.

### Required change

Do not route Ref2VA dialogue jobs through WanGP multishot. Keep this as a hard
guard even if WanGP later adds those fields to multishot; support should be
enabled only by an explicit, versioned capability probe and integration test.

## Finding 3 — the audio policy deliberately disconnects audio from video

The original generator copies WanGP's output MP4 and concatenates that native
audio/video pair. The repo enforces the opposite policy in three places:

- `ContinuationExtras.audio_policy_discard_rendered=True`;
- `Ref2VAProfile` emits that policy;
- `run_ref2va_runtime` rejects any policy that retains native rendered audio.

`production_ref2va_render()` then creates `raw.mux.mp4` by copying video from
WanGP output and audio from the guide. `run_ref2va_runtime()` remuxes the guide
again. The model's synchronized audio is never the canonical artifact.

Measured against the cut-1 input guide:

| Audio carrier | Maximum waveform correlation | Best offset |
|---|---:|---:|
| Perfect native H3 output | 0.951625 | 25 ms |
| Repo multishot native output | 0.037157 | 136 ms |
| Repo `raw.mux.mp4` | 0.993628 | 0 ms |
| Repo final `remux.mp4` | 0.999888 | 0 ms |

Whisper also proves the generated audiovisual content differs:

| Source | Transcript |
|---|---|
| Perfect native H3 cut 1 | “Who hushed now, dear? Have a cookie.” |
| Repo multishot native cut 1 | “Speaks the lard in your hung harrick.” |
| Repo final remux | “So hush now dear, have a cookie.” |

The final remux contains the right words only because the source guide was laid
over a video whose native generated speech was unrelated.

### Required change

Make audio carrier an explicit recipe policy, not a global G4 invariant:

- `native_h3_aligned` for validated H3 Ref2VA dialogue;
- `external_source_remux` only for recipes that have a real measured A/V-sync
  correction stage.

`production_ref2va_render()` must return and fetch the true WanGP output once.
It must not pre-remux. Preserve the native MP4 and its hash. Any alternate mux
is a named derivative, never `raw` and never the only ledgered artifact.

## Finding 4 — Whisper post-gating is tautological

`scripts/run_jobs.py` supplies the input guide as the pre-gate path and the
final external-audio remux as the post-gate path. Because the remux contains
that same guide, the post gate validates the mux operation, not whether H3 used
the audio to drive the video.

The bad repo control received KEEP with passing pre/post transcripts while the
actual WanGP-native transcript was gibberish.

### Required change

For Ref2VA:

1. Whisper-gate the prepared guide before rendering.
2. Whisper-gate the true native WanGP output before any derivative mux.
3. Fail if the native transcript does not match the intended line.
4. If an external derivative is produced, gate it separately and run an actual
   audiovisual offset/synchrony measurement.

## Finding 5 — the vision judge does not measure lip sync

The current judge samples only start/middle/end still images. It cannot observe
temporal mouth motion, hear audio, estimate offset, or compare phonemes to
visemes. Its `mouth_sync` name is therefore false precision. It assigned
`mouth_sync=1.0` to both bad control cuts.

### Required change

Rename the still-frame score to `speaker_mouth_activity` or equivalent. Add a
real audiovisual gate that consumes the full video and audio track. At minimum
it must estimate speech/mouth-motion offset over time; the stronger form also
scores phoneme/viseme agreement. Operator review remains the final acceptance
authority until that gate is calibrated against the perfect and rejected set.

## Finding 6 — there is no single versioned recipe authority

The recovered perfect recipe is profile 2, two refs, and the original S1/S2
prose at 56 frames. `services/director/renderers/h3_recipe.py` declares a
different “verified” recipe: profile 3, three refs, 480x832, and a different
Picture/Subject prompt grammar. `services/chain/controller.py`,
`predict/render_profiles.py`, and `host/wangp_adapter.py` each add further
defaults or special cases.

### Required change

Create an immutable recipe registry. The first entry should be
`v3_pair_20260906`, containing every behavior-affecting value:

- renderer payload schema and exact key presence/absence;
- prompt builder/version;
- model type, profile, attention, seed, frame count;
- image-ref ordering/count;
- audio-prep filter and accepted duration range;
- native-audio policy;
- chain-frame extraction command;
- assembly command;
- QC thresholds.

Planning, rendering, QC, chaining, and assembly must consume the same recipe
object. String names with scattered conditionals are insufficient.

## Finding 7 — chain-frame selection differs

The perfect generator extracts with `-sseof -0.05 -update 1 -frames:v 1`.
The repo uses `-sseof -0.1 -frames:v 1`. Pixel comparison confirms these select
different frames. More importantly, the current multishot route ignores the
resolved chain image entirely.

### Required change

After Ref2VA dispatch is corrected, make `chain_seek_from_end_s=0.05` part of
the versioned v3 recipe and extract from the accepted native MP4. Record the
PNG hash and verify it is the exact next cut's `image_start` and Picture 1.

## Finding 8 — assembly changes timestamps

The perfect generator uses the concat filter and re-encodes video with x264
CRF 18 plus AAC. The repo uses the concat demuxer with `-c copy`. The failed
control emitted a non-monotonic DTS warning and produced video starting at
`0.041992` seconds while audio starts at `0.000000`. The perfect assembly has
both streams starting at zero.

### Required change

Add a recipe-owned audiovisual filter-concat assembly mode matching the old
command. Validate both stream start times are zero and reject non-monotonic
timestamps. Stream-copy concat may remain for non-dialogue recipes only.

## Finding 9 — declared audio duration is not measured duration

The original guides measure approximately 2.330417 s and 2.096 s. The repo job
declared both as 2.333333 s and `audio_length_frames=56`; the profile validated
the declarations without probing the files.

### Required change

Probe prepared audio at the data-plane boundary. Persist source duration,
prepared duration, sample rate, channel count, and hash. Validate measured
values, not caller claims. Keep the original v3 audio-prep semantics as a
versioned mode: leading-silence removal, 100 Hz high-pass, +9 dB, trim at 2.4
seconds, and pad by 0.5 seconds only when under 2.0 seconds.

## Finding 10 — the failed control mislabeled a remux as native

`scripts/run_v3_native_control.py` selects `raw.mux.mp4` and records it as
`native_h3_raw_multiplexed_audio`. That file is the externally remuxed guide,
not the native WanGP output. The true output existed remotely as `raw.mp4` but
was not fetched or ledgered by the normal path.

### Required change

Retract that run's completed/KEEP quality claim. Use explicit artifact roles:
`renderer_raw`, `native_av`, `external_audio_derivative`, `assembled`. Each
role must record source hashes and stream metadata; filename inference is not
acceptable.

## Finding 11 — tests prove internal assumptions, not renderer semantics

Current tests explicitly require `discard_rendered_audio=True` and do not test
the downstream WanGP dispatch semantics of `script`. There is no test asserting
that a Ref2VA job reaches prompt/reference encoding, no native-output transcript
gate, and no exact settings-key snapshot for the perfect recipe.

### Required change

Add three test levels:

1. **Offline contract:** exact normalized v3 renderer-settings snapshot, exact
   CLI argv, no `script`, two refs, exact chain and assembly argv.
2. **Host smoke:** render log must contain Ref2VA reference encoding and must
   not contain `[MULTISHOT]`; native audio transcript must pass.
3. **Golden GPU canary:** on the pinned host, reproduce the known MD5s above.
   The recovered run is deterministic, so byte mismatch is a release failure.

Only after the golden canary passes should a new-premise two-cut test vary
characters, setting, lines, and audio while preserving the execution recipe.

## Finding 12 — renderer environment provenance is incomplete

The 3090 WanGP checkout is at commit
`4c93b64a47b5b0a915f2abec2ce754be98227150` with tracked modifications. The
wangp-dspy run ledger records its own repository SHA but not the full renderer
tree state or checkpoint hashes.

### Required change

Record and preflight:

- wangp-dspy commit and dirty diff hash;
- WanGP commit and dirty diff hash;
- model/checkpoint SHA256 values;
- Python, Torch, CUDA, ffmpeg, and driver versions;
- exact emitted renderer settings bytes and CLI argv;
- every input and output artifact hash.

An approved renderer fingerprint should gate production runs.

## Implementation order

1. Split job envelope from strict Ref2VA renderer settings; remove `script`.
2. Add the Ref2VA dispatch/log guard.
3. Return and preserve true WanGP-native output; remove double remux.
4. Replace global G4 with recipe-selectable audio-carrier policy.
5. Gate native audio and add real A/V sync measurement.
6. Add immutable `v3_pair_20260906` recipe authority.
7. Restore v3 chain extraction and filter-concat assembly behavior.
8. Add measured audio metadata and renderer fingerprints.
9. Add offline snapshot, host smoke, and exact-MD5 golden canary.
10. Run the different-premise two-cut generalization test only after the
    golden canary passes.

## Acceptance boundary

“Repo path completed” is not a quality verdict. A v3 parity run is accepted
only if all of the following are true:

- normal Ref2VA log marker present; multishot marker absent;
- input start/ref/audio assets appear in the actual generator call;
- native output transcript passes;
- true A/V sync gate passes;
- two-ref ordering and chain-frame hashes are proven;
- assembled stream timestamps both start at zero;
- golden control MD5s match on the pinned host;
- operator visual/audio verdict is KEEP.
