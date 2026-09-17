# 79 — Split Whisper pass bars accepted incompatible supplier audio

Status: implemented on this branch.

## Failure boundary

The LF003 VibeVoice supplier accepted Rho’s prepared turn at Whisper score
`0.500` because its local, remote, and CLI defaults were `0.5`. The production
render seam then rejected the same audio before rendering because its mandatory
pre-gate bar was `0.6`:

```text
pre: transcript score 0.500 below pass bar 0.600
```

This allowed staging/publication work for audio that could never enter the
render path, and made the effective audio contract depend on which default a
caller happened to omit.

## Change

`DEFAULT_WHISPER_PASS_BAR = 0.6` is now defined beside the gate implementation
and consumed by:

* `run_whisper_gate()`;
* the Ref2VA QC stage’s pre/post gates;
* the VibeVoice local supplier;
* the VibeVoice remote supplier;
* the VibeVoice CLI default and help text;
* `scripts/run_jobs.py` pre-render admission.

Explicit `--pass-bar`/`pass_bar` overrides remain supported. The production
policy remains strict at `0.6`; no score is reinterpreted or waived.

## Verification

Model-free tests now assert that the shared default is `0.6` and that VibeVoice
rejection evidence records the production bar. The relevant Whisper, VibeVoice,
Ref2VA runtime, and job-executor tests are run in the PR.
