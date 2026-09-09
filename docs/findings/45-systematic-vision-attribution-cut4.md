# Finding #45 — cut 4 chain continuity remains systematic after reseeding

## Observation

The post-#44 acceptance drain exercised the new policy against the real
3090/local Qwen-VL judge. Cut 4 (the Soul's line, seeds `2304914099`,
`2304914100`, and `2304914101`) failed the explicit visual gate on all three
attempts. The queue dead-lettered it after the configured two retries and
left cuts 5–6 pending behind the failed prerequisite. The prior renders,
logs, and seed-specific failure records remain preserved.

Cuts 1–3 passed with their expected Pixar identity descriptions and both
Whisper gates. Frame inspection of cut 4 shows the Soul's mouth opening while
grandma stays closed, so the original wrong-mouth hypothesis is not supported.
The failure is the cut-4 chain continuity/content seam rather than queue,
render, mux, or QC transport.

## Interpretation

This is the systematic case anticipated by the reseed policy, not a retry
loop: changing the seed did not preserve the requested composition. Cut 4
chains from cut 3's final frame (grandma left, Soul right), but all three
renders re-stage the opening with Soul left and grandma right, with wardrobe,
hair, scale, and framing drift. The model is re-deriving the frame instead of
honoring the chained spatial layout. The generic gate message could not tell
this apart from attribution until finding #46 preserved component evidence.

## Next PR (not applied here)

Harden the continuation prompt for a speaker switch: repeat the spatial
anchor (grandma remains LEFT, Soul remains RIGHT, no re-staging) alongside
the silent character's name and full identity description, and add a
regression fixture for a chained S1→S2 turn. Neutral closed-mouth seeding is
also worth testing; latent protection remains future work. Re-run the
six-cut acceptance only after that prompt change; do not waive the vision
gate or reopen this failed attempt silently.
