# Finding #36 — acceptance bundle has no configured host asset map

**Status:** Confirmed by the repo-owned acceptance rerun, 2026-09-07.

With the registered `dg-acceptance` premise and live judge credential supplied,
the runner planned and submitted the six jobs, but the first Ref2VA job failed
before any WanGP write or GPU render. `WanGPAdapter.render_for_job()` handed the
local audio path (`assets/acceptance/turn1.wav`) to the strict runtime while
`SshHost` had no `asset_map`; the containment gate therefore rejected it as
outside the sanctioned roots. The host-side acceptance assets exist, but the
default acceptance runner does not derive or configure their mapping.

## Minimal PR

Make the acceptance host contract explicit at runner setup: accept a
config-driven local-prefix → host-prefix asset map (including the six WAVs and
the anchor/identity plate aliases), pass it into `SshHost`, and add an
integration regression that asserts the mapped audio/image paths are sanctioned
before `render_for_job()` is called. Do not broaden containment or fall back to
the local path.
