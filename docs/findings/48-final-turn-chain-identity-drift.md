# Finding #48 — final speaker switch still re-stages the chained identity

## Observation

The post-#47 acceptance rerun used the spatial-anchor wording in the chain,
H3 recipe, and vision judge. Cuts 1–3 passed on their first seeds. Cut 4
failed once and passed on seed `2304914100` after the configured reseed. Cut 5
passed on its first seed. The final Soul turn (cut 6, “More, please.”) failed
the visual gate on all three attempts (`368361140`, `368361141`, and
`368361142`) and was dead-lettered; no assembly was emitted.

Each rejection has durable component evidence:

```json
{"mouth_sync": 0.0, "action_match": 0.0, "speaker_attribution": 0.0}
```

Frame inspection of the three artifacts shows the same broader continuity
problem rather than a simple mouth attribution miss. The chain input has the
Pixar soul on the RIGHT with a flaming, close-cropped head. The outputs
re-stage the scene on each seed: framing and scale change, the soul's hair and
fire treatment change (including a brown-haired non-burning variant), and the
opening composition is not a faithful continuation. Grandma remains present,
but the identity/wardrobe reference is not held.

## Interpretation

The #47 spatial-anchor text improves the cut-4 switch (one retry now holds the
left/right layout), but it does not make continuation identity deterministic
for the final Soul turn. This is a model/conditioning seam, not a queue,
transport, mux, or judge-response problem. The fail-closed behavior is
correct: the run stops at cut 6 and does not claim an assembled film.

## Next PR (not applied here)

Evaluate a stronger continuation strategy for late speaker switches: include
an explicit first-frame identity checklist (hair/fire/wardrobe/scale) and a
neutral closed-mouth tail in the seed, compare against a latent-protect or
first-frame-preservation path, and keep the vision gate blocking. The three
failed artifacts and their raw judge responses are the regression fixture;
the acceptance rerun must not waive them.
