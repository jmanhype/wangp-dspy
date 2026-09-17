# 80 — Remote VibeVoice crashes discard host-environment diagnostics

Status: implemented on this branch.

## Failure boundary

The first strict-bar Rho redispatch selected WanGP’s Python environment instead of
the VibeVoice-compatible `/home/straughter/vb7-venv/bin/python`. That interpreter
exited before the remote supplier could write `report.json`:

```text
ValueError: Unrecognized processing class in
/home/straughter/models/VibeVoice-7B-hf
```

The local wrapper reported only `missing host artifact: .../report.json`. The
host returncode, stdout, stderr, and selected interpreter identity were absent
from durable evidence. Successful turn provenance recorded the requested Python
path, but not its resolved executable, implementation, version, or platform.

## Change

Remote supply now performs a fail-closed host-interpreter probe before staging a
generation command:

* requested executable, resolved executable, implementation, version, platform,
  and probe result are persisted to `<report>.host_environment.json`;
* successful and rejected turn provenance carries the same interpreter identity;
* successful and rejected localized reports reference the environment evidence;
* an existing host-environment evidence path blocks a reused report namespace;
* if generation exits before `report.json`, the missing-report error includes
  bounded host returncode/stdout/stderr and the environment record;
* no model is loaded and no output is published when the environment probe fails.

## Verification

Model-free tests cover successful environment localization, a pre-report host
crash retaining diagnostics, and a failed interpreter probe. Existing remote
supply/rejection tests are updated for the added probe call.
