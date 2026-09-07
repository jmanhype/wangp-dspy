# Finding #32 — premise/content coherence was not enforced

**Status:** Confirmed and guarded at plan/submit 2026-09-07

## Symptom

The acceptance run was recorded as a Devil's Grandma dialogue film, but the
render prompts identify the `lf-001` Lost Futures premise, *The Last
Lighthouse*. Cuts 2–6 therefore render lighthouse imagery and Mara/Ivo-like
characters while their supplied turn WAVs contain the Devil's Grandma lines.

## Evidence

Run: `acceptance-grid56-20260907`.

The six queued prompts all carry the same global identity pin:

> Throughout every scene identity and wardrobe stay locked: S1 (Mara) is a
> weathered lighthouse keeper, S2 (Ivo) is a quiet maintenance engineer.

The per-cut speaker/text fields are:

| cut | prompt speaker/text | supplied media |
|---:|---|---|
| 1 | S1 / “Oh hush now, dear. Have a cookie.” | Devil's Grandma plate + turn WAV |
| 2 | S2 / “Lady, I am on fire!” | Devil's Grandma turn WAV; lighthouse render |
| 3 | S1 / “Then you will want the milk.” | Devil's Grandma turn WAV; lighthouse render |
| 4 | S2 / “Fine. It is a good cookie.” | Devil's Grandma turn WAV; lighthouse render |
| 5 | S1 / “There is a brave boy.” | Devil's Grandma turn WAV; lighthouse render |
| 6 | S2 / “More, please.” | Devil's Grandma turn WAV; lighthouse render |

This is not a hidden fallback discovered during planning. The run explicitly
constructed `DirectorRun(..., premise="lf-001")`; the resulting premise was
resolved and propagated unchanged.

## Code path

1. `services/director/run.py::DirectorRun.__init__` resolves the explicit
   `lf-001` premise.
2. `DirectorRun.plan` copies `self.premise.characters` and passes them to
   `services.chain.controller::build_chain_plan`.
3. `build_chain_plan` validates only that script speaker names exist in that
   roster, then builds `ChainPlan.global_prompt` with the premise descriptions
   in `_global_prompt` and builds each `shot_prompt` from the script line.
4. `_continuation_config` combines that global prompt with the Picture-N
   speaker prompt and emits the per-job manifest; `emit_render_manifest` does
   not add a premise/media coherence check.
5. Before this finding was closed, `DirectorRun.submit` persisted the clips
   without a `premise_id` on each job, so the queue could not independently
   verify that its audio, plate, speaker manifest, and prompt belonged to the
   same premise.

## Root cause

The input contract permits mixing a valid premise roster (`lf-001`, Mara/Ivo)
with an unrelated script/plate/audio bundle (Devil's Grandma). Individual
schemas pass, so the render and Whisper gates can succeed while the film is
creatively about the wrong characters. The defect is a missing cross-artifact
coherence invariant, not a default-premise fallback.

## Closing PR (implemented)

`DirectorRun.plan` now requires a typed-by-schema `media_manifest` with this
shape:

```json
{
  "premise_id": "<resolved premise id>",
  "plates": {"anchor": "...", "<character name>": "..."},
  "audio": [{"path": "...", "speaker": "<character name or SN>"}]
}
```

The guard:

- persists `premise_id` and a canonical character/speaker roster in every run
  and clip manifest;
- requires each script speaker, Picture-N/speaker-manifest ID, plate role, and
  audio turn identity to resolve to that roster;
- rejects a mismatched bundle at plan/submit time before a queue job is
  emitted; and
- adds a regression fixture reproducing the `lf-001` + Devil's Grandma mix and
  asserting fail-closed planning.

`DirectorRun.submit` rechecks the premise/media binding on every clip and
persists it into the queued job. The guard cannot infer the identity of pixels
or waveform content from bytes alone; the explicit manifest is therefore the
auditable source of media identity.

## Re-audit note

Cut 1 is a visual spot-check PASS: it uses the actual Grandma/Soul plate and
shows the expected pair in the sampled first/middle/end frames. Cuts 2–6 are
creative FAILs (wrong identities/scenes, with additional continuity/glitch
failures). The existing verdict ledger remains **NEEDS REVIEW**; this finding
explains the premise mismatch but does not waive model or visual-QC failures.
