# WD-m7xw operator authorization and bounded preflight record

Verbatim operator input supplied by the `/root` dispatcher:

- `Authorized and approved.`
- `continue`
- `Continue the remaining 56 video cells, prioritizing no-download LTX-2.5 after the tokenizer fix.`

Recorded approval:

- Approved by: `operator via /root dispatcher`
- Authorization timestamp: `2026-09-26T20:33:00Z`
- Host: SSH alias `3090`, host `straughter-Z690-Steel-Legend`, NVIDIA RTX 3090 24 GiB
- Exact operations: `create`, `extend`, `retake`, `edit`, `outpaint`, `repaint`, `recast`, and `upscale`
- Execution boundary: synchronous, bounded, serial commands with local and remote timeouts
- Download boundary: `downloads=false`; use only the fifteen hash-matched present LTX-2.5 assets
- GPU/service boundary: stop on hash, disk, GPU, QC, or tokenizer failure; do not kill or restart unrelated services
- Source boundary: deploy Wan2GP `story/WD-i7qs` at `faea82d15bf10b3479c42c0ea430892aae975870` only in an isolated run tree

Preflight result:

- All fifteen required LTX-2.5 asset hashes matched: `host-logs/10_asset_hash_preflight.txt`.
- The isolated source tree was created at the required Wan2GP commit with only the expected untracked `ckpts` symlink: `host-logs/23_deploy_state.txt` and `host-logs/40_postflight_no_inference.txt`.
- The required real-path tokenizer check passed with vocabulary `262144` and video token id `258884`: `host-logs/22_tokenizer_check.txt`.
- GPU admission then failed closed: unrelated `llama-server` PID `3213164` occupied `18154 MiB`, leaving only `5873 MiB` free. The authorization explicitly forbids killing or restarting that service: `host-logs/30_gpu_preflight_blocked.txt`.
- No queue job was admitted, no inference command ran, and zero output files existed: `host-logs/40_postflight_no_inference.txt`.
- No model, dependency, or other HTTP download was requested. The isolated git worktree was created from already-present local Wan2GP objects. SSH carried only scripts, text state, and logs.
- The live Wan2GP tree remained at HEAD `4c93b64a47b5b0a915f2abec2ce754be98227150`, with the same 109-file dirty identity before and after preflight.

## Resumed operator authorization

Verbatim operator input relayed by the `/root` dispatcher:

- `kill whatever that is that was holding up the GPU and get back to work`
- `Unblock`
- `now requested prioritizing LTX-2.5`

Recorded resumed approval:

- Approved by: `operator via /root dispatcher`
- Authorization observed by: `2026-09-26T21:36:04Z` (first resumed host inspection)
- Host: SSH alias `3090`, host `straughter-Z690-Steel-Legend`, NVIDIA RTX 3090 24 GiB
- Exact native operations: `create`, `extend`, `retake`, `edit`, `outpaint`, `repaint`, `recast`, and `upscale`, once each, serially
- Execution boundary: synchronous local timeout 1900 seconds and native timeout 1800 seconds per operation
- Download boundary: `downloads=false`; `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` enforce use of the fifteen hash-matched assets
- GPU/service boundary: stop only re-verified llama-server PID `3213164` if still present; touch no other process and leave llama-server stopped
- Source boundary: Wan2GP isolated tree only at `faea82d15bf10b3479c42c0ea430892aae975870`

Resumed holder action:

- At `2026-09-26T21:42:08Z`, PID `3213164` was already absent and no compute application held the GPU. The GPU reported 84 MiB used and 24032 MiB free.
- No process was killed or restarted. The final postflight again reports PID `3213164` absent and 84 MiB used.
