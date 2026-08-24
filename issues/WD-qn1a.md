---
id: WD-qn1a
title: "readback: 4-shot render came out 420f not 428f — tolerance(4)=8 passed but 4-shot data point is -8f not -6f"
status: closed
priority: 2
type: task
labels: [bug, measurement]
created_at: 2026-08-23T17:53:08Z
created_by: speed
updated_at: 2026-08-24T13:51:17Z
content_hash: "sha256:bcb29794855edcb5874a723ea3a9dfbfef75461d922bedb0fc3675080de092a2"
assignee: jmanhype-glm
closed_at: 2026-08-24T13:51:17Z
close_reason: "PR #19 merged (bd6f079): tolerance semantics verified correct, pull-mirror hygiene fixed, 237 tests green. Evidence in comments."
---

## Description
Cycle 4 MV: expected 4x107=428f, actual 420f, diff 8. tolerance(4)=2+2*3=8 — the check PASSED (diff 8 >= 8 is false... wait 8>=8 is TRUE, meaning it should have RAISED). Verify the comparison operator: diff 8 vs tolerance 8 — if check is >= then it raised and process died silently; if > then it passed. Actual seam loss at n=4 is -8f (2.67/seam), confirming per-seam loss is NOT exactly 2 — second measurement point for MEASURED_SEAM_FRAMES (2 data points: n=3 -> -4, n=4 -> -8). Local process exited without completing its output tail (found dead); video pulled manually. ALSO: pull6 mirror contained unrelated historical render files (fetch_videos mtime filter worked, but scratch hygiene: output-dir mtime scan pulled stale files from outputs/) — investigate whether fetch_videos is scanning the SHARED outputs dir without story isolation.

## Acceptance Criteria


## Design


## Notes


## History
- 2026-08-24T13:46:23Z status: open -> in_progress
- 2026-08-24T13:46:23Z claimed by jmanhype-glm
- 2026-08-24T13:51:17Z status: in_progress -> closed

## Links


## Comments

### 2026-08-24T13:51:17Z speed
Closed by jmanhype-glm session. (1) Operator semantics verified by code inspection + live data: check is abs(got-want) >= tol with tol(4)=2+3*3=11 — cycle-4 good render (diff 8) passes, real loss (diff 15) raises; #15 recalibration (MEASURED_SEAM_CEILING=3) correct for both data points (n=3→4, n=4→8). Second measurement point recorded in source comment (wangp_adapter.py:172-184). (2) Scratch hygiene FIXED: SshHost.fetch_videos purged stale renders from pull mirror (rsync -a pulled whole shared outputs dir — pull6 finding). PR #19, TDD RED→GREEN, full suite 237 passed, merged to main bd6f079.
