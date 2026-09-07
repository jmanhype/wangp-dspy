"""H3 continuation-chain recipe — validated 2026-09-03/04 (operator-approved).

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
"""
