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
| Portable package round-trip and hashes | host_run_verified ([WD-bxhc record](../datasets/runs/maestro-parity/WD-bxhc/evidence.json)) | host_run_verified ([WD-bxhc record](../datasets/runs/maestro-parity/WD-bxhc/evidence.json)) | Deterministic export/import/re-export hash equality in [WD-bxhc evidence](../datasets/runs/maestro-parity/WD-bxhc/evidence.json) |
| Saved voice binding | evidence_complete_pending_review ([corrected provenance; consent absent](../datasets/runs/maestro-parity/WD-bxhc/reference-consent-rework.md)) | evidence_complete_pending_review ([corrected provenance; consent absent](../datasets/runs/maestro-parity/WD-bxhc/reference-consent-rework.md)) | Binding hashes exist, but the embedded references lack evidenced WD-bxhc cloning-reuse consent |
| Native-source recovery | host_run_verified ([WD-bxhc record](../datasets/runs/maestro-parity/WD-bxhc/evidence.json)) | host_run_verified ([WD-bxhc record](../datasets/runs/maestro-parity/WD-bxhc/evidence.json)) | Byte-for-byte source/recovery hash equality without transcoding in [WD-bxhc evidence](../datasets/runs/maestro-parity/WD-bxhc/evidence.json) |
| Registry identity resolution | host_run_verified ([WD-bxhc record](../datasets/runs/maestro-parity/WD-bxhc/evidence.json)) | host_run_verified ([WD-bxhc record](../datasets/runs/maestro-parity/WD-bxhc/evidence.json)) | Unique ID and alias resolution over an explicit local package registry in [WD-bxhc evidence](../datasets/runs/maestro-parity/WD-bxhc/evidence.json) |
| Appearance and voice mismatch rejection | host_run_verified ([WD-bxhc record](../datasets/runs/maestro-parity/WD-bxhc/evidence.json)) | host_run_verified ([WD-bxhc record](../datasets/runs/maestro-parity/WD-bxhc/evidence.json)) | Typed package-, appearance-, and voice-mismatch probes each exit 2 in [WD-bxhc evidence](../datasets/runs/maestro-parity/WD-bxhc/evidence.json) |
| Duplicate and ambiguous identity rejection | host_run_verified ([WD-bxhc record](../datasets/runs/maestro-parity/WD-bxhc/evidence.json)) | host_run_verified ([WD-bxhc record](../datasets/runs/maestro-parity/WD-bxhc/evidence.json)) | Real duplicate-ID and ambiguous-alias registries each reject with exit 2 in [WD-bxhc evidence](../datasets/runs/maestro-parity/WD-bxhc/evidence.json) |
| Immutable non-executable planning | host_run_verified ([WD-bxhc record](../datasets/runs/maestro-parity/WD-bxhc/evidence.json)) | host_run_verified ([WD-bxhc record](../datasets/runs/maestro-parity/WD-bxhc/evidence.json)) | Four speech and two character immutable databases reconstruct with no hidden mutation in [WD-bxhc evidence](../datasets/runs/maestro-parity/WD-bxhc/evidence.json) |
| Seed-based reconstruction | host_run_verified ([WD-bxhc record](../datasets/runs/maestro-parity/WD-bxhc/evidence.json)) | host_run_verified ([WD-bxhc record](../datasets/runs/maestro-parity/WD-bxhc/evidence.json)) | All six recorded binding/seed hashes reconstruct exactly in [WD-bxhc evidence](../datasets/runs/maestro-parity/WD-bxhc/evidence.json) |
| Cross-mode identity preservation | evidence_complete_pending_review ([anchor verified; consent absent](../datasets/runs/maestro-parity/WD-bxhc/reference-consent-rework.md)) | evidence_complete_pending_review ([anchor verified; consent absent](../datasets/runs/maestro-parity/WD-bxhc/reference-consent-rework.md)) | Image and video share the full anchor, but the saved-voice reference consent chain remains unapproved |
| Generated speech, image, or video continuity | unsupported in this lane | unsupported in this lane | none |

The 14 promoted cells in the seven reviewer-accepted deterministic rows remain bound to the WD-bxhc bundle with `reviewer_verdict: pending`. Saved voice binding and cross-mode identity preservation are deliberately non-verified: their package/video anchor is real and hash-equal, but their embedded references inherit the unresolved cloning-reuse consent documented in [`reference-consent-rework.md`](../datasets/runs/maestro-parity/WD-bxhc/reference-consent-rework.md). The image and video still do not promote the separate semantic “Generated speech, image, or video continuity” row, which remains unsupported in this lane.
