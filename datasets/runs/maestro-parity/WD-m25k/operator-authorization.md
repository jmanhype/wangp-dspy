# WD-m25k operator authorization and execution boundary

Verbatim dispatcher instruction:

> Continue the remaining 56 video cells, prioritizing no-download LTX-2.5 after the tokenizer fix.

Recorded interpretation:

- Approved by: `operator via /root dispatcher`
- Authorization observed: `2026-09-27T01:22:06Z`
- Host: SSH alias `3090`, host `straughter-Z690-Steel-Legend`, NVIDIA RTX 3090 24 GiB
- Exact target rows: `minimax_h3/kfi_frames_injection` and `minimax_h3/h3_audio_refinement`
- Exact target operations: the sixteen still-planned cells in `docs/video-capabilities.md`
- Download boundary: `downloads=false`; use only preexisting hash-matched H3 and helper assets
- Source boundary: use an isolated Wan2GP worktree; do not mutate the live dirty tree
- Service boundary: stop on hash, disk, GPU, source, or media-gate failure; touch no unrelated process
- Output boundary: real generated output where the native control is admitted, or an exact typed host/dependency boundary

LTX-2.5 priority is already satisfied by accepted `WD-m7xw`: four operations have real outputs and four missing-LoRA operations have exact dependency boundaries. This story therefore continues with the next zero-download H3 batch.
