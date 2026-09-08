# Finding #37 — live ModelScope judge can hang during request upload

**Status:** Confirmed and fixed with a bounded transport seam, 2026-09-07.

After the asset map was supplied, cut 1 rendered on the 3090 and reached the
blocking vision gate. The production `ModelScopeVisionJudge` then remained in
`requests`/OpenSSL `SSLSocket.sendall()` while uploading the three-frame
request; it produced no response for more than six minutes despite the
configured 180-second request timeout. The operator had to interrupt the
runner. The queue consequently remained in `qc` for cut 1 with five dependent
jobs pending. No visual score was recorded and the film did not proceed.

## Closing PR (implemented)

`ModelScopeVisionJudge` now wraps the synchronous request in an OS-level
wall-clock deadline (including TLS body upload), while retaining bounded
connect/read timeouts. A blocked transport raises a typed vision error instead
of hanging the drain; the existing executor failure boundary records it and
the blocking vision gate remains fail-closed. A regression session that blocks
the upload path proves the deadline without contacting the service.
