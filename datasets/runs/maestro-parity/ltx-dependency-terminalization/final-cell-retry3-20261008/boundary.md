# WD-28ac final-cell retry3 — 2026-10-08

## Outcome

The operator-approved retry3 native batch ran once in a fresh namespace and queue database with one attempt per operation.

- All seven named native operations rendered and are preserved as `rendered_pending_qc`.
- The previously missing 654,465,286-byte spatial-upscaler LoRA was downloaded once and hash-verified.
- The existing 7,605,507,256-byte distilled LoRA and the downloaded spatial upscaler were exposed through zero-copy source links.
- The queue contains seven jobs, all `rendered_pending_qc`, with zero failures.
- The seven retrieved native outputs and seven settings files were independently size- and SHA-256-verified against their operation records.
- No retry, substitution, package install, deletion, provider spend, training, threshold change, or protected-engine change occurred.

## Boundary

This is native completion evidence only. It does **not** claim QC review, matrix promotion, or story acceptance. The final `ltx/2.3 upscale` disposition must wait for the governed evidence review and matrix transition.

## Authorization disposition

The retry3 authorization is consumed. Its canonical SHA-256 and no-retry disposition are recorded in `authorization-consumption.json`.

The canonical digest is reproducible from `authorization.canonical.json`: encode the authorization as UTF-8 JSON with recursively sorted keys, compact separators, ASCII escaping enabled, and no trailing newline, then take its SHA-256.
