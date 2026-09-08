# Finding #45 — cut 4 attribution remains systematic after reseeding

## Observation

The post-#44 acceptance drain exercised the new policy against the real
3090/local Qwen-VL judge. Cut 4 (the Soul's line, seeds `2304914099`,
`2304914100`, and `2304914101`) failed the explicit visual gate on all three
attempts. The queue dead-lettered it after the configured two retries and
left cuts 5–6 pending behind the failed prerequisite. The prior renders,
logs, and seed-specific failure records remain preserved.

Cuts 1–3 passed with their expected Pixar identity descriptions and both
Whisper gates. This isolates the remaining failure to the cut-4 visual
attribution/content seam rather than queue, render, mux, or QC transport.

## Interpretation

This is the systematic case anticipated by the reseed policy, not a retry
loop: changing the seed did not make the requested S2-only turn pass. Cut 4
chains from cut 3's final frame (S1 was the preceding speaker), so the
observed pattern is consistent with H3 anchoring mouth motion to the
last-frame speaker despite the silent-character instruction.

## Next PR (not applied here)

Harden the continuation prompt for a speaker switch: repeat the silent
character's name *and full identity description* in the closed-mouth
instruction, and add a regression fixture for a chained S1→S2 turn. Re-run
the six-cut acceptance only after that prompt change; do not waive the
vision gate or reopen this failed attempt silently.
