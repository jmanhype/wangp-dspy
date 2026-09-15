# H3 dialogue continuation: recovered v3 contract

## Correction — 2026-09-12

**This section supersedes the historical recipe below for September 6 v3
parity.** The earlier single-ref, compulsory tail-padding and external-remux
contracts are not the recovered v3 recipe. The original pair has the
operator's “perfect” verdict; new generations do not inherit that verdict.

Source: `datasets/runs/provenance/v3_pair_generator.py`. Versioned values and
verbatim prompts: `predict/v3_recipe.py`. Diagnosis:
`docs/V3-PERFECT-PARITY-AUDIT-2026-09-12.md`. Repair status:
`docs/V3-PARITY-FIX-2026-09-12.md`.

### Renderer wire contract

Use `golden_v3` in the repo planner. The Ref2VA payload must never pass through
the generic multishot `WanGPJobConfig` serializer.

| Setting | Recovered v3 value |
|---|---|
| model_type | `minimax_h3_ref2va_pruned` |
| image_prompt_type | `S` |
| image_start | Master frame for cut 1; extracted accepted predecessor frame thereafter |
| video_prompt_type | `I` |
| image_refs | Exactly `[image_start, silent_character_face]`, in order |
| audio_prompt_type | `A` |
| audio_guide | Prepared single-speaker WAV |
| audio_guide2, video_source, video_guide | `null` |
| keep_frames_video_source | Empty string |
| video_length | 56 at 24 fps, approximately 2.333 seconds |
| resolution | **Request** `480x832`; original **output** measured `704x576` |
| seed | 904 for the golden control, no automatic reseeding |
| CLI | `--profile 2 --attention sdpa` |
| prompt | Recovered S1/S2 prose; Picture 2 binds the silent face |

S1 is the current speaking role, not a permanent roster index. S2 is the silent
character for that cut. The original baseline omitted explicit steps, FPS and
guidance overrides; key absence matters too. The observed runtime uses 20
steps, but this is not a complete environment lock.

**No `script` or multishot fields may enter the renderer payload.** On the
audited WanGP checkout they select a shortcut that drops image/audio
conditioning. Policy, manifests and QC remain sidecars. The actual transport
is `wgp-settings.json`; the separate `settings.json` is the repo audit doc.
The log must show `Encoding H3 prompt and references`, with no `[MULTISHOT]`.
`conditioning-evidence.json` records mapped hashes and measured guide data.

### Audio and media operations

For unprepared source audio, `prepare_v3_turn_audio()` uses the original filter:

```text
silenceremove=start_periods=1:start_threshold=-40dB,highpass=f=100,volume=9dB,atrim=0:2.4
```

Only when shorter than 2 seconds does it add a 0.5-second tail. No universal
leading silence, resampling, time stretching or exact-grid fit. Already
prepared fixtures are not boosted again. Probe actual duration, channels,
sample rate and SHA256; do not invent guide duration from video length. The
original grandma/soul guides measure approximately 2.330417/2.096 s, mono at
24 kHz. The September 7 grid-padding acceptance amendment is a historical
variant, not silently rewritten or claimed as exact September 6 parity.

**Preserve native H3 audiovisual output.** Ref2VA requires
`discard_rendered_audio=False`; neither adapter nor runtime replaces its audio
with the guide. The compatibility filename `remux.mp4` currently remains, but
must be byte-identical to `raw.mp4`, with hashes and `audio_carrier=native_h3`
recorded. Old external-remux jobs need replanning, not silent adoption.

Whisper gates the guide before GPU work and the **native** output afterward,
at 0.6. Matching words is not a lip-sync measurement. Chaining uses:

```text
ffmpeg -y -v error -sseof -0.05 -i CUT.mp4 -update 1 -frames:v 1 NEXT_SEED.png
```

Assembly uses decoded audiovisual filter concat, H.264 CRF 18 + AAC—not
concat-demuxer stream copy. Check actual assembled timestamps and frame count.

### Honest quality boundary

Three still frames can assess identity/composition/mouth activity against the
actual input plate, **not** audio timing or phoneme/viseme synchronization.
Evidence reports `mouth_sync=null`, `av_sync_verified=false`. Mechanical
completion yields **NEEDS REVIEW**, never automatic KEEP for this lane.

`scripts/run_v3_native_control.py` runs the exact pair through DirectorRun,
queue, `render_for_job`, Whisper/vision QC, chaining and assembly. Compare the
actual output with the original hashes and audible/visible content before
claiming reproduction. Different-premise and deep-chain reliability require
separate experiments.

---

## Historical September 3/4 notes — not the v3 contract

The following is retained as historical context, not current v3 instructions.

Two validated modes:

MODE A — packed single generation (15s, 362f):
    One Ref2VA generation with a SHOT 1 / CUT TO / SHOT 2 prompt
    produces a multi-cut film with model-made hard cuts in one render.
    Validated: devilgrandma, aisle13, magnitude (3/3 QC-passed).
    VRAM: 362f needs --profile 2 on a 24GB card.

MODE B — last-frame chain (dialogue, per-cut speaker control):
    Each ~2.33s grid-aligned cut (56f = 5+17x3) uses the previous cut's decoded last frame as
    both image_start and the sole image_ref; audio_guide carries the
    single-speaker wav (2s speech plus a ~0.33s silence tail, RMS/transcript-gated); the prompt binds
    (S1) speaker-in-sync / (S2) lips-closed and swaps per turn.
    Seam measured 3.0-2.1/255 across a 6-cut chain (operator:
    "perfect continuation").

Config skeleton (wgp --process settings.json):

    MODE A                          MODE B
    ----------------------------    ---------------------------
    model_type  ref2va_pruned       model_type  ref2va_pruned
    image_prompt_type "S"           image_prompt_type "S"
    image_start <master plate>      image_start <prev cut last frame>
    video_prompt_type "I"           video_prompt_type "I"
    image_refs  [<plate>]           image_refs  [<same frame>]
    video_length 362                audio_prompt_type "A"
    resolution  "480x832"           audio_guide <single-speaker wav>
                                    video_length 56

Prompt skeleton (both modes):

    integrated_multimodal_description:
    [MODE A: SHOT 1 (0-5s): ... CUT TO SHOT 2 (5-10s): ...]
    [MODE B: (S1) <speaker> ... mouth in exact sync with the audio.
             (S2) <other> stays silent: lips pressed closed...]
    overall_soundscape: ...
    non_diegetic_music: N/A

Known constraints (measured):
    - audio_guide is Ref2VA-only (FL2VA rejects: pipeline.py:737).
    - FL2VA GV+K anchors to source frame 0 (wgp.py:7479 start_frame=0);
      the negative-keep tail patch exists but content tests preferred
      the Ref2VA single-frame lane.
    - Audio refs must be 2-15s, single-speaker; RMS-flat slices
      (music/no-speech) produce wrong-speaker or silent cuts.
    - wgp zombies + /tmp/wgp_queue.lock cause false "Queue completed":
      check log mtime vs clock, pkill all wgp, rm lock, spawn via
      Python subprocess with start_new_session=True.

Render (3090):
    cd ~/Wan2GP && ./venv/bin/python wgp.py --process <settings.json> \
        --profile 2 --attention sdpa
