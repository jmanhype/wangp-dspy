# Finding #47 — continuation prompts did not name the spatial anchor

## Evidence

Offline re-judging cut 4 renders `render-0017`, `render-0018`, and
`render-0019` returned the same explicit score object each time:

```json
{"mouth_sync": 0.0, "action_match": 0.0, "speaker_attribution": 0.0}
```

Frame inspection showed the Soul's mouth moving while grandma stayed closed,
but the chained composition was re-staged on every seed: the characters
swapped sides and their wardrobe/hair/framing drifted from cut 3. The judge
was therefore rejecting a broader identity/continuity failure, not observing
grandma carrying the Soul's line. The raw response and scores are now
persisted on the dead-lettered queue clip for offline replay.

## Fix (landed)

The chain controller now emits an explicit spatial anchor. For the registered
Devil's Grandma roster it states that the grandmother remains on the LEFT and
the soul on the RIGHT, exactly as in `<Picture 1>`, preserving scale,
wardrobe, and framing with no side swap or re-staging. Generic rosters get the
same invariant using their first two ordered subjects. The H3 recipe prompt
and the vision-judge prompt carry corresponding no-swap/no-restage language.

## Next verification

Reopen only after a fresh chain render with the anchored prompt. A rerun must
show the same spatial layout at the first generated frame and preserve the
full identity descriptions; the vision gate remains blocking.
