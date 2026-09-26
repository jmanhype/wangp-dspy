---
id: WD-f0vk
title: "Wan2GP emits nonfatal mutagen metadata errors after successful media saves"
status: in_progress
priority: 0
type: bug
labels: [discovered-by-pm, delivered]
parent: WD-3nod
created_at: 2026-09-26T17:06:49Z
created_by: speed
updated_at: 2026-09-26T17:48:54Z
closed_at: ""
close_reason: ""
content_hash: "sha256:8802004483b31cb56553dbc50e3a64f2fbf57097d54c547dbc83f22dcfc1f051"
blocks: [WD-fay0]
assignee: dev-WD-f0vk
follows: [WD-9t9o, WD-isg9]
---
## Description
## Context

PM review of accepted story WD-9t9o found that all three successful H3 VDN media operations emitted Wan2GP metadata errors from a host Python environment missing `mutagen`. The errors are nonfatal: each log subsequently records a saved media file, and WD-9t9o records passing output hashes, ffprobe evidence, 39/39 objective gates, scoped tests, backlog lint, diff check, and clean release verification.

The pushed WD-9t9o evidence commit is `216e7448c9a287f9df1b74e56f7dfd044e35af96` on `origin/story/WD-9t9o`:

- `datasets/runs/maestro-parity/WD-9t9o/host-logs/edit.render.log:39` — `Error saving metadata to MP4 ... No module named 'mutagen'`; line 40 says `Video file saved`.
- `datasets/runs/maestro-parity/WD-9t9o/host-logs/repaint.render.log:40` — the same metadata error; line 41 says `Video file saved`.
- `datasets/runs/maestro-parity/WD-9t9o/host-logs/upscale.render.log:11` — postprocessed video saved; lines 12-13 report cover-art extraction and metadata-save failures from the missing module.

The same condition exists in accepted WD-isg9 evidence at `datasets/runs/maestro-parity/WD-isg9/host-logs/edit.render.log:38`, `repaint.render.log:39`, and `upscale.render.log:12-13`. WD-g125 also contains an earlier embedded `DISCOVERED_BUG` named `WanGP remote metadata writer lacks mutagen`; no standalone triaged bug currently exists for that report.

Observed log SHA-256 values in the WD-9t9o worktree are:

- edit log: `231e61e337b000739786a58609c06ea3e8b4f546208148f8ef9fe3ea59fab64f`
- repaint log: `7bae39cb07ac15d5697253879e1f9313dfa23981a9dfa017baa3eb864901ca0a`
- upscale log: `91146c81e34bf1f73c214fe6766988d3245de28025b35092f2b2f9802bc4a101`

## Root Cause

The observed failure boundary is known: Wan2GP attempts MP4 metadata and cover-art operations that import `mutagen`, the active host Python environment cannot import it, and the exception path continues after media bytes are saved. The exact source site, dependency declaration, and intended optional/required behavior have not yet been identified; this story must diagnose them rather than assume that an ad hoc host package installation is the durable fix.

## Affected Components

- External Wan2GP MP4 metadata writer and cover-art extraction path used by the `3090` host.
- WD-9t9o host evidence bundle under `datasets/runs/maestro-parity/WD-9t9o/host-logs/`.
- Comparative accepted WD-isg9 host evidence under `datasets/runs/maestro-parity/WD-isg9/host-logs/`.
- Wangp evidence review/warning ownership: successful media gates must not silently normalize these unexplained host errors.

## Acceptance Criteria

- [ ] The diagnosis records the exact Wan2GP source site, runtime environment identity, and dependency classification for `mutagen`, distinguishing required metadata behavior from an optional nicety.
- [ ] A durable correction is implemented where Wangp owns the seam, or an upstream ticket plus a local fail-closed diagnostic/preflight is recorded if the defect is entirely external; an undocumented manual host install is not accepted.
- [ ] Regression coverage detects the exact `No module named 'mutagen'` metadata and cover-art conditions in the preserved WD-9t9o logs and requires explicit warning ownership rather than treating them as ordinary success output.
- [ ] The correction does not mutate any accepted media artifact, output hash, ffprobe record, objective-gate result, or evidence log.
- [ ] No GPU render, model download, training, or unrelated host mutation is authorized by this story; any live host verification other than a separately approved non-render dependency probe must be recorded as blocked rather than improvised.
- [ ] Targeted tests, `pvg lint --backlog`, and `git diff --check` pass, and delivery evidence links the exact source/test changes to these criteria.

## Testing Requirements

