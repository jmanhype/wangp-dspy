# WD-qthq authorized editor host execution

- Operator authorization verbatim: `Authorize` at `2026-09-29T23:17:30Z`.
- Authorized scope: host `3090`, exactly two declared hash-bound LF002 sources, one `kind=editor_export` queue job, CPU-only FFmpeg, `gpu_work=false`, and zero model downloads.
- Operating commit: `4f854dd1b938f145dcbd5eef907f6348ee12657a` on `story/WD-qthq`.
- Exact FFmpeg transport command: `ssh -o BatchMode=yes -o ConnectTimeout=15 3090 /bin/sh /tmp/wd-qthq-editor-export-20260929T195201Z-3c1a4bfd-ffmpeg.sh`.
- Host/workspace: `straughter-Z690-Steel-Legend` as `straughter`; `/home/straughter/Wan2GP/wd-qthq-editor-export/20260929T195201Z/cc0280f0`.
- Queue: `job-1790730445881-aa610b52`, `attempt-1`, final state `done`.
- Output: `outputs/editor-export.mp4`, 515764 bytes, SHA-256 `4f7c955ebbf68daa98eed4c117cb879db8dfc6744924d6f1e7ad1e1de8c8725e`.
- Objective gates: 8/8 pass in `objective-gates.json`; canonical checker passed with zero owned warnings.
- Visual proof: `review/order-contact-sheet.png` compares output/source for the first ordered half and output/declared clone frame for the second ordered half.
- Boundary history: two earlier wrapper attempts consumed no operation. The successful operation's preflight completed once; two post-preflight interruptions were local wrapper defects only (`ValueError` tuple unpack and malformed local `scp -o` argv) and did not retry host preflight, transfer a source, or admit a second queue job. Their exact artifacts are under `../boundary-attempts/`.
- Evidence note: the queue clip's symbolic log label is `ffmpeg.native.log`; the authoritative captured native log is `execute-ffmpeg.log`.
