# 78 — Native post-Whisper drift needs evidence and bounded retries

Status: implemented in local changeset; targeted validation passing.

## Failure boundary

The fresh LF002 VibeVoice dialogue bundle was executed at commit
`5a312566e81985027399e39d7df9f21bc342a77d`. WanGP accepted the non-null
`image_start`, both image references, the 2.333333-second guide, and the
56-frame contract. It completed all 20 denoise steps and native A/V decode.

The first cut then failed the native post-Whisper gate:

```text
intended:  This is the last rain we have.
heard:     This is the last great land we have to.
score:     0.571
bar:       0.600
```

The preserved native artifact and full evidence bundle are under
`datasets/runs/provenance/lf002-vibevoice-whisper-rejection-20260917/`.
Both raw and remux hashes are
`fab8acb2ce4cf55b4dbcd0272983fefc4347a6fb98fe03bc78ac73a24299d62c`.

Three repo defects made that result worse than the underlying stochastic miss:

1. `run_ref2va_qc_stage` wrote evidence only after both Whisper gates and the
   vision gate succeeded. A post-Whisper rejection discarded the successful pre
   evidence and scored post evidence.
2. Production QC did not assign a default `qc_evidence_path`; even successful
   QC returned an in-memory dictionary instead of the durable evidence path the
   executor ledger expects.
3. The executor had bounded seed retries for visual misses but treated every
   Whisper failure as terminal. It also inferred “golden replay” from every
   `golden_v3` recipe, preventing fresh production runs using that recipe from
   retrying stochastic native speech drift.

## Change

- Persist partial Whisper evidence on pre or post rejection:
  `{pre, post}` with actual transcripts, scores, pass bars, and `passed`.
- Carry the same evidence on `Ref2VAQCStageError`.
- Production Ref2VA QC now defaults to `<artifact-dir>/qc-evidence.json`
  and returns that path to the executor ledger.
- A scored native post rejection appends immutable `whisper_rejections`
  and `whisper_retry_history` before any retry.
- Fresh non-replay clips receive up to two seed retries (`seed + 1`, `+2`)
  through `WANGP_WHISPER_RETRIES`.
- Retry only a scored post transcript with numeric evidence. Unscored
  transport/generation failures remain terminal.
- Golden replay behavior is explicit: acceptance bundles with `golden_canary`
  set `golden_replay=true`; fresh production bundles set it false. Legacy
  callers that use `golden_v3` without the new field retain deterministic
  no-reseed behavior.

## Verification scope

Model-free tests cover partial evidence persistence, scored post-rejection
retry with seed `905 -> 906`, append-only rejection/history, unscored failure
remaining terminal, legacy golden replay remaining deterministic, and the
acceptance runner marking fresh versus golden-replay bundles.

Local targeted command:

```text
.venv/bin/python -m py_compile qc/audio_critic/ref2va_stage.py scripts/run_jobs.py services/jobs/executor.py scripts/run_acceptance.py
.venv/bin/pytest -q tests/test_whisper_gate.py tests/test_jobs_executor.py tests/test_run_jobs_worker.py tests/test_run_acceptance.py tests/test_v3_native_parity.py
```

Both exited `0`; the targeted set passes 87 tests.
The full suite reports 1,455 selected tests, zero failures/collection errors,
and its normal one skip; its JUnit SHA-256 is
`806ab484fcb7561114a8a2a22c07fd61d488cdc3396011a752e76207990dada3`.
