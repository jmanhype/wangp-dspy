# WD-bxhc operator authorization

- **Status:** approved
- **Approved by:** operator via `/root` parent authorization
- **Timestamp:** 2026-09-25T19:05:00Z
- **Scope:** WD-bxhc host batch 1 only: the 3,208,948,928-byte Chatterbox multilingual asset set, real VibeVoice and Chatterbox speech operations, and model-free portable-character operations on host `3090`.
- **Download ceiling:** 20,000,000,000 bytes.
- **GPU boundary:** use only free VRAM remaining beside the operator's already-running `llama-server`; do not stop, restart, or otherwise modify that process.
- **Rights boundary:** cloning references must be operator-owned synthetic assets with exact hashes, source, licence, and consent references; no third-party voice, unlicensed reference, training, or redistribution.

Verbatim operator words already recorded by the programme and carried forward by the dispatcher:

```text
I agree
you need to kill whatever that is that was holding up the GPU and get back to work so that we can finish and complete this
Unblock and cont
```

Verbatim dispatcher authorization for this lane:

```text
the operator approved host batch 1 with a 20 GB download ceiling and has repeatedly instructed to continue/unblock the programme
```

The older “kill whatever that is” sentence is historical authorization context only. This lane's explicit boundary above supersedes it: `llama-server` must remain running.

## Rework rights determination

The authoritative reference-rights rework is [`reference-consent-rework.md`](reference-consent-rework.md).
It corrects producer/source/licence attribution and explicitly records that
WD-bxhc cross-story cloning-reuse consent is not evidenced. Consequently clone,
saved-voice, and cross-mode matrix cells must not be promoted to
`host_run_verified` until the operator supplies reference-specific consent.
