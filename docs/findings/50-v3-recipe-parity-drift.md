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

## Follow-up — 2026-09-13, locally verified repair (now pushed for review)

The sections above preserve the original finding. Two corrections are now
supported by recovered-script and live-run evidence:

1. **Requested resolution is not output geometry.** The original request was
   `480x832`; WanGP produced `704x576` from the frame references. Setting the
   request to `704x576` would itself depart from the recovered recipe. The
   versioned recipe now keeps the request and measured output distinct.
2. **Dispatch and soundtrack replacement were the central architecture bug.**
   The generic settings carried a nonempty `script`, selecting WanGP's
   `[MULTISHOT]` shortcut and dropping image-start, reference and audio-guide
   conditioning. The adapter/runtime then replaced generated audio with the
   supplied guide. Correct guide transcripts were not evidence of conditioned
   generation or lip synchrony.

The local repair separates the native Ref2VA wire schema from job metadata,
rejects multishot dispatch fields, preserves native H3 audio/video bytes, gates
native output rather than a replacement soundtrack, and restores the recovered
prompt/reference/profile/seed/chain/concat path. Stills now report mouth
activity, not verified phonetic A/V synchrony. Machine completion is NEEDS
REVIEW, not an automatic operator KEEP.

The repo-generated run `v3-native-fixed-20260912` reproduced both native cuts,
the chain seed and assembled pair exactly. The assembled pair SHA256 is
`0146285a9ea6441b4688e1651a467c9af189e9b63e1403ffbf92938825294a51`.
The append-only verification record in that run's `runs.jsonl` has SHA256
`ca504d75066123185f97abdb883a92a9bb19a80b2897e944d7e9e9b64eb2f834`.
`predict/v3_canary.py` enforces the four original hashes plus frames, FPS and
zero audio/video start timestamps. Read-only re-verification on 2026-09-13
passed without a GPU rerender.

**Status:** exact original-pair reproduction and source-only validation are
verified. The repair is committed and pushed on
`codex/golden-v3-lf003-repro` at `43b04af680054c2d5a9ac6ddab2944bb9eefba9b`.
Review/merge, new-premise quality, fresh-clone GPU acceptance, and any model
chain-depth limit remain distinct and are not implied.

See `docs/V3-PARITY-FIX-2026-09-12.md` for implementation and evidence paths.
The subsequent source-only review passed both complete suites with 1,315
passed and 1 skipped after the separate #51 test-portability fix. See
`docs/V3-PARITY-RELEASE-READINESS-2026-09-13.md`; the branch is published for
review and has not been merged to `main`.
