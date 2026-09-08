# Finding #37 — live ModelScope judge can hang during request upload

**Status:** Confirmed by the mapped acceptance rerun, 2026-09-07.

After the asset map was supplied, cut 1 rendered on the 3090 and reached the
blocking vision gate. The production `ModelScopeVisionJudge` then remained in
`requests`/OpenSSL `SSLSocket.sendall()` while uploading the three-frame
request; it produced no response for more than six minutes despite the
configured 180-second request timeout. The operator had to interrupt the
runner. The queue consequently remained in `qc` for cut 1 with five dependent
jobs pending. No visual score was recorded and the film did not proceed.

## Minimal PR

Put a hard, observable deadline around the ModelScope call (including request
body upload), surface a typed timeout/network failure, and let the executor's
terminal-failure bookkeeping record it without leaving a job in `qc`. Add a
transport regression using a session whose send blocks beyond the deadline.
Keep the blocking vision gate fail-closed; never substitute scores or bypass
the judge on timeout.
