# WD-m0r5 blocked at the authorized download gate

The operator approved host batch 1 with the exact ceiling: report the
download-plan byte total and stop for operator approval above 20 GB.

Read-only inventory found the Qwen and FLUX handler code but no installed
Qwen-Image or FLUX image transformer weights. The four missing int8
transformers required by the four rows total **64,905,757,365 bytes**
(64,905,757,365 / 1,000,000,000 = 64.905757365 GB), above the 20 GB ceiling.
Their shared VAE/text-encoder dependencies are also absent, so this main-model
total is a lower bound for a fully runnable lane, not a complete install plan.

Therefore no model bytes were downloaded, no generation queue was admitted, and
no capability cell was changed to `host_run_verified` or
`unsupported_on_this_hardware`. This directory is a blocked diagnostic, not a
canonical Maestro evidence bundle; it intentionally has no `evidence.json`.

The sanctioned host preflight also failed on missing model files and remote disk
headroom (37G free, minimum 50G). Although that preflight printed
`gpu_state=idle`, a direct read-only `nvidia-smi --query-compute-apps` probe
still showed pid 1007225 using 7808 MiB; the CSV PID-comma format is not
recognized by the current preflight regex. The direct GPU observation is
retained and no host process was signaled or reconfigured.
