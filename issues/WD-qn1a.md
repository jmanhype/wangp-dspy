---
id: WD-qn1a
title: "readback: 4-shot render came out 420f not 428f — tolerance(4)=8 passed but 4-shot data point is -8f not -6f"
status: in_progress
priority: 2
type: task
labels: [bug, measurement]
created_at: 2026-08-23T17:53:08Z
created_by: speed
updated_at: 2026-08-24T13:46:23Z
content_hash: "sha256:91f1a7c5e8ba89caaf13bd9505d9ee9af9af4fb37b40ce5fae6877aee0f532dc"
assignee: jmanhype-glm
---

## Description
Cycle 4 MV: expected 4x107=428f, actual 420f, diff 8. tolerance(4)=2+2*3=8 — the check PASSED (diff 8 >= 8 is false... wait 8>=8 is TRUE, meaning it should have RAISED). Verify the comparison operator: diff 8 vs tolerance 8 — if check is >= then it raised and process died silently; if > then it passed. Actual seam loss at n=4 is -8f (2.67/seam), confirming per-seam loss is NOT exactly 2 — second measurement point for MEASURED_SEAM_FRAMES (2 data points: n=3 -> -4, n=4 -> -8). Local process exited without completing its output tail (found dead); video pulled manually. ALSO: pull6 mirror contained unrelated historical render files (fetch_videos mtime filter worked, but scratch hygiene: output-dir mtime scan pulled stale files from outputs/) — investigate whether fetch_videos is scanning the SHARED outputs dir without story isolation.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-24T13:46:23Z status: open -> in_progress
- 2026-08-24T13:46:23Z claimed by jmanhype-glm

## Links


## Comments