- Unit tests: missing-dependency classification, preserved-log recognition, warning ownership, and rejection of an ad hoc undocumented host fix.
- Integration tests: MANDATORY (no mocks). Exercise the actual Wangp diagnostic/evidence path against the real preserved WD-9t9o and WD-isg9 log bytes and their recorded hashes.
- Negative tests: a synthetic unrelated Python import error must not be mislabeled as this mutagen condition, and a missing log must fail closed.
- Standing gates: targeted suite selected by the developer, `pvg lint --backlog`, and `git diff --check`.
- This story does not authorize SSH, GPU rendering, model inference, downloads, or mutation of accepted host evidence.

## Discovered During

Story WD-9t9o: PM closeout review observed nonfatal missing-mutagen errors in edit, repaint, and upscale logs despite successful saves and passing media evidence; accepted WD-isg9 shows the same host condition.

## Capstone Impact

This bug blocks WD-fay0 at the governance gate, not by invalidating the accepted lane evidence. The saved media, hashes, ffprobe records, objective gates, and checker evidence remain usable, but WD-fay0 requires a clean backlog lint gate and WD-3nod cannot complete with this P0 sibling unresolved. The `WD-fay0 depends on WD-f0vk` edge is therefore required.

## MANDATORY SKILLS

- pvg — shared tracker operations, delivery evidence, lint, and story governance.
- nd — issue/dependency semantics and append-only evidence contract.

## Skills To Use

- pvg and nd for implementation and delivery governance.
- tool-systematic-debugging before changing host dependency or warning-classification behavior.

## nd_contract
status: new

### evidence
- Created: 2026-09-26 from the PM-supplied DISCOVERED_BUG report, with WD-9t9o commit `216e7448c9a287f9df1b74e56f7dfd044e35af96` and comparative WD-isg9 evidence inspected.

### proof
- [ ] Pending implementation

## Notes
## Implementation Evidence (REWORK DELIVERED)

### CI/Test Results
Commands run:
- uv run --frozen --offline --extra dev pytest -q tests/test_maestro_parity_evidence.py tests/test_production_render_seam.py --junitxml=/tmp/WD-f0vk-rework-targeted.xml
- uv run --frozen --offline python /tmp/wdf0vk_scan_real_final.py
- uv run --frozen --offline python -m py_compile scripts/verify_maestro_parity.py tests/test_maestro_parity_evidence.py
- uv run --frozen --offline python -m json.tool datasets/diagnostics/wan2gp-mutagen/WD-f0vk.json
- pvg verify scripts/verify_maestro_parity.py tests/test_maestro_parity_evidence.py datasets/diagnostics/wan2gp-mutagen/WD-f0vk.json docs/findings/86-wan2gp-mutagen-metadata-warnings.md docs/maestro-parity-evidence-contract.md --format=text
- pvg lint --backlog
- git diff --check
- git diff --cached --check
- git diff --exit-code -- datasets/runs/maestro-parity/WD-9t9o datasets/runs/maestro-parity/WD-isg9
- uv run --frozen --offline --extra dev wgp release verify
- git push origin story/WD-f0vk

Summary: rework PASS. Targeted JUnit tests=106 errors=0 failures=0 skipped=0. Real-byte scan remains WD-9t9o owned_warnings=4 diagnostics=0 and WD-isg9 owned_warnings=4 diagnostics=0 with exact lines/hashes. Compile and JSON validation PASS. pvg verify PASS (2 scannable files, 0 issues). Backlog lint PASS (134 scanned, 0 errors, 0 review findings). Both diff checks and accepted-evidence diff check PASS. Release verify PASS with release=ready and tag_created=false. Branch pushed from 59ae9790 to 0a3d95c070a6618e58d16617f5d9a13b34ebe894.

### Rework blocker verification
| QC blocker | Correction | Test |
|---|---|---|
| SHA case normalization | Output, reference, and native-log comparisons lower normalized valid 64-hex values before comparison while preserving shape diagnostics and exact recorded values in mismatch text | tests/test_maestro_parity_evidence.py:test_uppercase_sha256_values_match_exact_bytes_for_all_hashed_groups |
| Shared strict path resolver | One _safe_bundle_file resolver is used by outputs, references, and native logs; rejects blank/absolute paths, lexical .., symlinked components, resolved escapes, and non-files | lexical-dotdot and symlinked-parent parametrized tests across all three groups |
| Exhaustive import classification | Every No-module occurrence is found with finditer; multiple/ambiguous failures reject; ModuleNotFoundError/ImportError-only lines reject; only one exact owned mutagen form passes | secondary-import, ImportError-spelling, multiple-occurrence, and unrelated-import tests |
| Native hash map exactness | When present, values must be valid SHA-256 and key set must exactly equal deduplicated native_logs; extras and missing keys fail | test_extra_native_log_hash_key_fails_closed and existing mismatch/real-hash tests |

