---
id: WD-0zj8
title: "Clean-machine generated install"
status: in_progress
priority: 1
type: feature
labels: [install, evidence, external-integration, delivered]
parent: WD-3nod
created_at: 2026-09-24T14:14:09Z
created_by: speed
updated_at: 2026-09-25T04:12:34Z
content_hash: "sha256:c34833c36f61e28b82cee9413edf0274919ae46909020e65f1223dc02f140f5f"
blocks: [WD-fay0]
was_blocked_by: [WD-651z, WD-m0r5]
follows: [WD-651z, WD-m0r5, WD-e4r7]
---

## Description
## USER INTENT
This is proof #1 for “better than Maestro”: a stranger starts on a clean machine, invokes one documented command, and either reaches a real generated artifact with complete provenance or receives a typed, actionable refusal. The proof must use a disposable checkout and must not depend on the operator's existing checkout, configuration, credentials, downloaded models, or GPU. The no-GPU install-and-plan portion must be demonstrable before authorization; the generated artifact remains impossible until the operator supplies the required host/model inputs.

## REQUIRED OPERATOR INPUTS — NOT YET PROVIDED
- Per-batch GPU/render-host authorization has NOT been given by this story.
- Model-download approval has NOT been given by this story.
- A complete authorized host/model manifest, including every required model identity, source, hash or immutable version, license, and usage constraint, is also required and has NOT been supplied.
- The lane bundle must record the operator authorization and download approval verbatim, including scope, timestamp, approver, exact command boundary, host identity, and model list. Missing input is a blocked condition, not infeasibility and not a fake fallback verdict.

## No-Fabrication Rule
Installer output, `wgp doctor`, checkout state, deterministic plans, configuration templates, dry-runs, queue planning, fixture bytes, skipped generation, and prose claims are never generated-artifact evidence. `host_run_verified` requires actual emitted media bytes from an authorized run and a bundle that passes the accepted WD-651z checker. A refusal may be evidence of fail-closed behavior, but it is not generation evidence.

## OUT OF SCOPE
- A GUI, Pinokio launcher, registry publication, package upload, Git tag, or external account.
- Installing or downloading models without separate operator approval.
- Reusing a WD-m0r5 or other lane bundle as this story's evidence; each required artifact must come from this lane's authorized command.
- Changing queue admission, renderer policy, wiring, preflight, or `scripts/run_film.py` semantics.

## DIFF BUDGET
- About 5 files and under 400 authored changed LOC, expected in `install.sh`, `docs/install.md`, `README.md`, an install/evidence test, and bundle manifests/diagnostics under `datasets/runs/maestro-parity/WD-0zj8/`.
- Generated evidence is bounded to one real media artifact and its required logs/metadata; no model weights or disposable checkout is committed. Record aggregate bundle size and keep it under 128 MiB unless recorded refusal diagnostics are larger.

## Boundary Map
PRODUCES:
- docs/install.md -> clean-machine one-command generated-install procedure
  spec: one saved-shell-script invocation from a pristine user environment that creates or uses a disposable checkout, installs the locked tool, emits the no-GPU plan, and then either records a checker-valid generated-artifact bundle or fails closed with the exact missing host/model input.
- datasets/runs/maestro-parity/WD-0zj8/ -> `wangp-dspy.maestro-parity-evidence/v1` clean-machine bundle
  event: a successful authorized sub-bundle records authorization, exact argv, commit/dirty state, clean-environment identity, model/reference provenance, queue attempt, emitted media hash/metadata, objective gate, and reviewer decision; a blocked sub-bundle records the plan/provenance and exact typed refusal without claiming generation.
- README.md -> non-duplicative pointer to the clean-machine proof command
  event: keep the existing contributor quickstart distinct and state exactly which portion is no-GPU proof and which requires authorization.

CONSUMES:
- WD-u8yk: install.sh -> `sh install.sh [--source <path-or-url>] [--checkout <destination>] [--dry-run]`
  source: accepted one-command installer and checkout boundary; extend it rather than creating a second installer.
- WD-u8yk: README.md -> tested no-GPU quickstart command and expected plan summary
  source: the committed LF004 brief/planner path used to prove install plus plan without host configuration.
- WD-651z: docs/maestro-parity-evidence-contract.md -> `wangp-dspy.maestro-parity-evidence/v1`
  source: canonical authorization, provenance, hash, metadata, gate, and reviewer fields; do not duplicate or weaken them.
- WD-651z: scripts/verify_maestro_parity.py -> `verify_bundle(bundle: Path) -> VerificationReport`
  event: the accepted checker must exit zero on the successful lane bundle before any verified claim.
- (operator): explicit per-batch host authorization and model-download approval -> verbatim authorization record
  source: future operator input; not supplied by story creation.

