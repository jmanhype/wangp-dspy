# Finding #35 — acceptance bundle has no resolvable DG premise roster

**Status:** Confirmed and resolved on the data side in `490066c` (2026-09-07);
the next run now reaches the fail-closed ModelScope credential gate.

`assets/acceptance/staging_r2.json` declares `media_manifest.premise_id` as
`dg-acceptance`. Before `490066c`, that ID was absent from the Lost Futures
index and the bundle carried no embedded roster, so the repo-owned runner
refused before queue creation. The premise is now registered in
`datasets/lost-futures/index.json` with stable character descriptions; the
runner resolves the roster and stops next at the missing live judge credential
instead of queueing ungated work.

## Minimal PR

Keep the registered roster and ensure the media manifest plate keys and
per-turn audio speakers resolve to it. With a ModelScope credential present in
the execution environment, the runner can plan and submit without out-of-band
creative data.
