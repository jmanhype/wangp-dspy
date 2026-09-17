# 75 — Remote VibeVoice contends with the GPU-resident judge

Status: IMPLEMENTED IN LOCAL CHANGESET; pending review and live validation.

## Failure boundary

The coordinator reported that the remote retry after #74 still failed before
generation: `llama-server` occupied 7816 of 24576 MiB while the VibeVoice model
requires approximately 16.7 GiB plus execution overhead. This report motivates
timesharing; the unit tests below do not reproduce or verify GPU memory usage.

## Change

Remote supply defaults to `VibeVoiceJudgeLease`, delegating acquire/release to
the existing `scripts.run_jobs.free_vram_for_render` and
`start_local_vision_judge` lifecycle. References and the manifest stage first;
acquire then immediately precedes remote module invocation. A `finally` block
restores the judge before artifact fetching, including when invocation raises,
returns failure, or acquisition partially fails. Acquire/release exceptions
and explicit False results fail closed: no successful local report or audio
publication. A restoration error supersedes an earlier exception while Python
retains its exception context. Remote failure artifacts may remain on the host.

The injectable `gpu_lease` implements `acquire(host)` and `release(host)`;
successful methods return None. CLI `--remote-gpu-lease judge` is the default.
Explicit `--remote-gpu-lease none` (`manage_gpu=False` in the remote API) is
reserved for an externally managed dedicated GPU. Local supply never invokes
the lease, including the local module invoked on the remote host. No QC gates,
model settings, or artifact provenance checks change.

This is the existing judge timeshare lifecycle, not an inter-process mutex or
a free-memory measurement. Concurrent GPU jobs still require external
serialization. Restoration starts the configured judge even if it was already
stopped before this invocation. It assumes the existing judge control script
manages the competing service; it cannot reclaim unrelated GPU processes.

## Verification

Model-free tests cover injected acquire/execute/release ordering, restoration
after nonzero execution and transport exceptions, rejection without invocation
after acquisition failure, no publication after release failure, the actual
repo lifecycle adapter's stop/sleep/execute/start ordering and control failures,
the explicit external-GPU CLI policy, and unaffected local supply.

No GPU model was loaded, and no remote host was contacted for this change.
Local validation: `.venv/bin/python -m pytest tests/test_vibevoice.py
tests/test_render_host.py -q` exited 0 with 54 passing cases;
`git diff --check` exited 0.
