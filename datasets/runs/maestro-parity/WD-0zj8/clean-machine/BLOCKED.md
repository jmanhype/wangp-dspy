# Generated-artifact half remains blocked

The clean-machine run in this directory emitted a deterministic LF004 plan and then
refused generation before SSH, model download, queue admission, inference, or GPU work.
It is not generation evidence and `host_run_verified` is false.

Required operator inputs still absent:

- per-batch GPU/render-host authorization, including scope, timestamp, approver, exact command boundary, and host identity;
- model-download approval;
- a complete authorized host/model manifest with every model identity, source, hash or immutable version, license, and usage constraint.

Missing input is a blocked condition, not infeasibility and not permission to fake a
fallback artifact. Do not invoke the WD-651z success checker as a generation claim.
