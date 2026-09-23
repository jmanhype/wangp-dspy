# Portable character capability planning

`wgp character` is a deterministic, typed, no-GPU planning surface for portable character identity, appearance, saved voice bindings, and cross-mode continuity contracts. A successful package, import, registry lookup, or plan proves bytes and request shape only. It never proves that an image, video, voice, or identity-preserving result was generated.

## Portable format

A character definition uses `wangp-dspy.character-package/v1`. It records a character ID, speaker label, version, description, at least one appearance role (including exactly one `native` view), a required saved `.wgpvoice` package, image/video continuity modes and thresholds, and a recipe seed. Every appearance path is hash-pinned and carries its recorded native source path, license, and consent reference.

Export writes a deterministic `.wgpcharacter` ZIP containing:

- `character.json`: the immutable package manifest and identity hash;
- `appearance/<role>.<suffix>`: byte-for-byte appearance members;
- `voice/character.wgpvoice`: the unchanged saved voice package.

Export validates appearance and voice hashes before writing. Import accepts only a new destination, rejects encrypted, oversized, duplicate, unsafe, unexpected, or hash-mismatched members, and never treats an archive entry as executable. The saved voice manifest must agree on character ID, speaker label, and voice binding ID. Re-exporting the same definition and bytes yields the same package SHA-256.

Native recovery follows the manifest to its recorded source, verifies the exact source hash, and copies the bytes without decoding or transcoding. A missing or changed source fails closed; Wangp never substitutes a thumbnail or derivative.

## Identity registry and continuity requests

An explicit registry directory is built only from its portable packages. It resolves a character by unique character ID or unique case-insensitive speaker alias. Duplicate character IDs or ambiguous speaker labels fail before resolution.

Image and video requests use `wangp-dspy.character-continuity-request/v1`. A request names its mode, mode-compatible operation, prompt, seed, and complete character reference: package path/hash, character ID and speaker label, appearance member/hash, saved voice member/hash/binding, and supported modes. Planning reopens the package, verifies every hash, checks identity, requires the mode to be declared in the package, and fails closed on any mismatch.

Typed exit-2 diagnostics cover missing or invalid definitions, unreadable appearance or voice assets, binding mismatches, invalid or tampered packages, existing outputs or destinations, unavailable native sources, duplicate or ambiguous identities, unsupported modes, invalid requests, and unusable plan databases. Each diagnostic includes remediation and a safe next command; no partial queue database is left behind.

## Commands

```text
wgp character create --definition character.json --out normalized.json --json
wgp character bind-voice --definition character.json --voice orin.wgpvoice --out bound.json --json
wgp character export --definition bound.json --package orin.wgpcharacter --json
wgp character import --package orin.wgpcharacter --destination imported-orin --json
wgp character show --package orin.wgpcharacter --json
wgp character recover --package orin.wgpcharacter --destination native.png --json
wgp character resolve --registry registry/ --identity "Orin Vale" --json
wgp character plan --request image.json --dry-run --json
wgp character plan --request video.json --db run/character-plan.db --json
wgp character plan --db run/character-plan.db --reconstruct --json
```

Durable plans are written only to `character_plan_records`, never to the executable `jobs` table. Update and delete triggers reject mutation. Every record carries `plan_only=true`, `executable=false`, `queue_submitted=false`, `host_contact=false`, and `media_generated=false`; the real admission path selects none while a genuine render job remains admissible. Reconstruction validates the frozen request, reopens and revalidates the package, independently regenerates the binding and seed hashes, and reports `hidden_mutation` on any mismatch.

## Capability matrix

| Capability | Image | Video | Generation evidence |
| --- | --- | --- | --- |
| Portable package round-trip and hashes | planned | planned | none |
| Saved voice binding | planned | planned | none |
| Native-source recovery | planned | planned | none |
| Registry identity resolution | planned | planned | none |
| Appearance and voice mismatch rejection | planned | planned | none |
| Duplicate and ambiguous identity rejection | planned | planned | none |
| Immutable non-executable planning | planned | planned | none |
| Seed-based reconstruction | planned | planned | none |
| Cross-mode identity preservation | planned | planned | none |
| Generated speech, image, or video continuity | unsupported in this lane | unsupported in this lane | none |

Every capability row above remains `planned`; none has generation evidence. Cross-mode identity preservation and generated media are **not verified - requires authorized host run**. Such a claim requires a separately authorized bundle recording operator authorization, command, repository commit, character/voice/model provenance, queue attempt, output hashes, objective identity-gate evidence, and reviewer decision. No GPU, SSH, model download, paid provider, renderer admission, retry, or QC/AV semantic is exercised or changed by this planning surface.
