# WD-bw0h clean-machine retry5 — 2026-10-11

## Outcome

The one-shot v3 retry5 authorization was consumed and stopped fail-closed after a real H3
render completed. It is **not** a governed generated-artifact pass and must not promote the
first-run capability row.

- Wangp execution head: `02eb43a3084afdc86f78d7f4d0e3a81939ac61b0`
- Authorized source identity: `f356f1bfe54945e6ae9847643a1c808498816acf8c6e8aee43227955311994d6`
- Authorization canonical SHA-256: `558138882a66465d912e4a6fb000c74c37b3ffc931fb1ef0e94adaf04cc8e482`
- Fresh remote root: `/home/straughter/Wan2GP/wd-bw0h-clean-generated-retry5-20261009`

## What passed

- Clean disposable workspace and checkout at the authorized head.
- Exact four-model size/hash preflight with zero downloads.
- SSH, 86 GB disk headroom, idle-GPU, and QC health preflight.
- PyAV compatibility staging and the no-model media-write preflight.
- Exactly one durable H3 standard-create job.
- Native H3 completed all 20 denoising steps.
- Queue completed 1/1 and recorded QC verdict `KEEP`.
- A real non-black 480x832, 24 fps, 4.458333-second stereo MP4 was emitted and retrieved.

## Terminal boundary

The governed recorder's nonempty-byte threshold required at least 500,000 bytes. The real
output was 480,063 bytes, SHA-256
`0fd78acd6a728e65744537a98813b3427e1341d41a07330baa08f004bc7da406`.
Five of six objective gates passed; `h3_standard_create_nonempty_bytes` failed. The recorder
therefore stopped with `OBJECTIVE_GATE_FAILED`, did not write canonical `evidence.json`, and
recorded `generated_artifact=false`. A post-hoc canonical checker invocation also exited 1
because that required evidence manifest is absent.

The native render log also contains one `PYAV_COMPAT_FAILED: RuntimeError: compatibility
directory must lead PYTHONPATH` line even though the separate media-write preflight passed and
the render process environment showed the compatibility directory first in `PYTHONPATH`.
A post-run wrapper import probe also loaded the exact shim with `APPLIED=True`. That native
warning is preserved unedited and remains an investigation boundary; it is not claimed as an
owned warning.

No second render, threshold change, model download, package download, provider spend,
training, deletion, substitution, or capability promotion occurred.
