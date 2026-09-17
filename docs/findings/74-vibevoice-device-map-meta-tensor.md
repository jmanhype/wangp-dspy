# 74 — VibeVoice automatic placement exposes a meta device

Status: IMPLEMENTED IN LOCAL CHANGESET; pending review and live validation.

## Failure boundary

The coordinator reported that the repo-only remote audio run at main `e103311`
failed before `model.generate`: automatic placement exposed `model.device` as
`meta`, and transferring processor inputs there raised `Cannot copy out of meta
tensor`. A first parameter is not a reliable execution-device selector for an
Accelerate-dispatched model.

## Change

Resolve the input execution device from `hf_device_map` first, then from model
parameter devices. Skip meta, CPU, disk and invalid/unindexed placements; accept
explicit accelerator placements (including integer CUDA map ordinals). Never
guess a CUDA index or use `model.device` as fallback. If no concrete accelerator
placement exists, raise `VibeVoiceError` before processor input transfer or
generation. Placement metadata is not a hardware-availability check: an invalid
runtime placement still fails through the existing typed generation error.

The role `0` audio/text chat template, plain voice-reference path, dtype, seed,
and exactly one `model.generate` call per turn remain unchanged. No changes to
Whisper gates, remote dispatch, provenance, model loading or model weights.

## Verification scope

Model-free tests cover a meta-first map with concrete CUDA string/integer
placement, fallback past meta parameters, all-meta rejection, CPU/disk-only
rejection, absent placement and malformed placement. Rejections make no seed,
processor, generation or save calls and create no output file. These tests do
not establish successful GPU inference or audio quality; no GPU/remote execution
was performed for this change.

Local validation: `.venv/bin/python -m pytest tests/test_vibevoice.py
tests/test_render_host.py -q` exited 0 with 45 passing test cases.
`git diff --check` exited 0.