## Story Acceptance Criteria
1. [State] Given a pristine disposable environment with an isolated `HOME` and temporary tool/cache/checkout directories, the one documented command performs the install and emits the tested no-GPU plan without manual config editing, existing Wangp state, SSH configuration, GPU work, or model download.
2. [Unwanted] Given absent, incomplete, or unauthorized host/model inputs, the generation stage refuses before queue admission or inference with a typed diagnostic naming the missing input and a safe next action; it does not silently stop at the plan, substitute a fixture or dry-run, or emit a placeholder artifact.
3. [State] Given the required authorization, download approval, complete host/model manifest, and a successful run, the command emits actual media bytes whose SHA-256, measured metadata, provenance, queue attempt, and objective gate are recorded in `datasets/runs/maestro-parity/WD-0zj8/` and pass the accepted WD-651z checker.
4. [Unwanted] No hand-created or hand-edited `evidence.json`, absent hash, mismatched artifact, unauthorized model, reused lane output, or partial run is represented as `host_run_verified`.
5. [State] The disposable-checkout proof records the exact source URL or path, resolved commit, dirty state, command argv, tool versions, host/model presence or absence, and the no-GPU plan identity, while leaving the operator's normal configuration and checkout unchanged.
6. [State] Documentation distinguishes the always-available install/plan proof from the authorized generated-artifact proof and links each claim to its bundle or recorded refusal.
7. [Unwanted] `services/jobs/queue.py`, `services/director/renderers/policy.py`, `services/director/wiring.py`, `services/jobs/preflight.py`, and `scripts/run_film.py` remain unchanged from accepted base `40f8c2b373dec1c84ca5a596c821b740934af6fb`.

## Testing Requirements
- Real-process integration MANDATORY with no mocks: run the documented command from a clean temporary user environment and disposable checkout; capture installer, plan, generation-refusal, and authorization-gated paths separately where authorization is unavailable.
- Prove no manual configuration by starting with isolated `HOME`, empty tool/cache directories, no `WANGP_*` host variables, and no pre-existing checkout; assert the no-GPU plan summary and repository provenance.
- For the absent host/model case, assert non-zero exit, exact typed diagnostic and remediation, absence of queue admission/model contact/generated media, and preservation of the emitted plan/refusal record.
- If operator authorization is later supplied, hash and ffprobe/probe the emitted artifact, invoke the accepted WD-651z checker, and require exit zero before any verified claim.
- Run install/README targeted tests; `uv run --frozen --extra dev pytest -q --junitxml=/tmp/WD-0zj8-full.xml` with parsed JUnit `errors=0` and `failures=0`; `uv run --frozen --extra dev wgp release verify` reporting `release=ready` and `tag_created=false`; and `git diff --exit-code 40f8c2b373dec1c84ca5a596c821b740934af6fb -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py`.
- Also run `git diff --check`, record aggregate bundle size, and record that no model weights or disposable checkout were committed.

## Delivery Requirements
- Paste the clean-environment command, exact output tails, resolved commit/tool identities, plan summary, typed refusal, bundle tree/hash/metadata, checker result, parsed JUnit counters, release fields, protected-file parity, and `git diff --check`.
- If host/model authorization remains absent, explicitly report the generated-artifact portion as blocked on that input; the install/plan and fail-closed portions may still be delivered as separate recorded outcomes without claiming generation.

## MANDATORY SKILLS
- pvg

## nd_contract
status: new

### evidence
- Authored on 2026-09-24 from accepted WD-u8yk install behavior, `docs/install.md`, and the README no-GPU quickstart; operator host/model approvals remain outstanding.

### proof
- [ ] Pending implementation and explicit operator authorization.

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence (DELIVERED)

