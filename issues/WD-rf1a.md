---
id: WD-rf1a
title: "Delivered media resolution contradicts the plan envelope for every recorded render"
status: closed
priority: 0
type: task
parent: WD-as25
created_at: 2026-09-21T07:00:04Z
created_by: speed
updated_at: 2026-09-23T17:36:19Z
content_hash: "sha256:340607dd3b9a9d30f4b605cf159d6386e5ba3ed91c55f52c8ae1f8c272ac2fbc"
assignee: dev-WD-rf1a
follows: [WD-l48s]
labels: [delivered, accepted]
closed_at: 2026-09-23T17:36:19Z
close_reason: "Accepted: exact-head replay, adverse cases, RED/GREEN, 1990-test suite, build, CI, and delivery proof all verified"
---

## Description
## USER INTENT
A user can run deterministic preflight replay and see real delivered media dimensions reconciled with the plan envelope rather than every complete row rejected for `delivered_resolution_contradicts_envelope`.

## Symptom
Every recorded render's delivered resolution contradicts the resolution recorded in that run's own plan/envelope, so the production preflight invariant "delivered media envelope == planned envelope" is false for 100% of recorded complete rows.

## Measured evidence
From the preflight spend-gate corpus built in WD-l48s (`datasets/spend-gate/v1/`, `--evidence-mode all-local`):

- `deterministic_preflight` rejects **18 of 18** complete rows, and every rejection carries the single reason `delivered_resolution_contradicts_envelope`.
- The same holds in the tracked subset (13 of 13).
- Concrete instance: the operator-accepted LF004 recovery film delivers **704x576** while the planning envelope for those clips records **480x832**. That film passed every declared QC/AV gate and was operator-accepted, so the delivered numbers are the ones that actually shipped; the envelope field is the wrong one.
- Gate outcomes are unaffected: vision 25/0, whisper post 27/9, av_sync 13/5 all recorded against the delivered media.

## Impact
- The spend-gate deterministic baseline cannot admit any real render until this field is correct, which blocks any calibrated admission work (WD-as25).
- Any other consumer of the planned resolution — aspect-ratio or framing checks, plate sizing, LoRA/model targeting, contact-sheet layout — is reading a number that contradicts reality.
- The contradiction is currently silent: nothing in the pipeline compares the envelope resolution against the delivered media.

## Scope
Determine why the envelope resolution disagrees with delivered media (planner field vs render profile vs post-process/rescale step), then correct the recording or the checks so the invariant is either true or explicitly typed as a known transform. Do not change any QC/AV/retry gate.

## Out of scope
- Any render. This is a recording/verification defect; existing accepted artifacts must not be mutated.
- The union/envelope redesign of other missing queue-envelope fields (separate triage).

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Discovered during WD-l48s replay; reasons attributed per row in `datasets/spend-gate/v1/replay-report.md`.

### proof
- [ ] Pending: identify the divergence point and fix it, or record why the delivered resolution intentionally differs.

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence
Summary: The 480x832 value is a renderer request, not delivered geometry. The spend-gate recorder now binds that request, PNG reference geometry, the recorded WanGP handler SHA-256, and expected 704x576 output in a typed resolution_transform; replay admits a matching transform, abstains without one, and rejects a genuine mismatch.

Commands run:
- uv run --frozen --extra dev python /tmp/rf1a_reproduce_local.py  # before: 18 complete, 18 rejected, reason delivered_resolution_contradicts_envelope=18
- uv run --frozen --extra dev python scripts/build_spend_gate_corpus.py --repository-root . --evidence-mode all-local --output-dir datasets/spend-gate/v1 --replay --verify-artifact
- uv run --frozen --extra dev pytest tests/test_spend_gate.py::test_resolution_request_is_typed_against_reference_geometry -q --junitxml=/tmp/rf1a_t.xml
- uv run --frozen --extra dev pytest tests/test_spend_gate.py -q --junitxml=/tmp/rf1a_s.xml
- uv run --frozen --extra dev pytest -q --junitxml=/tmp/rf1a_full2.xml
- uv build --out-dir /tmp/rf1a_uv_build_final
- uv run --frozen --extra dev python /tmp/rf1a_final_replay.py  # after: 18 admitted, 0 rejected, 0 abstained, reasons={}
- gh api repos/jmanhype/wangp-dspy/commits/d4fb478ec0e706c12ad008058a5caea48bd9d8bf/check-runs