### Commit
- Branch: story/WD-f0vk
- Rework SHA: 0a3d95c070a6618e58d16617f5d9a13b34ebe894
- Push: origin/story/WD-f0vk advanced 59ae9790 -> 0a3d95c0.
- No SSH, GPU, inference, download, host mutation, or accepted evidence-byte mutation.

LEARNINGS:
- Case-insensitive hex comparison must happen only after the existing 64-hex shape gate, never by widening the value pattern.
- Checking only the final path component misses symlinked parents; the shared resolver walks and lstats every lexical component before resolve.
- Import-failure classification needs all occurrences and both Python exception spellings, not the first regex search result.
- Hash-map key-set equality prevents an otherwise valid log from hiding undeclared extra expectations.

## nd_contract
status: delivered

### evidence
- Rework commit 0a3d95c070a6618e58d16617f5d9a13b34ebe894 pushed to origin/story/WD-f0vk.
- Targeted 106/106 PASS; real WD scans unchanged at 4 owned warnings and 0 diagnostics each; pvg verify/backlog lint/diff checks/release verify PASS.

### proof
- [x] QC blocker 1: uppercase output/reference/native-log SHA values compare correctly without weakening shape checks.
- [x] QC blocker 2: outputs, references, and native logs share one strict path resolver and reject all requested unsafe forms.
- [x] QC blocker 3: every import failure occurrence and exception spelling is classified or fails closed.
- [x] QC blocker 4: native-log hash values and exact deduplicated key set are enforced, including extras.
- [x] Accepted WD-9t9o/WD-isg9 evidence remains byte-unchanged.

## Implementation Evidence

### CI/Test Results
Commands run:
- uv run --frozen --offline --extra dev pytest -q tests/test_maestro_parity_evidence.py tests/test_production_render_seam.py --junitxml=/tmp/WD-f0vk-targeted.xml
- pvg lint --backlog
- git diff --check
- git diff --cached --check
- uv run --frozen --offline --extra dev wgp release verify
- git ls-remote origin refs/heads/story/WD-f0vk

Summary: targeted tests PASS (95 run, 0 errors, 0 failures, 0 skipped); backlog lint PASS (134 scanned, 0 errors, 0 review findings); both diff checks PASS; release=ready and tag_created=false; pushed branch SHA 59ae97903978c5f04a4dbffd7e372e0fe7d5a74a. Coverage was not collected; the targeted result provides 95 exact executed tests with zero skips.

## nd_contract
status: delivered

### evidence
- Authoritative detailed proof, diagnosis, AC table, and SHA remain in the preceding delivered evidence block.
- Delivery-shape repair records the exact verifier-required CI/Test Results, Commands run, and Summary fields without changing code or the pushed commit.

### proof
- [x] Delivery proof preflight shape complete in addition to the detailed 6/6 AC proof above.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-26.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

PROOF:

### Commands and measured results
- Targeted: `uv run --frozen --offline --extra dev pytest -q tests/test_maestro_parity_evidence.py tests/test_production_render_seam.py --junitxml=/tmp/WD-f0vk-targeted.xml` — PASS, JUnit tests=95 errors=0 failures=0 skipped=0.
- Real-byte scanner: `uv run --frozen --offline python /tmp/wdf0vk_scan_real_final.py` — WD-9t9o owned_warnings=4 diagnostics=0; WD-isg9 owned_warnings=4 diagnostics=0. Each set includes edit metadata, repaint metadata, and upscale cover-art + metadata at the exact committed lines/hashes.
- Compile/JSON: `uv run --frozen --offline python -m py_compile scripts/verify_maestro_parity.py tests/test_maestro_parity_evidence.py` and `python -m json.tool datasets/diagnostics/wan2gp-mutagen/WD-f0vk.json` — PASS.
- Static: `pvg verify scripts/verify_maestro_parity.py tests/test_maestro_parity_evidence.py datasets/diagnostics/wan2gp-mutagen/WD-f0vk.json docs/findings/86-wan2gp-mutagen-metadata-warnings.md docs/maestro-parity-evidence-contract.md --format=text` — VERIFY PASSED (2 scannable files, 0 issues).
- Backlog: `pvg lint --backlog` — PASS, 134 scanned, 0 errors, 0 review findings.
- Whitespace/clean tree: `git diff --check`, `git diff --cached --check`, and clean `git status --short` — PASS after commit.
- Release: `uv run --frozen --offline --extra dev wgp release verify` — release=ready, tag_created=false.
- Accepted-log preservation: `git diff --exit-code -- datasets/runs/maestro-parity/WD-9t9o datasets/runs/maestro-parity/WD-isg9` — PASS. Recomputed SHA-256 values exactly match the six values in the diagnosis artifact.
- No SSH, GPU, inference, model download, host mutation, accepted-log edit, output edit, ffprobe edit, or gate-result edit was performed.

