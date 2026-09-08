# Finding #38 — premise identity did not bind the registered visual style

**Status:** Implemented with the Pixar acceptance bundle update, 2026-09-07.

The premise/media coherence guard verified character names, speakers, and
plate paths, but it had no invariant tying the anchor plate to the operator's
locked visual style. A correctly named replacement plate could therefore pass
metadata checks while changing the film's look.

## Closing PR

Premises may register a `style_ref` SHA-256 for the master anchor. Production
media manifests must carry the same ref, and `DirectorRun.plan()` hashes the
actual anchor bytes before planning or queue submission. A missing, mismatched,
or unreadable style anchor fails closed. The DG acceptance index and bundle now
bind the Pixar master plate hash; legacy premises without a style ref remain
temporarily compatible until upgraded.
