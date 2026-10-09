# WD-mgcd media-write diagnostic

`pyav-probe.txt` preserves the coordinator's 2026-10-09 read-only host
diagnostic received as `/tmp/WD-mgcd-pyav-probe.txt`, byte for byte.
SHA-256: `ede7669366e852393373d801027e342dac0a3dcaa42bbad5083dc7a9281a6e8e`.
The coordinator reports execution in the authorized offline H3 runtime, with
no model loading, render, installation, or download. This worker did not contact
the host. These are observed dependency versions, not a compatibility fix.

The tiny torchvision write reproduces the integer-required PyAV failure in
`../clean-generated/failed-isolated-retry4-20261009/host-logs/render.log`.
The original retry4 evidence and its consumed authorization remain unchanged.
The new recorder rejects media-write failure before model checks or queue
admission; an incompatible runtime is not made compatible by this change.
Any future attempt needs a fresh source-bound authorization. The current
template still binds historical bytes and cannot authorize this new recorder.

Local tests use explicit dependency fixtures: they prove staging, offline
environment, subprocess execution, byte/hash checks and queue exclusion, not
a successful real-codec write on this machine.
