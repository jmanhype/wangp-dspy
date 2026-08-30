# SPEC (DRAFT) — S3: Audio manifest + QC integration slice (definition only)

Story: WD-a1d9-followup · Author: sol-max · Date: 2026-08-30
Status: DRAFT — awaiting operator approval before dispatch.

## Goal

Consume the S2 audio data plane end-to-end at the manifest and QC
layers: audio-bearing jobs become a typed job PACKAGE, and QC reads
the rendered artifact + audio policy to produce judged Ref2VAAudioQC
fields.

## Proposed scope

1. NEW `predict/audio_manifest.py` — serialize the Ref2VA settings
   doc `extra` audio payloads (audio_guide, audio_provenance,
   audio_policy, audio_qc) into a sidecar `audio_manifest.json`
   written next to the render output; readback validator confirms
   round-trip. Per Qwen ruling: any manifest hashing MUST exclude
   `extra` keys (or hash only the sanctioned audio payload block).
2. EXTEND remux policy EXECUTION (deferred from S2): a pure-python
   policy planner that, given AudioPolicy + keeper window, emits the
   ffmpeg remux command (discard rendered audio, remux from
   source_master/vocal_stem window) — command GENERATION only,
   executed by the existing render driver, containment-checked per
   GLM note N1 (paths never reach shell; argv list form only).
3. QC integration: `qc/` gains a Ref2VA audio QC stage that fills
   Ref2VAAudioQC.mouth_sync / audio_fidelity / visual_motion_match /
   audio_artifacts from (a) schema-only path: judge placeholders with
   critic_model='Qwen2-Audio-7B' fields present but None until a
   judge runs, and (b) G3/G4 enforcement: QC refuses any artifact
   whose audio did not pass through the discard/remux policy.
4. Run-record wiring: s4 run records gain `audio_manifest` hash.

## Non-goals

- Running Qwen2-Audio-7B (no GPU budget; 4.4 GiB free).
- Speaker gate / diarization (separate lane).
- Any change to the H3 GEPA A/B harness (snapshot + grep gates from
  S2 stay in force).

## Open question for operator

Should the manifest be a REQUIRED sidecar for every Ref2VA render
(hard gate at readback) or advisory until the remux slice lands?

**RESOLVED (2026-08-30, operator dispatch): REQUIRED.** audio-bearing
Ref2VA jobs must ship `audio_manifest.json`; readback of a render
without it is a typed `AudioManifestError`, and QC refuses such
artifacts (G3/G4). Legacy non-audio H3 is unaffected — only the
Ref2VA lane consults the manifest.
