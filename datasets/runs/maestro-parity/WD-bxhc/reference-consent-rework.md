# WD-bxhc reference provenance and consent rework

This record corrects the rejected WD-bxhc cloning chain without changing any
accepted output bytes. It is a rights record, not reviewer approval.

## Primary reference b013bad88be5b44609304764aaa6b10afb9f0299d768c8abc48c2d1afd4bed18

- **WD-bxhc path:** `inputs/voice-primary-vibe.wav`
- **True source:** byte-for-byte copy of WD-cpow `datasets/runs/maestro-parity/WD-cpow/inputs/target-voice.wav`.
- **Producer/history:** operator-owned LF002 Orin voice guide; WD-cpow used it as the VibeVoice revoice target.
- **Licence:** operator-owned evaluation asset; no redistribution.
- **Upstream rights evidence:** WD-cpow `operator-authorization.md` states verbatim: “Source/target rights: operator-owned `inputs/source.mp4` and `inputs/target-voice.wav`; outputs are operator-owned evaluation artifacts and must not be redistributed.”
- **Consent status:** NOT EVIDENCED for cross-story reuse as a WD-bxhc cloning reference. The quoted WD-cpow authorization establishes ownership and evaluation rights in that lane, but contains no operator statement consenting to WD-bxhc voice cloning.
- **Consequence:** no WD-bxhc clone row is promoted to `host_run_verified` on this reference.

## Secondary reference e371ebe7ee1ce9964657b4f34f61d32fbff2a5345bdb90add6c3e7dba1ee2175

- **WD-bxhc path:** `inputs/voice-secondary.wav`
- **True source:** byte-for-byte copy of WD-cpow `datasets/runs/maestro-parity/WD-cpow/outputs/wd_cpow_vibevoice_raw.prepared.wav`.
- **Producer/history:** VibeVoice-7B output prepared by WD-cpow from primary `b013bad…bed18`; it is not Chatterbox and was not produced by WD-bxhc.
- **Licence:** operator-owned WD-cpow evaluation output; no redistribution.
- **Upstream rights evidence:** WD-cpow `operator-authorization.md` states verbatim that “outputs are operator-owned evaluation artifacts and must not be redistributed.”
- **Consent status:** NOT EVIDENCED for cross-story reuse as a WD-bxhc cloning reference. Ownership alone is not cloning consent.
- **Consequence:** the two-reference clone, saved portable voice binding, and cross-mode claims remain non-verified pending explicit operator consent.

## Rework boundary

The original generated audio, image, and video bytes are retained. Historical
failed-attempt sidecars remain unchanged as rejection evidence. Only the final
authoritative sidecars and reworked request/provenance records cite the two
anchors above. The original `.wgpvoice` and `.wgpcharacter` bytes are also
retained to preserve the accepted identity anchor; their rows remain
non-verified because their embedded reference consent chain is not approved.
