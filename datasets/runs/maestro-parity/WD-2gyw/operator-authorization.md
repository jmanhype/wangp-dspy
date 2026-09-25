# WD-2gyw operator authorization

- 2026-09-25: "I agree" (batch 1 approval; 20,000,000,000-byte download ceiling).
- 2026-09-25: "kill whatever that is that was holding up the GPU and get back to work so that we can finish and complete this"
- 2026-09-25: "Unblock and cont"
- 2026-09-25: "Yes" to the dispatcher's explicit questions: (a) stop `llama-server` (leaving the operator's web-intel stack degraded) while video renders run; (b) run the feasible video subset rather than relocating more data for the full 119 GB.

Approved by: operator via /root parent authorization.
Scope: WD-2gyw host video evidence on render host 3090 (`straughter-Z690-Steel-Legend`, NVIDIA RTX 3090, measured 24,576 MiB total), using already-present assets first and additional model downloads only within the explicit ceilings below. Research/evaluation only; no training, GUI, publication, or protected-engine modification.
Download boundary: batch 1 20,000,000,000 bytes, plus the dispatcher-approved WD-2gyw feasible-subset ceiling of 60,000,000,000 bytes for this lane. Stop rather than lower the disk floor.
Failure boundary: record exact failures/OOM/refusals. Do not hide rows, restart llama-server, or start unrelated GPU work. Dispatcher will restore llama-server after the lane.
