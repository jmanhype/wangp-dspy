# FL2VA keyframe targets + R2I pose-target step

First/last-frame (FL2VA) rendering with explicit end-of-shot keyframe
targets, plus the R2I (render-to-image) step that produces an
H3-native last-frame still.

Contract scraped 2026-09-01 from official/community FL2VA guides:
- minimax3.com/blog/minimax-h3-first-last-frame (first/last mode)
- @yu_ichi_suzuki technique post (R2I: minimum-length R2V with refs +
  pose, extract final frame as the FL2VA last-frame still)
- Official guide modes T2VA / I2VA / FL2VA / L2VA ( WanGP H3 handler:
  `image_prompt_types_allowed "TSEVL"`, `end_frames_always_enabled` )

## The 4-beat prompt contract

`build_fl2va_prompt(clip, plan, ...)` in `services/chain/keyframes.py`
emits, in this order:

1. MANDATORY alignment line (first line):
   "How the reference pictures align with the target video — Picture 1
   (from Shot 1) aligns with the 0.00-second mark of the target video;
   Picture 2 (from Shot N) aligns with the S.SS-second mark of the
   target video." N = actual final shot index; S.SS computed from the
   EXISTING chain frame math (clip.duration_s, itself frames/fps).
2. Beat 1 — `[Shot 1] <style>, <what Picture 1 shows>, matching the
   position, framing, and lighting established by Picture 1.`
3. Beat 2 — camera motion as a natural sentence: "The camera pushes in
   with small amplitude at slow speed." Type + amplitude + speed,
   NEVER stacked tags; default amplitude/speed (medium/normal) omitted.
4. Beat 3 — 2-3 intermediate states IN ORDER, never re-describing the
   frame content: "Toward the end of the shot the differences narrow
   until <what Picture 2 shows>, landing on the exact pose, spacing,
   and composition established by Picture 2 at the S.SS-second mark."
5. Sound footer — overall_soundscape (1-4 sentences), non-diegetic
   music: N/A when none.

## Gates (raise KeyframePromptError BEFORE any config emits)

- (a) middle clause >= 2 ordered intermediate states and must NOT
  re-describe Picture 1 or the Picture 2 target pose (crossfade
  failure mode — restating frame content makes the model crossfade
  instead of animating). Detected by normalized-token overlap.
- (b) single `[Shot 1]` unless `multi_shot=True`; later shots need
  strictly increasing timestamps validated within the clip duration.
- (c) camera motion = natural sentence; stacked comma-tag strings
  rejected; defaults omitted.
- (d) overall_soundscape 1-4 sentences.

## R2I flow

```
ChainClip.end_pose present?
 ├─ no  → unchanged first-frame continuation path (I2VA)
 └─ yes → job 1: r2i_pose_target
          5-frame R2V (minimum video_length on the 17k+5 grid),
          standard plate refs (anchor + one per character),
          end_pose described in the prompt, model_type
          minimax_h3_fl2va_pruned
            │  render, then extract FINAL FRAME
            ▼
          job 2: fl2va_first_last  (needs = r2i job id)
          image_prompt_type "SE"  ← WanGP first+last mapping
          image_start = previous clip's last frame
          image_end   = extracted R2I final frame
          prompt      = built 4-beat FL2VA prompt
```

Both keyframes stay H3-native renders (more animatable than external
image edits — @yu_ichi_suzuki finding).

WanGP mapping note: there is NO `video_prompt_type "F+"` token in the
Wan2GP H3 handler. Verified against the checkout
(`models/minimax_h3/minimax_h3_handler.py`, `wgp.py`): first+last
mode is `image_prompt_type` containing `S` (start) + `E` (end) with
`image_start`/`image_end` inputs. The FL2VA job encodes exactly that.

## EndPoseDescriber

`signatures/director.py::EndPoseDescriber` (dspy.Signature):
beats + shot context in, strict-JSON `end_poses` out. PURE planning —
no GPU. Wired as an OPTIONAL post-pass
`ShortFilmPlanner.describe_end_poses(...)` (not part of `plan()`),
following the existing DSPY_LLM sentinel pattern (legacy callable or
ambient dspy LM; caller attaches poses to ChainClips).

## Manifest behavior

`emit_render_manifest` (services/chain/controller.py): a clip with
`end_pose` emits TWO jobs (r2i then fl2va, `fl2va.needs = r2i
job_id`); without `end_pose` the manifest is byte-for-byte the
previous path.