SHA: d4fb478ec0e706c12ad008058a5caea48bd9d8bf

### CI/Test Results
- RED regression: tests=1 failures=1 errors=0 skipped=0 exit=1 (KeyError resolution_transform before the fix).
- Targeted regression: tests=1 failures=0 errors=0 skipped=0 exit=0.
- Spend-gate suite: tests=18 failures=0 errors=0 skipped=0 exit=0.
- Full pytest: tests=1990 failures=0 errors=0 skipped=1 exit=0.
- Build: exit=0; wheel wangp_dspy-0.1.0-py3-none-any.whl SHA-256 d73c2b38cf7e8eebe41c3e960b02b3504e0f938ead038d968a30aff6018dfa3d; sdist wangp_dspy-0.1.0.tar.gz SHA-256 ba71d036fc21d421ac3b36fd3b6d2ec12a32ec4805627f181f377b44072cbf19.
- GitHub check test on exact head d4fb478ec0e706c12ad008058a5caea48bd9d8bf: COMPLETED / SUCCESS, run 35891704635.
- PR: https://github.com/jmanhype/wangp-dspy/pull/178

### AC Verification
| AC | Result | Evidence |
|---|---|---|
| Reproduce the corpus rejection before the fix | PASS | Before replay: 18/18 complete rows rejected with delivered_resolution_contradicts_envelope. |
| Trace both values to writers/readers | PASS | Request writer predict/render_profiles.py:304-308; spend recorder training/spend_gate.py:258-286,301; delivered ffprobe writer training/spend_gate.py:288-301; replay reader training/spend_gate_replay.py:123-136. |
| Classify the divergence | PASS | Incomparable fields plus an unrecorded renderer transform: predict/v3_recipe.py:3-5 and docs/h3-continuation-recipe.md:31-41 distinguish request 480x832 from output 704x576. |
| Record an explicit typed transform without weakening the gate | PASS | training/spend_gate.py:14-19,258-286 records handler/reference/output; replay abstains unknown and rejects mismatch at training/spend_gate_replay.py:126-136. |
| Add a real-process regression test and prove RED | PASS | tests/test_spend_gate.py:260-290; RED JUnit tests=1 failures=1, GREEN tests=1 failures=0. |
| Re-run replay and full validation | PASS | Final replay 18 admitted / 0 rejected / 0 abstained / reasons={}; full pytest and build evidence above. |

## nd_contract
status: delivered

### evidence
- PR #178 at head d4fb478ec0e706c12ad008058a5caea48bd9d8bf.
- Full pytest JUnit /tmp/rf1a_full2.xml: 1990 tests, 0 failures, 0 errors, 1 skipped.
- CI test check: success on exact head.
- Final corpus replay /tmp/rf1a_after_counts.json: 18 admitted, 0 rejected, 0 abstained.

### proof
- [x] AC #1: The pre-fix 18/18 resolution rejection was reproduced and recorded.
- [x] AC #2: Request and delivered values were traced to their exact writers/readers with file-line evidence.
- [x] AC #3: The divergence was classified as incomparable request versus media geometry plus a previously unrecorded renderer transform.
- [x] AC #4: The transform is explicitly typed and fail-closed; genuine contradictions still reject.
- [x] AC #5: The real-process regression was demonstrated RED and then GREEN.
- [x] AC #6: Corpus replay, full tests, build, and exact-head CI all passed.


## History
- 2026-09-23T15:59:30Z status: open -> in_progress
- 2026-09-23T15:59:30Z claimed by dev-WD-rf1a

- 2026-09-23T16:02:18Z dep_added: blocks WD-l48s
- 2026-09-23T17:16:58Z status: in_progress -> in_progress
- 2026-09-23T17:16:59Z auto-follows: linked to predecessor WD-l48s
- 2026-09-23T17:36:19Z status: in_progress -> closed
- 2026-09-23T17:36:19Z dep_removed: no_longer_blocks WD-l48s

## Links
- Parent: [[WD-as25]]
- Follows: [[WD-l48s]]

## Comments
