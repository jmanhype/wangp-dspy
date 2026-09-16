# 64 — render retry fingerprints were not canonical or attempt-scoped

Status: OPEN; source repair staged for review.

## Evidence

Qodo review of PR #85 found five gaps in the deterministic replay guard:

1. Legacy failed/dead-letter clips had no stored fingerprint.
2. FL2VA `image_end` input changes did not change the fingerprint.
3. Ref2VA ignored top-level `steps`, but changing that ineffective field did
   change the fingerprint.
4. Seed-bump retries mutated clips without recomputing the stored fingerprint.
5. A failed multi-clip job treated unattempted later clips as failed inputs.

## Minimal fix

Make the fingerprint lane-aware and content-aware:

- include start and end image references, including mapping forms and file
  bytes;
- include effective common inputs;
- omit Ref2VA’s ignored top-level `steps`;
- recompute fingerprints on every clip-blob persistence;
- compute a legacy fingerprint on demand when one was never stored;
- mark the clip that reached renderer admission;
- deny only attempted clips, while preserving legacy single-clip behavior.

The queue now persists `render_attempted` before invoking the renderer, so a
render exception remains replay-guarded while later untouched clips in a
multi-clip job remain submittable.

## Regression coverage

Tests now cover:

```text
legacy failed clip without stored fingerprint → identical retry rejected
changed image_end bytes                        → fingerprint changes
mapping and string image_end                   → same fingerprint
ignored Ref2VA steps edit                      → fingerprint unchanged
seed mutation through update_clips             → fingerprint recomputed
unattempted sibling in failed multi-clip job   → accepted
```
