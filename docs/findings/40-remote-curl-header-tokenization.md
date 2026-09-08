# Finding #40 — remote local-judge curl header was split by SshHost

**Status:** Confirmed and fixed by the first post-#39 remote smoke test,
2026-09-07.

The local Qwen adapter sent `-H` and `Content-Type: application/json` as two
argv entries.  `SshHost.run_probe()` forwards argv through OpenSSH's remote
command line; because that seam does not add shell quoting, the space in the
header value was re-tokenized remotely.  Curl then treated `application/json`
as a hostname (`Could not resolve host: application`) and never reached the
vision endpoint.  On-host `LocalHost` tests did not expose this namespace
difference.

## Minimal PR

Keep the header value in one token (`-HContent-Type:application/json`) and add
a host-seam regression assertion.  No change to containment or to the
fail-closed response parser is needed.
