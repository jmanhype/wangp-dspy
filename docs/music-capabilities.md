# Maestro music capability planning

`wgp music` is a deterministic, typed, no-GPU planning surface. It normalizes melody/chord sections and ABC input, records two independent model slots, preserves style-reference provenance, and emits immutable plan records outside the executable queue. A successful plan proves request and queue shape only; it never proves that audio was generated.

## Request schema

Generation and style adaptation use `wangp-dspy.music-capability-request/v1`. A request carries immutable model provenance separately through `--models`; Wangp never downloads either model. Both slots support `instrumental` and `song` presets, but only `ace_step` currently plans style adaptation:

- `ace_step`: independent slot one, `planned/ace_step` model type
- `stable_audio`: independent slot two, `planned/stable_audio` model type

Each request records title, style, lyrics when the preset is `song`, tempo, meter, key, section names/durations, melody ABC, chord symbols, exact duration, 48 kHz stereo target, and recipe seed. The target format is fixed to `48000 Hz / 2 channels`. A filename or request field never becomes a format claim; a future authorized run must measure actual output with ffprobe.

Sections must have unique names and durations that sum exactly to `duration_s`. Melody lines must be complete `|...|` ABC bars containing at least two ABC notes/rests per bar. Chords use lead-sheet symbols such as `C`, `Am`, `Fmaj7`, and `G/B`. The compiler emits a deterministic score containing `X`, `T`, `M`, `L`, `Q`, `K`, section comments, melody bars, and chord annotations.

Style adaptation requires readable, hash-matched reference audio, recorded source and rights, readable hash-matched before-audio, a distinct nonexistent after-audio path, a planned host-only command, and an `audible_ab` comparison contract. References are never copied, relicensed, or redistributed by this surface. Planning validates structure only: it executes no training, inference, encoder pass, or write to the planned after path and makes no aesthetic verdict.

## Commands

```text
wgp music plan --request request.json --models models.json --score-out song.abc --json
wgp music compile --request request.json --models models.json --db run/plans.db --score-out song.abc --json
wgp music style --request style-request.json --models models.json --json
wgp music compare --db run/plans.db --json
```

`compile` creates one immutable record per requested track in a new SQLite database. Records live in `music_plan_records`, with update and delete triggers, not the executable `jobs` table. Every record pins the full normalized score and score hash, arrangement, section, backend family/preset/type/hash/license/source/usage constraint/VRAM profile, 48 kHz stereo target, style-reference hashes and rights, before-audio hash, planned after path, comparison mode, and normalized settings plus canonical settings hash. `plan_only=true`, `executable=false`, `queue_submitted=false`, and `host_contact=false`; no real admission path can drain these records.

`compare` opens the database read-only, independently reconstructs the score and model settings from the typed recipe, and compares both canonical hashes. Every record must match. Absent, empty, malformed, or edited records fail closed with exit code 2 and `hidden_mutation=true` on a hash mismatch.

## Capability matrix and authorization boundary

| Model slot / operation | Generate | Style adapt | Generation evidence |
| --- | --- | --- | --- |
| `ace_step` | planned | planned | none |
| `stable_audio` | planned | unsupported for planning | none |

Every executable row remains `planned`. A row can become `host_run_verified` only from a separately authorized bundle containing command, repository commit, model/reference provenance, queue attempt, exit status, output hashes, measured 48 kHz stereo ffprobe metadata, QC evidence, and operator authorization. Instrumental and non-instrumental output on both slots, second-model output, audible style A/B output, training/reference provenance, and style adaptation are therefore **not verified - requires authorized host run**. No GPU, SSH, model download, paid provider, renderer, queue gate, retry, or QC/AV semantic is exercised or changed by this planning slice.
