# Maestro speech capability planning

`wgp voice` is a deterministic, typed, no-GPU planning surface for plain speech, reference cloning, ordered segment assembly, and portable character bindings. A successful plan proves request shape and durable planning only; it never proves that audio exists.

## Request schema

Requests use `wangp-dspy.speech-capability-request/v1`. The independently implemented slots are:

- `vibevoice/vibe_7b`: primary VibeVoice-compatible slot; plans `speech` and `voice_clone`, zero/one/two-reference counts, 1,200-character and 30-second segment ceilings.
- `chatterbox/chatterbox_multilingual`: independent fallback slot; plans `speech` only, with 600-character and 20-second segment ceilings.

The manifest supplied through `--models` must record each slot's SHA-256, license and explicit acceptance, source, usage constraint, and VRAM profile. Wangp never downloads a model or calls a provider.

A request carries language, immutable style, full text, ordered WAV references when cloning, segment policy, 24 kHz mono target, planned output path, optional character binding, and recipe seed. `speech` cannot carry references. `voice_clone` requires exactly one `primary` WAV or a `primary` plus `secondary` WAV, each at least two seconds, with source, license, consent reference, and byte hash. Chatterbox pairing with cloning is unsupported and fails before durable state.

Segment planning first keeps sentence chunks below the requested character limit, then splits an over-limit sentence on spaces. An over-limit unsplittable token, a request above the engine's real limit, or an invalid duration fails with typed exit 2. Every ordered record carries its text/hash, start/end accounting, planned silence, engine settings, reference hashes, model provenance, package binding, 24 kHz mono declaration, and assembled target. Assembly is an explicit ordered concatenation plan with planned character and silence accounting; actual duration and audio are **not verified - requires authorized host run**.

## Commands

```text
wgp voice plan --request speech.json --models models.json --json
wgp voice generate --request speech.json --models models.json --db run/plans.db --json
wgp voice clone --request clone.json --models models.json --db run/plans.db --json
wgp voice export --request clone.json --models models.json --package character.wgpvoice --json
wgp voice import --package character.wgpvoice --destination imported-character --json
wgp voice plan --db run/plans.db --reconstruct --json
```

Durable writes go only to `speech_plan_records`, not the executable `jobs` table. Update and delete triggers make records immutable. Every record has `plan_only=true`, `executable=false`, `queue_submitted=false`, and `host_contact=false`. The real admission path therefore selects nothing from these records while a genuine render job remains admissible.

Reconstruction independently validates each frozen recipe, re-splits its text, regenerates per-segment settings, and compares canonical SHA-256 hashes. Absent, empty, malformed, or edited databases fail closed with exit 2 and `hidden_mutation=true`.

## Portable character voices

A `.wgpvoice` package is a deterministic ZIP containing `voice-package.json`, one appearance image, and one or two WAV references under canonical `references/` names. The manifest binds character ID, speaker label, voice binding ID, appearance hash/member, engine compatibility, reference roles/durations/hashes, language, style, source, license, and consent reference. Export never copies host credentials or unrelated files.

Import accepts only a new destination directory, rejects encryption, duplicate members, paths outside the canonical namespace, oversized members, and hash mismatches, and writes controlled member names rather than extracting arbitrary ZIP paths. The package proves provenance and portability only; it contains no claim that its target speech was generated.

## Capability matrix

| Engine / mode | Plain speech | One-reference clone | Two-reference clone | Generation evidence |
| --- | --- | --- | --- | --- |
| `vibevoice/vibe_7b` | planned | planned | planned | none |
| `chatterbox/chatterbox_multilingual` | planned | unsupported | unsupported | none |

All executable rows remain `planned`. A row can become `host_run_verified` only from a separately authorized bundle recording operator authorization, command, repository commit, model/reference provenance, queue attempt, exit status, output hashes, measured ffprobe metadata, transcript evidence, AV-sync evidence where applicable, and portable-package linkage. No GPU, SSH, model download, paid provider, renderer, queue gate, retry, or QC semantic is exercised or changed by this planning slice.
