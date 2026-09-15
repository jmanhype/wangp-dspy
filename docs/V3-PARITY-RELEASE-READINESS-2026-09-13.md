# v3 parity repair — source-only release review

## Decision

**Exact reference pair verified; source-only checks green; not released.**

Actual repository: `/Users/Shared/HermesWorkspace/wangp-dspy`.
Branch: `codex/golden-v3-lf003-repro`.
HEAD: `23dd219ff76b406f8d41d81ea4f66583f936d966`.
The repair and this review are local/uncommitted. No commit, push, remote PR,
GPU rerender or operator-verdict change was performed in this follow-up.

## Evidence independently checked

1. Ran `predict.v3_canary` against the existing newly generated cut 1, cut 2,
   assembled pair and chain seed. All four original hashes passed, with frame,
   FPS and audio/video start-time checks. Pair SHA256:
   `0146285a9ea6441b4688e1651a467c9af189e9b63e1403ffbf92938825294a51`.
2. A delegated source-only candidate used a local clone of the recorded HEAD,
   overlaid current tracked edits plus the eleven repair files listed below.
   No untracked media, queue databases or old experimental runner scripts were
   copied. The first full suite found one real portability defect: #51's test
   hard-coded the Hermes checkout path.
3. Reviewed the test-only fix, retained the actual-root/HEAD and outside-Git
   assertions, and independently ran both complete suites: **1,315 passed,
   1 skipped** in each checkout (1,316 collected, no failures or errors).
4. Reviewed comments/docstrings correcting obsolete native-audio instructions.
   The runtime retains native H3 audio; the shared external remux planner is a
   separate lane. Documentation changes do not claim that Whisper or three
   still images measure phonetic A/V synchrony.

Evidence bundle: `datasets/runs/provenance/v3-parity-release-check-20260913/`.
Its manifest records copied evidence hashes, initial failure, final JUnit
results, the golden recheck and explicit scope limitations. The original
render directories and append-only run history are unchanged.
Evidence manifest SHA256:
`7ff8043c62032e4274688bcc3fd634ebb1cbf7e02c23db7eb279ffc237be0769`.

## Candidate contents and pre-existing work

The source-only run tested the integrated current tree, not a hypothetical
patch excluding all prior local work. The pre-repair snapshot under
`/tmp/wangp-before-parity-fix/` contains ten already-modified tracked files.
These three still match that snapshot exactly:

- `qc/audio_critic/whisper_cli.py`
- `services/director/run.py`
- `tests/test_audio_prep.py`

Seven additional files contain overlapping pre-existing and repair edits:
`host/wangp_adapter.py`, `predict/audio_prep.py`,
`predict/continuation_lane.py`, `predict/render_profiles.py`,
`qc/audio_critic/modelscope_vision_judge.py`, `scripts/run_jobs.py`, and
`services/chain/controller.py`. Those include functional dependencies such as
two-cut planning/profile propagation; they must not be dropped or silently
claimed as newly authored work. Whole-tree staging is inappropriate.

The eleven explicitly included new repair files are:

```text
host/ref2va_evidence.py
host/ref2va_recovery.py
predict/ref2va_settings.py
predict/v3_recipe.py
predict/v3_canary.py
scripts/run_v3_native_control.py
tests/test_completed_ref2va_recovery.py
tests/test_host_native_assembly.py
tests/test_ssh_probe_argv.py
tests/test_v3_canary.py
tests/test_v3_native_parity.py
```

The recovered generator source used by prompt tests is already tracked.
Untracked `scripts/run_v2_control.py`, `scripts/run_v3_pair.py`,
`scripts/run_v3_single.py`, generated media and unrelated local files were
excluded from the source-only candidate and remain untouched.

## Separate finding/PR boundaries

- **#50:** native conditioning/audio repair, exact recovered recipe, evidence
  and golden regression gate. Locally proven; review/reconciliation with its
  pre-existing dependencies still precedes any authorized commit or PR.
- **#51:** portable repository-identity tests and its finding document.
  Test-only change; production identity code is unchanged. Keep separate from
  the rendering PR.
- **#48:** historical rejected chain artifacts remain evidence. Exact two-cut
  reproduction does not establish six-cut quality or a maximum chain depth.
  The old conditioning-dropping path cannot prove a native H3 latent ceiling.
- Other finding documents (#41/#45/#48 and validation notes in #42/#47) retain
  unresolved or historical verification language. This source review does not
  claim their live infrastructure/creative acceptance is newly checked.

## Limits and next authorized step

The isolated test reused the existing Python environment and local FFmpeg;
it is not a fresh dependency install or immutable GPU-environment proof.
The real golden run still needs its original host fixtures and renderer
environment; passing source tests does not provision them. No new-premise or
six-cut acceptance is inferred from identical two-cut bytes.

Before publication, obtain the operator's explicit commit/push authorization,
reconcile the overlapping pre-existing hunks, and preserve one finding per PR.
After the release snapshot is approved, a separately recorded new-premise
two-cut trial is the next creative-generalization check—not another redundant
render of the already-proven original pair.

## Orchestration evidence

The requested Astra policy and saved setup were read. Routine work was sent
to fresh-context agents with explicit `zai-coding/glm-5.3`, low-effort requests;
their file edits, test output and reports were checked by the orchestrator.
The setup file alone is not model-execution proof, and no independent parent
model attestation is claimed here. DeepSeek and ModelScope inference were not
used. No X-profile operation was performed.

Three delegated tasks produced checked test/documentation artifacts. The
inventory follow-up and evidence-packaging tasks then exhausted provider
retries with HTTP 429. The orchestrator finished the local packaging after
that failure, rejected and corrected an invalid line-count table in the draft
inventory, and independently confirmed final docstring-stripped AST equality.
Those failures are recorded rather than represented as successful delegation.
