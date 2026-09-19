# 84 — LF003 cut 3 fails the three-frame mouth-box gate

Status: current-gate failure confirmed; no latent-carry implementation.

## Boundary

WD-rij6 executed a fresh, clean-checkout, no-`completed_prefix`, one-queue,
one-ledger LF003 four-cut probe at repository commit
`35201a11bb1839fd5ba83739eed690227aabe199`. Cuts 1 and 2 completed all gates.
Cut 3 rendered from the decoded final frame of cut 2 and passed both Whisper
gates, but the repository vision judge returned a result without the required
three `speaker_mouth_bboxes`. The queue therefore rejected cut 3 before
identity acceptance, mouth-box consensus, and SyncNet. Cut 4 remained pending
on its chain dependency and was not rendered; no assembly was created.

This finding is limited to the exact current-stack artifacts below. It does
**not** establish that latent carry is required, and it does not reinterpret
the older pre-correction depth-five runs.

## Exact evidence

- Run: `lf003-four-cut-fullgate-20260919`
- Failed job: `job-1789824118538-02ca412d`
- Queue state after fail-closed stop: cut 1 `done`, cut 2 `done`, cut 3
  `failed`, cut 4 `pending`.
- Terminal failure class/detail:
  `qc_gate` / `vision result must include three speaker_mouth_bboxes [x,y,w,h]`
- Cut 3 Whisper: pre `1.000`, post `1.000`
  (`datasets/runs/pull/acceptance/worker-e59bab85fab5/render-0002/qc-evidence.json`)
- Cut 3 rendered video SHA-256:
  `08acf7d3601b3489e15ddf76e6f50d741a9d6550b04cc784f29cb952fbe9b47d`
- Cut 3 chain input (`chain/clip0003/chain_last_frame.png`) SHA-256:
  `045a28a664b718c4edc1833a68b32882073f7afdddf4b5367c375b9e5e7fd72a`
- Cut 3 audio guide SHA-256:
  `f660d9564d073056110f1bc210c79c6ed83c4773c6e02743e688c11607cecfe7`
- Queue SHA-256:
  `3f0aa16b384f6c3e0f043d3d9bbc451f34b0af22853a1eece341d4aae5112e0b`
- Ledger SHA-256:
  `04f8ff1568d10e50cdd02a27c5cfe294605448805e49feca79de19990d651b38`

The cut 3 contact sheet appears near-static. Decoded frame PSNR supports that
observation (frame 0 vs 28: `36.526770 dB`; frame 0 vs 55: `38.853586 dB`;
frame 28 vs 55: `36.849490 dB`), but pixel similarity is diagnostic evidence,
not a replacement for the failed mouth-box gate.

## Disposition

- Preserve all three cut bundles, both chain frames, the failed queue, the
  append-only ledger, VibeVoice supply provenance, review probes/contact
  sheets, and the pre-execution clean identity.
- Do not retry cut 3 in this story after the required cut-3 continuity gate
  fails.
- Do not render cut 4 or assemble a partial film.
- Do not weaken the vision, mouth-box, Whisper, or SyncNet thresholds.
- Do not implement latent save/load or first-frame preservation in this story.
