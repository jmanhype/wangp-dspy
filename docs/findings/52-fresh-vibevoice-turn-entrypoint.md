# 52 — Fresh dialogue still lacks a reusable VibeVoice entrypoint

Status: IMPLEMENTED IN LOCAL FINDING-52 CHANGESET; pending review/merge.
This remains a VibeVoice supply-layer finding, not an H3 render regression.

## Observed during lf002-two-cut-20260913

The operator authorized a new two-cut Archive of Rain trial with fresh isolated
dialogue, the approved scene plate and the recovered v3 rendering recipe.
The inspection used the actual Hermes checkout at HEAD
the parity release candidate (`codex/golden-v3-lf003-repro`, now published)
plus its source repairs.
No generation or render command was executed on the GPU during this check.

Required new lines:
- Nell: This is the last rain we have.
- Orin: Then don't spill a single drop.

## Evidence and boundary

- scripts/run_acceptance.py consumes existing audio_paths; it does not synthesize them.
- scripts/run_film.py explicitly rejects missing supplied audio in continuation mode.
- predict/audio_prep.py provides prepare_v3_turn_audio, which prepares existing WAVs.
- docs/vibevoice-dialogue.md describes the VibeVoice model API, but is not an executable entrypoint.
- datasets/runs/provenance/v3_pair_generator.py contains generation logic, but executes
  hardcoded Devil's Grandma audio and direct wgp work at top level. Importing/running
  it for this test would bypass the repo executor and invoke unintended work.
- The inspected host /home/straughter/marathon/bin/build_turns.py writes a fixed
  dialogue table; it does not generate speech.
- /home/straughter/bin/studio-audio is reusable but exposes OmniVoice, VoxCPM2,
  Chatterbox and Qwen3-TTS, not VibeVoice. No alternate engine was substituted.
- SSH and nvidia-smi succeeded. GPU utilization was 0%, with 7,808 MiB occupied
  by llama-server. Availability of VibeVoice model loading has not been tested.

This is a bounded inspection of known repo/host entrypoints, not a claim that
no VibeVoice script exists anywhere on the machine.

## Resolution in the Finding-52 changeset

`predict.vibevoice` now provides a reusable VibeVoice turn-supplier module and
`python -m predict.vibevoice` CLI accepting a manifest of
speaker, text, explicitly selected voice-reference path, output path and seed.
Use the documented processor/model API, load once, and generate each speaker
turn separately. Keep imports side-effect-free. Fail on missing inputs,
generation errors or existing outputs unless explicitly resuming with matching
provenance. Preserve raw WAVs and model/voice/input hashes, effective settings
and generation logs. Transfer through the host asset seam; run repo audio
preparation and the Whisper pre-gate before publication. The implementation is
tested through injected backend/transcriber/ffmpeg seams; it did not load a
model, contact the 3090, submit a job, or queue a render.

Tests: two different speakers/texts map to two distinct generation calls and
output files; missing reference fails before GPU work; output/provenance mismatch
does not silently resume; no render is queued on audio generation/pre-gate failure.

The existing external-WAV supply contract remains valid: the operator/Hermes
may supply freshly generated VibeVoice turns instead of implementing this PR.

## Current result

Approved plate preserved. Two crop-style reference-image candidates generated
with the built-in image tool; these are not deterministic pixel crops and are
not separately operator-approved. Fresh WAVs remain absent. No bundle was
submitted, no video was queued, and no claim is made of a completed two-cut
trial. The repository now has the bounded supplier entrypoint needed to create
those WAVs when an operator explicitly authorizes a model-backed run.