### Diagnosis
- Exact accepted-evidence source site: `/home/straughter/Wan2GP/wgp.py::generate_media`; accepted same-runtime stack frames identify generate_media at wgp.py:7583 and 7870. The exact mutagen statement line is not present in preserved bytes and is not invented.
- Runtime: host straughter-Z690-Steel-Legend, `/home/straughter/Wan2GP/venv/bin/python`, Python 3.11, mutagen absent in active venv. Accepted WD-m0r5 local inventory separately shows user Python 3.12 mutagen 1.47.0, not active Wan2GP venv.
- Dependency classification: mutagen is required for embedded metadata/cover-art success but optional for saved media bytes in the observed caught-error control flow. Wangp does not declare it; upstream declaration is not preserved, and no ad hoc install is made.

### Commit
- Branch: story/WD-f0vk
- SHA: 59ae97903978c5f04a4dbffd7e372e0fe7d5a74a
- Remote: origin/story/WD-f0vk at the same SHA (verified by git ls-remote).
- Files: scripts/verify_maestro_parity.py; tests/test_maestro_parity_evidence.py; docs/maestro-parity-evidence-contract.md; datasets/diagnostics/wan2gp-mutagen/WD-f0vk.json; docs/findings/86-wan2gp-mutagen-metadata-warnings.md.

### AC Verification
| AC | Requirement | Code/Evidence Location | Status |
|---|---|---|---|
| 1 | Exact source site, runtime identity, dependency classification | diagnosis artifact sections source_diagnosis/runtime_identity/dependency_classification (JSON lines 5-46); Finding 86 | PASS |
| 2 | Durable Wangp-owned correction, no undocumented install | verify_native_logs at scripts/verify_maestro_parity.py:91-203 and warning code line 193; contract line 33 | PASS |
| 3 | Real WD-9t9o/WD-isg9 regression bytes/hashes and explicit warning ownership | tests/test_maestro_parity_evidence.py:201-228; JSON accepted_log_bytes | PASS |
| 4 | Preserve accepted artifacts/logs/results | unchanged diff + six recomputed hashes above | PASS |
| 5 | No SSH/GPU/download/unrelated host mutation | command boundary and diagnosis probe_boundary | PASS |
| 6 | Targeted tests, backlog lint, diff check | measured outputs above; release additionally ready | PASS |

LEARNINGS:
- The canonical Maestro-parity verifier is the best local seam because queue_attempt already names native logs and the checker is contractually read-only.
- Python splitlines changes line numbering for logs containing carriage-return progress updates; split on newline preserves accepted-log line numbers.
- Mutagen exists in the host user Python 3.12 inventory but not the active Wan2GP Python 3.11 venv; package presence elsewhere is not an install authorization.
- Successful media bytes and optional embedded metadata must remain separate success boundaries so neither masks the other.

## nd_contract
status: delivered

### evidence
- Commit and pushed branch 59ae97903978c5f04a4dbffd7e372e0fe7d5a74a.
- Targeted 95/95 PASS; real-byte scanner 4 owned warnings per story and 0 diagnostics; backlog lint PASS; diff checks PASS; release ready.
- Accepted WD-9t9o/WD-isg9 bundles unchanged and all six log hashes match.

### proof
- [x] AC #1: exact accepted-evidence source component site, runtime identity, and required-vs-optional dependency classification recorded.
- [x] AC #2: Wangp-owned read-only warning ownership implemented without ad hoc install or host mutation.
- [x] AC #3: real WD-9t9o/WD-isg9 bytes and hashes drive regression coverage and explicit warning classification.
- [x] AC #4: accepted evidence, output hashes, ffprobe/gate records, and logs remain unchanged.
- [x] AC #5: no prohibited live-host operation was run.
- [x] AC #6: targeted tests, backlog lint, and diff checks pass; release verify also reports ready.

## History
- 2026-09-26T17:13:27Z dep_added: blocks WD-fay0
- 2026-09-26T17:14:42Z status: open -> in_progress
- 2026-09-26T17:14:42Z auto-follows: linked to predecessor WD-9t9o
- 2026-09-26T17:14:42Z claimed by dev-WD-f0vk
- 2026-09-26T17:31:26Z status: in_progress -> in_progress
- 2026-09-26T17:31:26Z auto-follows: linked to predecessor WD-isg9

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-9t9o]], [[WD-isg9]]

## Comments
