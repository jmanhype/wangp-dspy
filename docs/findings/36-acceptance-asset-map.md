# Finding #36 — acceptance bundle has no configured host asset map

**Status:** Confirmed and resolved for the acceptance host by the
config-driven `WANGP_ASSET_MAP`/`WANGP_SANCTIONED_DIRS` environment (2026-09-07).

With the registered `dg-acceptance` premise and live judge credential supplied,
the runner planned and submitted the six jobs, but the first Ref2VA job failed
before any WanGP write or GPU render. `WanGPAdapter.render_for_job()` handed the
local audio path (`assets/acceptance/turn1.wav`) to the strict runtime while
`SshHost` had no `asset_map`; the containment gate therefore rejected it as
outside the sanctioned roots. Supplying the approved environment map made the
host asset contract resolve correctly; cut 1 then rendered and reached QC. The
runner still intentionally requires this operator-supplied mapping rather than
guessing host paths.

## Minimal PR

Keep the acceptance host contract explicit at runner setup: supply a
config-driven local-prefix → host-prefix asset map (including the six WAVs and
the anchor/identity plate aliases), and retain the regression asserting mapped
audio/image paths are sanctioned before `render_for_job()` is called. Do not
broaden containment or fall back to the local path.
