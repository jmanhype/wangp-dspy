# WD-osfm operator authorization and dispatcher decision

Verbatim operator input:

> you decide

Decision:

- Selected batch: `LTX-2.3`
- Decided by: `/root` dispatcher
- Decision time: `2026-09-27T16:19:00Z`
- Rationale: after accepted SCAIL-2 and Wan batches, LTX-2.3 is the only remaining planned video row. The selected native WanGP Q4_K_M Light checkpoint and required helpers total `35,379,235,525` bytes. The old Comfy FP8 checkpoint does not match WanGP packaging and is not used.

Storage authorization:

- The 3090 currently has `21,203,777,584` bytes free.
- A superseded, unused full-int8 H3 checkpoint occupies `34,038,903,007` bytes at `/home/straughter/Wan2GP/ckpts/MiniMax-H3-FL2VA_int8_convrot.safetensors`.
- Its SHA-256 is `83a36b67776962f44087f2f7c12d95791393f3cce1ef898efc90405216e7b0c0`.
- Move that exact file to `/Users/Shared/HermesWorkspace/model-offload/wangp-3090/MiniMax-H3-FL2VA_int8_convrot.safetensors`.
- The destination has at least `100 GiB` free.
- Verify both size and hash on both systems before unlinking the remote source.
- Preserve every other checkpoint, including the active rank8 H3 model.

Exact scope:

- Download only the eighteen declared LTX-2.3/Gemma/helper files.
- Link, but do not download, the already-present hash-identical temporal upscaler.
- Own all nine LTX-2.3 cells.
- Use the accepted local WD-ycjg create output as the control/reference asset.
- Use an isolated Wan2GP worktree and mutate no live dependency or source file.
- Stop on undeclared network need, storage mismatch, insufficient disk/GPU, source mismatch, or media-gate failure.

Out of scope:

- LTX-2.5 specialized LoRA downloads.
- Any live dependency/provider mutation, training, publication, threshold change, protected-engine change, unrelated process action, or deletion of an unverified artifact.
