# LF004 operator dogfood review packet
**Status:** `operator_review_pending` / `no_render_started`; no GPU, model, SSH, queue, host, render, approval, or jobs-database work. Repository `story/WD-z46c` at `efcba335c634c09af61f6a47423783cab4ef97ba`.

**Plan:** 4 clips at the pinned Wan2GP MiniMax H3 Ref2VA minimum of 107 frames each, `dry_run=true`, `gpu_work=false`, `queue_submitted=false`, duration `17.832s`.
## Identities

- Typed brief: `sha256:4d8a0597ea40783f5928ed534fa002ca139595b321204f0d34be05f4ee5a9a59`; file `4cd4d8250b64d09ae9cd58a7db20cb94dbbf664eb78736e87f6d2973de4137b1`.
- Canonical plan: `70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86`.
- Initial raw plan (packet generation): `eed857ee3af097cf7f816b32dd4fa1de532e9bfcc343fc7bfe141f6db1da9d04`.
- Initial run ledger (packet generation): `d1aac53d2ea0a186c69f2414c7f0385a12874112bb88536a7a47b3a8ce3f7fc1`.
- Script: `a05929f7bd94df69fe09e2a856724b40135ca6d750545f6a4ef7b42144ef8c00`.

The canonical plan hash is SHA-256 over the sorted, compact JSON plan with location-dependent `input` and dirty-tree `repository` objects removed. Absolute paths beneath either the recording worktree root or the verifying checkout root are structurally normalized to repository-relative values. Two clean out-of-repository replays and one differently located detached checkout produced the same canonical identity. Initial raw plan/ledger hashes above are generation-time records; an exact in-place replay may change them through repository-dirty self-reference and is not a stable identity check.
## Inputs

- `anchor.png` ← `assets/acceptance/lf003-v3/anchor.png`: `c87547fe9ac64f3e84b0f09d8b1d0aa716ba3a0c0e486260eff2e8f0c831e210`.
- `Tess.png` ← `assets/acceptance/lf003-v3/face_tess.png`: `5fe5fac33312fa9675930c3a07d22f76c0838bb48e0b3c93e22e0fc2ac484ef6`.
- `Rho.png` ← `assets/acceptance/lf003-v3/face_rho.png`: `87e24404c5fa0359aa3d1fd56147cc7ee0ee99fd5e5a19a6c1926848fa2415a0`.
- Tess, “Tomorrow's sunrise is only a projection.” ← `lf003-vibevoice-audition-20260917/audio/tess.prepared.wav`: `8ed7970078130c8a64036ad7bbd52c10b36cbbe32b6eb678a1b4856cc8501b3f`.
- Rho, “Then give me a real horizon.” ← `lf003-vibevoice-rho-strong-20260918/audio/rho.prepared.wav`: `d7607d276a371132c148cb39552796db27325e4b2f022d9ee3ba02bb295a5322`.
- Tess, “The projector died at midnight.” ← `lf003-four-cut-fullgate-20260919/audio/tess-cut3.prepared.wav`: `f660d9564d073056110f1bc210c79c6ed83c4773c6e02743e688c11607cecfe7`.
- Rho, “Then we will watch the stars.” ← `lf003-four-cut-fullgate-20260919/audio/rho-cut4.prepared.wav`: `c001101d6dfc49cd3b59b358192bcc37ed93c4084ccb89e52306488afb1794c2`.

Each dialogue string exactly equals the selected VibeVoice provenance `text` and matching accepted report entry; all four report entries are `complete`, their prepared hashes match the WAVs, and all Whisper gates passed. The audio-guide table also retains the observed Whisper transcript for auditability.
## Verification record

```sh
# Results: 1) 11 passed; 2) brief=sha256:4d8a0597ea40783f5928ed534fa002ca139595b321204f0d34be05f4ee5a9a59 clips=4
uv run --frozen --extra dev pytest -q tests/test_content_brief.py
uv run --frozen --extra dev python scripts/run_content_brief.py --brief datasets/content_briefs/lf004-operator-dogfood/brief.json --plates datasets/content_briefs/lf004-operator-dogfood/plates --output datasets/content_briefs/lf004-operator-dogfood/plan.json --run-dir datasets/content_briefs/lf004-operator-dogfood/run
uv run --frozen --extra dev python datasets/content_briefs/lf004-operator-dogfood/run/verify.py --canonical-sha 70280fdcd6fb7f54bc4f7027e03de54e4897178dd41adcf92ef31bd347d7bd86
# Result: status=verified, replay=identical (canonical plan identity, including from a differently located detached checkout)
```
