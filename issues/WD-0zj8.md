---
id: WD-0zj8
title: "Clean-machine generated install"
status: in_progress
priority: 1
type: feature
labels: [install, evidence, external-integration]
parent: WD-3nod
created_at: 2026-09-24T14:14:09Z
created_by: speed
updated_at: 2026-09-25T03:24:13Z
content_hash: "sha256:bbb4f55488b4c688e38169c6f13c0ca1878d50e356ea5fb16b451b0d3b472b63"
blocks: [WD-fay0]
was_blocked_by: [WD-651z, WD-m0r5]
assignee: dev-WD-0zj8
follows: [WD-651z, WD-m0r5]
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

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Was blocked by: [[WD-651z]], [[WD-m0r5]]
- Follows: [[WD-651z]], [[WD-m0r5]]

## Comments
