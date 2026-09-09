# Finding #50 — the production path did not reproduce the winning v3 pair

## Evidence

The operator's reference pair (`v3_pair`, 2026-09-06) is a 704x576, 24fps,
56-frame-per-cut render made with profile 2 and seed 904 for both cuts. Its
inputs are the 704x576 frame-grab references `grandma_frame2.png`,
`soul_frame.png`, and `grandma_frame.png`; cut 2 starts from cut 1's decoded
last frame. The winning prompt explicitly binds the silent character's
Picture-N face and uses the dungeon two-shot as the composition anchor.

The supposedly equivalent acceptance rerun emitted a materially different
configuration:

| Contract | v3 pair | acceptance rerun |
|---|---|---|
| output geometry | 704x576 | 480x832 |
| Wan2GP profile | 2 | 3 |
| seed policy | fixed 904 | hash-derived per line (`_seed_for`) |
| composition anchor | `grandma_frame2.png` frame-grab | generic `plate.png` master |
| identity refs | full 704x576 frame refs | tight `face_*.png` crops |

The source of each divergence is in-repo, not inferred: `h3_recipe.py` pins
`WIDTH, HEIGHT = 480, 832` and `PROFILE = 3`; `wangp_adapter.py` invokes
`--profile 3`; and `chain/controller.py` assigns `seed=_seed_for(...)`, which
produced `348474354`, `162456454`, `1050738740`, and other non-904 seeds in the
rerun. The committed `staging_r2.json` names `plate.png` and tight face crops,
not the winning frame-grab assets.

The resulting film visibly re-stages the dungeon into a generic room and
drifts the character appearance. The per-cut vision gate still passed several
clips because it checked activity/identity inside each clip; it did not assert
golden-v3 geometry, anchor identity, or cross-cut visual parity.

## Interpretation

This is recipe/configuration drift, not a WanGP randomness explanation and not
the cut-6 latent ceiling. The acceptance path proved that its own gates and
queue work, but it did **not** prove the operator-validated v3 recipe. The
claim that the production path encoded that recipe was false.

## Minimal PR (not applied here)

Add a committed golden-v3 recipe fixture and a parity test that checks the
emitted settings before any GPU work: 704x576, profile 2, fixed seed 904,
frame-grab anchor/ref paths, exact two-ref ordering, and the v3 speaker
prompt. Make the acceptance bundle select that fixture explicitly; keep
hash-derived seeds and generic geometry as a separate, named recipe rather
than silently substituting them.