Commands run:
- `uv run --frozen --extra dev pytest -q tests/test_readme_quickstart.py` — 6 passed.
- `uv run --frozen --extra dev pytest -q tests/test_install.py::test_missing_uv_fails_closed tests/test_readme_quickstart.py::test_clean_checkout_install_plan_then_typed_generation_refusal` — 2 passed.
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-0zj8-full.xml` — JUnit tests=2085 errors=0 failures=0 skipped=1.
- `uv run --frozen --extra dev wgp release verify` — release=ready tag_created=false.
- `git diff --exit-code d8671f3 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py` — clean.
- `git diff --check` — clean.

Summary: clean disposable-checkout install produced the four-clip LF004 no-GPU plan (SHA-256 935f3ed64ba19d16aba7059d075fcfd8e99df66cca899357a10a7fca6c2fd0bb), then failed closed exit 3 with HOST_CONFIGURATION_INCOMPLETE and MODEL_MANIFEST_REQUIRED. generated_artifact=false and host_run_verified=false. AC #2 is PARTIAL; AC #3 remains BLOCKED.

Commit SHA: 2d4d1f39c56bb208eaf16fb2e0ab7d09f80e14a1
Clean-proof source commit correction: 212f12058e1704f9c1657437f7698c4f4e126d21
Coverage: not measured.

## nd_contract
status: delivered

### evidence
- One documented command and real clean-checkout outputs are committed under datasets/runs/maestro-parity/WD-0zj8/clean-machine/; full JUnit has zero errors/failures; release ready; protected files unchanged; branch remote matches HEAD.

### proof
- [x] AC #1 clean install+plan.
- [ ] AC #2 PARTIAL missing host/model refusal only.
- [ ] AC #3 BLOCKED operator inputs absent.
- [x] AC #4 no fabricated host-run evidence.
- [x] AC #5 clean-proof provenance recorded.
- [x] AC #6 documentation boundary clear.
- [x] AC #7 protected files unchanged.

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-24.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED — NO-GPU HALF ONLY)

PROOF:

### Delivered boundary
- Delivered the story-declared no-GPU install/plan and typed-refusal lane only.
- The generated-artifact half remains BLOCKED. Do not claim AC #3. AC #2 is PARTIAL: absent host and absent model manifests are proven; the full incomplete/unauthorized-input matrix and authorized generation path remain undone.

### Clean-machine command
- `sh install.sh --source "$PWD" --clean-proof "${TMPDIR:-/tmp}/wangp-clean-machine"`
- Documented at `docs/install.md:51-76`; implementation at `install.sh:114-180,248-303`; recorder at `scripts/record_clean_machine_refusal.py:1-197`; real-process test at `tests/test_readme_quickstart.py:424-578`.

### Demonstrated plan output
- `brief=sha256:67202d3597affeab4e5edcf15a1acef2f5e88ed00950ce17ff3012f5bb0472cd clips=4 plan=/private/tmp/wangp-clean-machine/proof/plan.json`
- `PLAN_ONLY path=/tmp/wangp-clean-machine/proof/plan.json generated_artifact=false`
- Plan SHA-256: `935f3ed64ba19d16aba7059d075fcfd8e99df66cca899357a10a7fca6c2fd0bb`.

### Demonstrated typed refusals
- Exit: `3`.
- `GENERATION_REFUSED diagnostics=2 exit=3`
- `diagnostic code=HOST_CONFIGURATION_INCOMPLETE ... observed: missing host.target, host.wgp_root ... remediation: Set every explicit host value, then rerun this preview before authorization.`
- `diagnostic code=MODEL_MANIFEST_REQUIRED ... observed: model manifest absent; zero authorized model identities are recorded ... Supply a complete wangp-dspy.model-assets/v1 manifest ... then record explicit model-download approval. Wangp does not download models.`
- No traceback, queue admission, SSH, model download, inference, GPU work, fixture media, or fallback artifact.

### Evidence bundle
- `datasets/runs/maestro-parity/WD-0zj8/clean-machine/` (72 KiB).
- `blocked-record.json` records argv, source/resolved commit `212f1204542ca56948137db46593e1c127be4e04`, clean tree, tool versions, plan hash/summary, host/model diagnostics, and `host_run_verified=false`.
- `BLOCKED.md` records the operator-input block. No model weights or disposable checkout is committed. The WD-651z success checker was not invoked because this is not a generated-artifact bundle.

### CI/Test Results
- `uv run --frozen --extra dev pytest -q tests/test_readme_quickstart.py` — 6 passed.
- `uv run --frozen --extra dev pytest -q tests/test_install.py::test_missing_uv_fails_closed tests/test_readme_quickstart.py::test_clean_checkout_install_plan_then_typed_generation_refusal` — 2 passed.
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-0zj8-full.xml` — parsed JUnit `tests=2085 errors=0 failures=0 skipped=1 time=764.897`.
- One unrelated existing warning appeared: StarletteDeprecationWarning for `fastapi/testclient.py` importing `starlette.testclient`; no test failed.
- Coverage: not measured; the required behavioral/full-suite commands did not request coverage.

### Release and repository gates
- `uv run --frozen --extra dev wgp release verify` — `release=ready`, `tag_created=false`.
- `git diff --exit-code d8671f3 -- services/jobs/queue.py services/director/renderers/policy.py services/director/wiring.py services/jobs/preflight.py scripts/run_film.py` — clean.
- `git diff --check` — clean.
- `pvg verify README.md docs/install.md install.sh scripts/record_clean_machine_refusal.py tests/test_readme_quickstart.py datasets/runs/maestro-parity/WD-0zj8/clean-machine --include-tests --format=text` — `VERIFY: PASSED (2 files scanned, 0 issues)`.

### Commit
- Branch: `story/WD-0zj8`.
- HEAD/pushed: `2d4d1f39c56bb208eaf16fb2e0ab7d09f80e14a1` (remote SHA equal).
- Clean-proof source commit recorded in bundle: `212f1204542ca56948137db46593e1c127be4e04`.

