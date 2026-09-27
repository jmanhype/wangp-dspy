# WD-ycjg operator authorization and dispatcher decision

Verbatim operator input:

> you decide

Decision:

- Selected batch: `SCAIL-2`
- Decided by: `/root` dispatcher
- Decision time: `2026-09-27T04:20:00Z`
- Rationale: SCAIL-2 has a complete declared dependency set of `26,009,968,164` bytes, the host has `64,910,606,336` bytes free, and the GPU is idle with `23,834 MiB` free. This leaves roughly `38.9 GB` disk headroom and avoids starting with the larger LTX-2.3 or Wan/2GP batches.

Exact authorized scope:

- Download the sixteen declared SCAIL-2 model/helper files into `/home/straughter/Wan2GP/ckpts/` (the final five are the XLM-R CLIP model/tokenizer files exposed by the first model-load attempt).
- After the live Wan2GP venv exposed missing SAM3 imports, use three additional story-local Python dependencies only under `/home/straughter/wd-ycjg-run/python-deps/`: `iopath` source 42,226 bytes, `portalocker` wheel 129,647 bytes, and `pycocotools` wheel 493,172 bytes. Total authorized bytes across all nineteen files are 28,418,905,124. This changes no system, venv, repository, or model dependency.
- Verify every file by exact byte size and SHA-256 before admission.
- Use only the preexisting local HOL120 person-bearing control video as visual source/reference.
- Run the seven still-planned SCAIL-2 cells: create, extend, blend, retake, edit, repaint, and recast.
- Preserve the existing typed SCAIL outpaint and upscale boundaries.
- Use an isolated Wan2GP worktree; do not mutate its live dirty tree.
- Stop on undeclared network need, hash mismatch, insufficient disk/GPU, source mismatch, or media-gate failure.

Out of scope:

- LTX-2.3 and Wan/2GP downloads.
- LTX-2.5 specialized LoRA downloads.
- Any live dependency/provider mutation, training, publication, threshold change, protected-engine change, or unrelated process action.
