# Maestro parity evidence contract

This is the sole programme-wide contract for a Maestro-parity evidence bundle.
Lane stories must reference it and must not copy or specialize the field list.
The executable enforcement is `scripts/verify_maestro_parity.py`; the document
and checker share the field-group list below, and tests fail if they diverge.

## Bundle shape

A bundle is the directory `datasets/runs/maestro-parity/<story-id>/`. Its record
is `evidence.json`, and every path referenced by that record is encoded as a
plain UTF-8 path relative to the bundle root. Absolute paths, `..`, and links
that resolve outside the bundle are invalid. The verifier is strictly read-only:
it never creates, repairs, timestamps, reformats, or copies an inspected bundle.

The record's root `schema` must be exactly
`wangp-dspy.maestro-parity-evidence/v1`.

## Canonical required field groups

All values must be present and internally valid. A blank value is equivalent to
a missing value. The checker reports the most specific field identifier that can
be determined, exits non-zero on any diagnostic, and never upgrades a partially
readable bundle to a pass.

| Field group | Required shape and fail-closed meaning |
| --- | --- |
| `operator_authorization` | Non-empty object with non-blank `text`, `scope`, RFC 3339 `timestamp`, and `approved_by`; `status` must be `approved`. Anything denied, absent, or blank fails. |
| `command` | Non-empty array containing the exact executable argv in order. Every element must be non-blank text; the checker does not reconstruct or substitute arguments. |
| `repository.commit` | Object with non-blank `commit` (40 lowercase/uppercase hexadecimal characters) and `dirty_state`. `dirty_state.dirty` must be boolean and `identity_sha256` must be a 64-character hexadecimal SHA-256 that captures the dirty-state identity. |
| `model_provenance` | Non-empty array. Each item requires non-blank `identity`, `source`, and `license`; either `sha256` (64 hexadecimal characters) or non-blank `immutable_version`; and `download_approved: true`. A model lacking both identity anchors or download approval fails. |
| `reference_provenance` | Non-empty array. Every reference requires a bundle-relative `path`, non-blank `role`, a 64-character `sha256`, and non-blank `license`. The path must identify a regular file in the bundle, and its actual SHA-256 must equal the recorded value. |
| `queue_attempt` | Object with non-blank durable `queue_id`, `job_id`, and `retry_id`; `admission_state` must be `admitted`; `exit_status` must be `succeeded`. |
| `output.sha256` | Non-empty array with bundle-relative `path` and 64-character `sha256` for every emitted artifact. Every path must identify a regular file in the bundle, and hashing its exact bytes must reproduce the recorded value. One mismatch fails the entire bundle. |
| `media_metadata` | Non-empty array with exactly one entry for every `output.sha256` path and no others. Each entry has `path`, `kind`, positive integer `width` and `height`, non-blank `alpha_mode`, and an `audio` object whose `present` is boolean. For `kind: video`, `duration_s` and `fps` are positive numbers; when audio is present, non-blank `codec`, positive integer `sample_rate_hz`, and positive integer `channels` are required. For `kind: image`, `duration_s` and `fps` are null and `audio.present` is false. |
| `objective_gate_results` | Non-empty array for every declared objective gate. Each item has non-blank `name`, a non-empty `inputs` array of non-blank values, numeric `threshold`, numeric `measured`, and `verdict`. Only `pass` is acceptable for a verified parity row; failing or omitted gates fail. |
| `reviewer_verdict` | Object with `decision: approved` and a non-empty `evidence_links` array of non-blank links to the reviewer's evidence. |

## Hash and verdict semantics

Hashes are lowercase-or-uppercase hexadecimal SHA-256 over exact file bytes;
cosmetic normalization is forbidden. The verifier computes each reference and
output hash from disk and reports the exact field, recorded value, and observed
value on mismatch. It does not trust an artifact filename, media duration, model
label, or score merely because text is present.

Pass requires **all** field groups and nested values to validate, all recorded
reference/output hashes to match disk, every declared objective gate to pass,
and explicit operator and reviewer approval. The CLI prints `PASS` and exits
zero only on that state; every other state prints a `FAIL <field>: <reason>`
diagnostic and exits one.

WD-651z proves this contract using fixture bundles in temporary test
directories only. Real bundles from parity lanes are applied and verified by the
programme capstone, WD-fay0; no fixture or demonstration bundle may be placed in
`datasets/runs/maestro-parity/`.