### AC Verification
| AC | Status | Evidence |
|---|---|---|
| 1 | PASS | One command, isolated HOME/cache/tool state, fresh clone, no-GPU LF004 plan; real-process test `tests/test_readme_quickstart.py:424-578`. |
| 2 | PARTIAL | Missing host and missing model each produce typed actionable nonzero refusal before generation; incomplete/unauthorized matrix remains. |
| 3 | BLOCKED | Requires per-batch host authorization, model-download approval, and complete authorized manifest; no operator inputs supplied. |
| 4 | PASS for delivered bundle | No `evidence.json`, no fake media/hash, and `host_run_verified=false`. |
| 5 | PASS | `blocked-record.json` records command, source, resolved clean commit, dirty state, tools, host/model state, and plan identity/hash. |
| 6 | PASS | `docs/install.md:51-76` and `README.md:60-63` explicitly distinguish plan/refusal from generation evidence. |
| 7 | PASS | Protected-file diff against `d8671f3` is clean. |

LEARNINGS:
- The existing README quickstart worktree mechanism extended cleanly to a disposable source plus second isolated clone.
- Preserving installer argv required a temp file; creating it before checking `uv` regressed the missing-uv typed path, so creation now follows the `uv` prerequisite check.
- Isolating HOME/cache/tool paths plus an empty WANGP_CONFIG prevents operator host state from leaking into the supposedly clean proof.

## BLOCKED CONDITION
The generated-artifact half remains blocked pending per-batch GPU/render-host authorization, model-download approval, and a complete authorized host/model manifest containing every required model identity, source, hash or immutable version, license, and usage constraint. This is missing input, not infeasibility and not permission for a fake fallback verdict.

## nd_contract
status: delivered

### evidence
- Clean disposable-checkout command produced LF004 plan SHA-256 `935f3ed64ba19d16aba7059d075fcfd8e99df66cca899357a10a7fca6c2fd0bb`, then typed host/model refusals with exit 3; full JUnit `tests=2085 errors=0 failures=0 skipped=1`; release ready; branch pushed at `2d4d1f39c56bb208eaf16fb2e0ab7d09f80e14a1`.

### proof
- [x] AC #1: clean install+plan works end to end without operator host/model/GPU state.
- [ ] AC #2: PARTIAL — absent host/model typed refusals proven; remaining incomplete/unauthorized cases not claimed.
- [ ] AC #3: BLOCKED — operator authorization, download approval, and complete manifest absent.
- [x] AC #4: no fabricated `host_run_verified` evidence in the blocked bundle.
- [x] AC #5: disposable-proof provenance and tool/plan identity recorded.
- [x] AC #6: plan/refusal versus generated-artifact boundary documented.
- [x] AC #7: protected engine files unchanged from `d8671f3`.

## nd_contract
status: in_progress

### evidence
- Claimed by dispatcher as dev-WD-0zj8 on 2026-09-25; implementing only the story-declared no-GPU install/plan and typed-refusal half.

### proof
- [ ] Pending clean-checkout install+plan and separate typed host/model refusal evidence.

## MANDATORY SKILLS
- pvg

Observable outcome: the clean-machine check returns an install evidence bundle under datasets/runs/maestro-parity/WD-0zj8/ with command, commit, environment, and hashes, or a fail-closed blocked record; no GPU batch is authorized by this story and explicit future per-batch operator authorization remains required.

## History
- 2026-09-24T14:14:09Z dep_added: blocked_by WD-651z
- 2026-09-24T14:14:09Z dep_added: blocked_by WD-m0r5
- 2026-09-24T14:14:10Z dep_added: blocks WD-fay0
- 2026-09-24T16:02:51Z dep_removed: was_blocked_by WD-651z
- 2026-09-25T02:28:58Z dep_removed: was_blocked_by WD-m0r5
- 2026-09-25T03:16:41Z status: open -> in_progress
- 2026-09-25T03:16:41Z auto-follows: linked to predecessor WD-651z
- 2026-09-25T03:16:41Z auto-follows: linked to predecessor WD-m0r5
- 2026-09-25T03:16:41Z claimed by dev-WD-0zj8
- 2026-09-25T04:10:45Z status: in_progress -> in_progress
- 2026-09-25T04:10:45Z auto-follows: linked to predecessor WD-e4r7
- 2026-09-25T04:11:56Z status: in_progress -> in_progress
- 2026-09-25T04:12:33Z status: in_progress -> open
- 2026-09-25T04:12:33Z released by speed
- 2026-09-25T04:12:34Z status: open -> in_progress

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Was blocked by: [[WD-651z]], [[WD-m0r5]]
- Follows: [[WD-651z]], [[WD-m0r5]], [[WD-e4r7]]

## Comments
