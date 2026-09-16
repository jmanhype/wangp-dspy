# 66 — dirty-run provenance was incomplete

Status: CLOSED in PR #97 / commit `d52a45d`; complete dirty-run provenance is
on `main`.

## Evidence

Qodo review of PR #87 found two provenance gaps:

1. `append_dataset_run` retained only repository root and commit SHA, dropping
   the newly captured clean/dirty state and status/diff hashes from canonical
   dataset-run records.
2. Git status identified untracked paths, but the provenance hashes did not
   cover untracked file types, modes, and contents. Two materially different
   dirty trees could therefore share the same recorded identity.

## Minimal fix

Dataset-run emission now validates and persists the complete repository
identity. Repository identity additionally records a deterministic
`untracked_content_sha256` over every nonignored untracked path, its file type
and mode, symlink target bytes where applicable, and regular-file bytes.

The path entries include an explicit length prefix, avoiding ambiguous
concatenations, and regular files are hashed in bounded chunks.

## Resolution

`services/director/run_ledger.py` captures deterministic untracked content
identity and `services/director/run_records.py` preserves the complete
repository provenance in canonical records. Regression coverage is in
`tests/test_run_identity.py`. The strict LF002 single-ledger record also
demonstrates a clean checkout with zero changed/untracked paths. The full
suite at `9b70be1` passed 1380 tests with one intentional skip and no
failures.
