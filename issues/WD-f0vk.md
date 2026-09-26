---
id: WD-f0vk
title: "Wan2GP emits nonfatal mutagen metadata errors after successful media saves"
status: open
priority: 0
type: bug
labels: [discovered-by-pm]
parent: WD-3nod
created_at: 2026-09-26T17:06:49Z
created_by: speed
updated_at: 2026-09-26T17:06:49Z
content_hash: "sha256:b55cedfeac3f5fb93ccfdab6a9cbc7f42092b50b5af06d4149e6b1fa9f944015"
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

No `blocks WD-fay0` dependency is added. The saved media, hashes, ffprobe records, objective gates, and checker evidence remain usable, so this warning-quality/host-dependency defect does not truly block the capstone's evidence verification. It must be tracked and owned separately.

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

## Acceptance Criteria


## Design


## Notes


## History


## Links
- Parent: [[WD-3nod]]

## Comments
